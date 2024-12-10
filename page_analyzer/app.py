from flask import Flask, render_template, flash, request, redirect, url_for
from dotenv import load_dotenv
from urllib.parse import urlparse
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import uuid
from validators import url as valid_url
from datetime import datetime


load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    
    @app.route('/', methods=['GET', 'POST'])
    def index():
        if request.method == 'POST':
            url = request.form.get('url')
            created_at = request.form.get('created_at')

            parsed_url = urlparse(url)
            normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

            if not url:
                flash('Пожалуйста, введите URL для проверки.', 'error')
                return redirect(url_for('index'))
            
            if len(url) > 255:
                flash('Длина URL должна быть меньше 256 символов.', 'error')
                return redirect(url_for('index'))

            # Валидация URL
            if not valid_url(url):
                flash('Некорректный URL', 'error')
                return redirect(url_for('index'))

            # Проверка существования URL в базе данных
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM urls WHERE name = %s", (normalized_url,))
                existing_url = cur.fetchone()
            if existing_url:
                flash('Страница уже существует.', 'warning')
                return redirect(url_for('index'))

            # Добавление нового URL в базу данных
            with conn.cursor() as cur:
                cur.execute("INSERT INTO urls (name, created_at) VALUES (%s, %s)",
                            (normalized_url, datetime.now()))
                conn.commit()

            flash('URL успешно добавлен.', 'success')
            return redirect(url_for('urls'))

        return render_template('index.html')

    @app.route('/urls', methods=['GET'])
    def urls():
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(""" SELECT u.id, u.name, MAX(c.created_at) AS last_check FROM urls u LEFT JOIN url_checks c ON u.id = c.url_id GROUP BY u.id, u.name ORDER BY u.created_at DESC; """)
            urls = cur.fetchall()

            for url in urls:
                if url['last_check']:
                    url['last_check_formatted'] = url['last_check'].strftime('%Y-%m-%d')

        return render_template('urls.html', urls=urls)

    @app.route('/urls/<int:id>', methods=['GET'])
    def url_detail(id):
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Получаем информацию о конкретном URL
            cur.execute("SELECT * FROM urls WHERE id = %s", (id,))
            url_data = cur.fetchone()

        if 'created_at' not in url_data:
            print(f"Ключ 'created_at' отсутствует в словаре {url_data}")
        else:
            print(f"Ключ 'created_at' найден со значением: {url_data['created_at']}")

        if not url_data:
            flash('Запись не найдена.', 'error')
            return redirect(url_for('urls'))

        # Получаем список проверок для данного URL
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM url_checks WHERE url_id = %s ORDER BY created_at DESC", (id,))
            checks = cur.fetchall()

        for check in checks:
        # Преобразуем строку с датой в объект datetime
            check['created_at_formatted'] = check['created_at'].strftime('%Y-%m-%d')  # Предположим, что строка имеет такой формат

        # Аналогичная обработка для url_data
        if url_data and url_data['created_at']:
            url_data['created_at_formatted'] = url_data['created_at'].strftime('%Y-%m-%d')

        return render_template('url_detail.html', url=url_data, checks=checks)
    
    @app.route('/urls/<int:id>/checks', methods=['POST'])
    def add_check(id):
        # Проверяем существование URL
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM urls WHERE id = %s", (id,))
            url = cur.fetchone()
        if not url:
            flash('Запись не найдена.', 'error')
            return redirect(url_for('urls'))

        # Создаем новую запись в таблице url_checks
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO url_checks (url_id, created_at) VALUES (%s, %s)",
                (id, datetime.now())
            )
            conn.commit()

        flash('Проверка запущена', 'success')
        return redirect(url_for('url_detail', id=id))

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
    