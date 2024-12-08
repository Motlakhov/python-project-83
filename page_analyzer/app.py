from flask import Flask, render_template, flash, request, redirect, url_for
from dotenv import load_dotenv
from urllib.parse import urlparse
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import uuid
from validators import url as valid_url


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
            cur.execute("SELECT * FROM urls WHERE name = %s", (url,))
            existing_url = cur.fetchone()
            if existing_url:
                flash('Страница уже существует.', 'warning')
                return redirect(url_for('index'))

            # Добавление нового URL в базу данных
            cur.execute("INSERT INTO urls (name, created_at) VALUES (%s, %s)",
                        (url, created_at))
            conn.commit()

            flash('URL успешно добавлен.', 'success')
            return redirect(url_for('urls'))

        return render_template('index.html')

    @app.route('/urls', methods=['GET'])
    def urls():
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM urls ORDER BY created_at DESC")
        urls = cur.fetchall()
        return render_template('urls.html', urls=urls)

    @app.route('/urls/<int:id>', methods=['GET'])
    def url_detail(id):
        cur.execute("SELECT * FROM urls WHERE id = %s", (id,))
        url = cur.fetchone()
        if not url:
            flash('Запись не найдена.', 'error')
            return redirect(url_for('urls'))

        return render_template('url_detail.html', url=url)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
    