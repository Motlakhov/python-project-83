import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from contextlib import contextmanager
from datetime import datetime


load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')


@contextmanager
def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def get_cursor(connection):
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    try:
        yield cursor
    finally:
        cursor.close()


def execute_query(query, params=None, single_result=False):
    with get_db_connection() as conn:
        with get_cursor(conn) as cur:
            cur.execute(query, params)
            conn.commit()
            
            # Проверяем, есть ли данные для получения
            if cur.description is not None:
                if single_result:
                    return cur.fetchone()
                else:
                    return cur.fetchall()
            else:
                return None


# Запросы в базу данных
def get_url_by_id(id):
    query = 'SELECT * FROM urls WHERE id = %s'
    result = execute_query(query, (id,), single_result=True)
    return result if result else None


def get_url_by_name(name):
    query = 'SELECT * FROM urls WHERE name = %s'
    result = execute_query(query, (name,), single_result=True)
    return result if result else None


def insert_into_urls(name, created_at):
    query = 'INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id'
    result = execute_query(query, (name, created_at), single_result=True)
    return result['id'] if result else None


def get_all_urls():
    query = (
        'SELECT u.id, u.name, '
        'MAX(uc.created_at) AS last_check, uc.status_code '
        'FROM urls u ' 
        'LEFT JOIN url_checks uc ON u.id = uc.url_id ' 
        'GROUP BY u.id, u.name, uc.status_code ' 
        'ORDER BY u.id DESC;'
    )
    results = execute_query(query)
    return results


def get_checks_for_url(id):
    query = (
        'SELECT * FROM url_checks '
        'WHERE url_id = %s '
        'ORDER BY created_at DESC;'
    )
    results = execute_query(query, (id,))
    return results


def insert_into_url_checks(url_id, data):
    query = (
        'INSERT INTO url_checks '
        '(url_id, status_code, created_at, h1, title, description) '
        'VALUES (%s, %s, %s, %s, %s, %s)'
    )
    query_params = (
        url_id, 
        data['status_code'], 
        datetime.now(), 
        data['h1'], 
        data['title'], 
        data['meta_description']
    )
    execute_query(query, query_params)
