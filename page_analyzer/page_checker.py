from bs4 import BeautifulSoup
from requests import Response


def extract_page_data(response: Response):
    soup = BeautifulSoup(response.text, 'html.parser')

    h1_tag = soup.find('h1')
    title_tag = soup.find('title')
    meta_description_tag = soup.find('meta', attrs={'name': 'description'})

    return {
        'h1': h1_tag.text[:255] if h1_tag else '',
        'title': title_tag.text[:255] if title_tag else '',
        'status_code': response.status_code,
        'meta_description': (meta_description_tag.get('content', '')[:255]
                             if meta_description_tag else '')
    }
