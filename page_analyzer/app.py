import os
import requests
from datetime import datetime
from page_analyzer.utils import normalize_url, validate_url
from page_analyzer.page_checker import extract_page_data
import page_analyzer.db as db
from dotenv import load_dotenv
from flask import (Flask, flash, get_flashed_messages, redirect,
                   render_template, request, url_for)
from requests import RequestException


app = Flask(__name__)

load_dotenv()

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')


@app.get('/')
def index():
    return render_template('index.html')


@app.post('/urls')
def add_url():
    url = request.form['url']

    normalized_url = normalize_url(url)

    validation_result = validate_url(url)

    if validation_result is not None:
        flash(validation_result, 'error')

        if validation_result == 'Некорректный URL':
            status_code = 422
        else:
            status_code = 400

        return render_template('index.html'), status_code

    # Проверка существования URL в базе данных

    existing_url = db.get_url_by_name(normalized_url)
    if existing_url:
        flash('Страница уже существует', 'info')
        return redirect(url_for('run_check', id=existing_url['id']))
    else:
        new_site_id = db.insert_into_urls(normalized_url, datetime.now())
        flash('Страница успешно добавлена', 'success')
        return redirect(url_for('run_check', id=new_site_id))


@app.get('/urls')
def show_urls():

    messages = get_flashed_messages(with_categories=True)
    show_error_message = any(category == 'error' for category, _ in messages)

    if show_error_message:
        return render_template('index.html')

    urls = db.get_all_urls()

    # Конвертируем полученный словарь в список
    urls_list = []
    for url in urls:
        if url['last_check']:
            url['last_check_formatted'] = \
                url['last_check'].strftime('%Y-%m-%d')
        urls_list.append(url)
    return render_template('urls.html', urls=urls_list)



@app.get('/urls/<int:id>')
def run_check(id):
    url_data = db.get_url_by_id(id)

    if not url_data:
        flash('Запись не найдена.', 'error')
        return redirect(url_for('show_urls'))

    # Получаем список проверок для данного URL
    checks = db.get_checks_for_url(id)

    for check in checks:
        check['created_at_formatted'] = \
            check['created_at'].strftime('%Y-%m-%d')

    # Аналогичная обработка для url_data
    if url_data and url_data['created_at']:
        url_data['created_at_formatted'] = \
            url_data['created_at'].strftime('%Y-%m-%d')

    return render_template('url_detail.html', url=url_data, checks=checks)


@app.post('/urls/<int:id>/checks')
def add_check(id):
    url_data = db.get_url_by_id(id)

    if not url_data:
        flash('Запись не найдена.', 'error')
        return redirect(url_for('show_urls'))

    try:
        response = requests.get(url_data['name'])
        response.raise_for_status()
        status_code = response.status_code
    except RequestException:
        flash("Произошла ошибка при проверке", 'error')
        return redirect(url_for('run_check', id=id))

    page_data = extract_page_data(response)

    db.insert_into_url_checks(id, page_data)

    flash('Страница успешно проверена', 'success'), status_code
    return redirect(url_for('run_check', id=id))

# Обработка ошибки 404 (страница не найдена)
@app.errorhandler(404)
def page_not_found(error):
    flash('Запрошенная страница не найдена.', 'error')
    return render_template('index.html'), 404


# Обработка ошибки 500 (внутренняя ошибка сервера)
@app.errorhandler(500)
def internal_server_error(error):
    flash('На сервере произошла ошибка. Попробуйте позже.', 'error')
    return render_template('index.html'), 500


if __name__ == '__main__':
    app.run(debug=True)
