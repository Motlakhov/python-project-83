from flask import Flask, render_template, flash, request, redirect, url_for, get_flashed_messages, session
from dotenv import load_dotenv
from urllib.parse import urlparse
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import uuid
from validators import url as valid_url
from datetime import datetime
import requests
from requests import RequestException
from bs4 import BeautifulSoup


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
                return redirect(url_for('urls'))  # Переходим на /urls с сохраненной ошибкой

            # Проверка существования URL в базе данных
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM urls WHERE name = %s", (normalized_url,))
                existing_url = cur.fetchone()
            if existing_url:
                flash('Страница уже существует', 'info')
                return redirect(url_for('index'))

            # Добавление нового URL в базу данных
            with conn.cursor() as cur:
                cur.execute("INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id",
                            (normalized_url, datetime.now()))
                new_site_id = cur.fetchone()[0]
                conn.commit()
            
            flash('Страница успешно добавлена', 'success')
            return redirect(url_for('url_detail', id=new_site_id))

        return render_template('index.html')

    @app.route('/urls', methods=['GET'])
    def urls():
        messages = get_flashed_messages(with_categories=True)
        show_error_message = any(category == 'error' for category, _ in messages)

        if show_error_message:
            return render_template('index.html')

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(""" WITH latest_checks AS (
                                SELECT DISTINCT ON (uc.url_id)
                                    uc.url_id,
                                    uc.created_at,
                                    uc.status_code
                                FROM url_checks uc
                                ORDER BY uc.url_id, uc.created_at DESC
                            )
                            SELECT
                                u.id,
                                u.name,
                                lc.created_at AS last_check,
                                lc.status_code
                            FROM urls u
                            LEFT JOIN latest_checks lc ON u.id = lc.url_id
                            ORDER BY u.created_at DESC; """)
            urls = cur.fetchall()

            # Конвертируем полученный словарь в список
            urls_list = []
            for url in urls:
                if url['last_check']:
                    url['last_check_formatted'] = url['last_check'].strftime('%Y-%m-%d')
                urls_list.append(url)

        return render_template('urls.html', urls=urls_list)

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
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM urls WHERE id = %s", (id,))
            url_data = cur.fetchone()
        
        if not url_data:
            flash('Запись не найдена.', 'error')
            return redirect(url_for('urls'))
        
        try:
            response = requests.get(url_data['name'], timeout=5)
            response.raise_for_status()  # Если сайт недоступен, вызывается исключение
            status_code = response.status_code
            session['last_status_code'] = status_code
        except RequestException:
            flash(f"Произошла ошибка при проверке", 'error')
            return redirect(url_for('url_detail', id=id))
        
        soup = BeautifulSoup(response.text, 'html.parser')
        # Инициализируем переменные для хранения результатов анализа
        h1_tag_content = ''
        title_tag_content = ''
        meta_description_content = ''

        # Поиск тега <h1>
        h1_tag = soup.find('h1')
        if h1_tag is not None:
            h1_tag_content = h1_tag.text.strip()

        # Поиск тега <title>
        title_tag = soup.title
        if title_tag is not None:
            title_tag_content = title_tag.text.strip()

        # Поиск тега <meta name="description">
        meta_description_tag = soup.find('meta', attrs={'name': 'description'})
        if meta_description_tag is not None:
            meta_description_content = meta_description_tag.get('content').strip()

        # Записываем результаты анализа в базу данных
        with conn.cursor() as cur:
            cur.execute(
                """ INSERT INTO url_checks (url_id, status_code, created_at, h1, title, description) VALUES (%s, %s, %s, %s, %s, %s) """,
                (id, status_code, datetime.now(), h1_tag_content, title_tag_content, meta_description_content)
            )
            conn.commit()

        flash('Страница успешно проверена', 'success')
        return redirect(url_for('url_detail', id=id))

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
    