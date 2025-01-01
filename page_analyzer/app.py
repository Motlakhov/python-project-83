import os
import requests
from datetime import datetime
from page_analyzer.utils import normalize_url, validate_url
from page_analyzer.page_checker import extract_page_data
from page_analyzer.db import (get_url_by_name, insert_into_urls, 
                              get_all_urls, get_url_by_id, 
                              get_checks_for_url, insert_into_url_checks)
from dotenv import load_dotenv
from flask import (Flask, flash, get_flashed_messages, redirect,
                   render_template, request, session, url_for)
from requests import RequestException


app = Flask(__name__)

load_dotenv()

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/urls', methods=['POST'])
def post_index():
    url = request.form.get('url')

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

    existing_url = get_url_by_name(normalized_url)
    if existing_url:
        flash('Страница уже существует', 'info')
        return redirect(url_for('url_detail', id=existing_url['id']))
    else:
        new_site_id = insert_into_urls(normalized_url, datetime.now()) 
        flash('Страница успешно добавлена', 'success')
        return redirect(url_for('url_detail', id=new_site_id))


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


@app.route('/urls', methods=['GET'])
def urls():

    messages = get_flashed_messages(with_categories=True)
    show_error_message = any(category == 'error' for category, _ in messages)

    if show_error_message:
        return render_template('index.html')

    urls = get_all_urls()

    # Конвертируем полученный словарь в список
    urls_list = []
    for url in urls:
        if url['last_check']:
            url['last_check_formatted'] = url['last_check'].strftime('%Y-%m-%d')
        urls_list.append(url)
    return render_template('urls.html', urls=urls_list)


@app.route('/urls/<int:id>', methods=['GET'])
def url_detail(id):
    url_data = get_url_by_id(id)         

    if not url_data:
        flash('Запись не найдена.', 'error')
        return redirect(url_for('urls'))

    # Получаем список проверок для данного URL
    checks = get_checks_for_url(id)

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
    url_data = get_url_by_id(id)
        
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
    
    page_data = extract_page_data(response)

    insert_into_url_checks(id, page_data)

    flash('Страница успешно проверена', 'success')
    return redirect(url_for('url_detail', id=id))


if __name__ == '__main__':
    app.run(debug=True)
