import os
from datetime import datetime
from urllib.parse import urlparse

import psycopg2
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import (Flask, flash, get_flashed_messages, redirect,
                   render_template, request, session, url_for)
from psycopg2.extras import RealDictCursor
from requests import RequestException
from validators import url as valid_url

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')


def create_app():

    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    return app


app = create_app()


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/urls', methods=['POST'])
def post_index():
    url = request.form.get('url')

    parsed_url = urlparse(url)
    normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    if len(url) > 255:
        flash('Длина URL должна быть меньше 256 символов.', 'error')
        return render_template('index.html')

    # Валидация URL
    if not valid_url(url):
        flash('Некорректный URL', 'error')
        return render_template('index.html'), 422

    # Проверка существования URL в базе данных
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM urls WHERE name = %s", (normalized_url,))
            existing_url = cur.fetchone()
            if existing_url:
                flash('Страница уже существует', 'info')
                return redirect(url_for('url_detail', id=existing_url['id']))
            else:
                # Добавление нового URL в базу данных
                cur.execute(""" INSERT INTO urls (name, created_at) 
                            VALUES (%s, %s) 
                            RETURNING id """,
                            (normalized_url, datetime.now()))
                new_site_id = cur.fetchone()['id']
                conn.commit()
            
                flash('Страница успешно добавлена', 'success')
                return redirect(url_for('url_detail', id=new_site_id))


@app.route('/urls', methods=['GET'])
def urls():

    messages = get_flashed_messages(with_categories=True)
    show_error_message = any(category == 'error' for category, _ in messages)

    if show_error_message:
        return render_template('index.html')

    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(""" SELECT
                                u.id,
                                u.name,
                                MAX(uc.created_at) AS last_check,
                                uc.status_code
                            FROM urls u
                            LEFT JOIN url_checks uc ON u.id = uc.url_id
                            GROUP BY u.id, u.name, uc.status_code
                            ORDER BY u.id DESC; """)
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
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Получаем информацию о конкретном URL
            cur.execute("SELECT * FROM urls WHERE id = %s", (id,))
            url_data = cur.fetchone()

            if not url_data:
                flash('Запись не найдена.', 'error')
                return redirect(url_for('urls'))

            # Получаем список проверок для данного URL
            cur.execute(""" SELECT * FROM url_checks 
                        WHERE url_id = %s 
                        ORDER BY created_at DESC """, (id,))
            checks = cur.fetchall()

            for check in checks:
                check['created_at_formatted'] = \
                    check['created_at'].strftime('%Y-%m-%d')

            # Аналогичная обработка для url_data
            if url_data and url_data['created_at']:
                url_data['created_at_formatted'] = \
                    url_data['created_at'].strftime('%Y-%m-%d')

    return render_template('url_detail.html', url=url_data, checks=checks)


@app.route('/urls/<int:id>/checks', methods=['POST'])
def add_check(id):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:         
            # Проверяем существование URL
            cur.execute("SELECT * FROM urls WHERE id = %s", (id,))
            url_data = cur.fetchone()
        
            if not url_data:
                flash('Запись не найдена.', 'error')
                return redirect(url_for('urls'))
        
            try:
                response = requests.get(url_data['name'])
                response.raise_for_status()  
                status_code = response.status_code
                session['last_status_code'] = status_code
            except RequestException:
                flash("Произошла ошибка при проверке", 'error')
                return redirect(url_for('url_detail', id=id))
        
    soup = BeautifulSoup(response.text, 'html.parser')
    # Инициализируем переменные для хранения результатов анализа
    h1_tag_content = ''
    title_tag_content = ''
    meta_description_content = ''

    # Поиск тега <h1>
    h1_tag_content = (
    soup.h1.get_text(strip=True)[:255]
    if soup.h1
    else ''
)

    # Поиск тега <title>
    title_tag_content = (
    soup.title.get_text(strip=True)[:255]
    if soup.title
    else ''
)

    # Поиск тега <meta name="description">
    meta_description_content = (
    soup.find('meta', attrs={'name': 'description'})
    .get('content')[:255]
    if soup.find('meta', attrs={'name': 'description'})
    else ''
)

    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Записываем результаты анализа в базу данных
            cur.execute(
                """ INSERT INTO url_checks 
                (url_id, status_code, created_at, h1, title, description) 
                VALUES (%s, %s, %s, %s, %s, %s) """,
                (
                    id, 
                    status_code, 
                    datetime.now(), 
                    h1_tag_content, 
                    title_tag_content, 
                    meta_description_content
                )
            )
            conn.commit()

    flash('Страница успешно проверена', 'success')
    return redirect(url_for('url_detail', id=id))


if __name__ == '__main__':
    app.run(debug=True)
