import requests
from bs4 import BeautifulSoup
import re

def extract_info_from_url(url):
    """Пытается извлечь название и описание из URL"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Попытка извлечь заголовок
        title = soup.find('meta', property='og:title')
        if title and title.get('content'):
            title = title['content']
        else:
            title = soup.title.string.strip() if soup.title else None

        # Попытка извлечь описание
        desc = soup.find('meta', property='og:description')
        if desc and desc.get('content'):
            desc = desc['content']
        else:
            desc_tag = soup.find('meta', attrs={'name': 'description'})
            desc = desc_tag['content'] if desc_tag else None

        if not title:
            # Простой regex для извлечения домена и пути
            match = re.search(r'https?://([^/]+)', url)
            title = match.group(1) if match else url

        return title, desc
    except Exception:
        return None, None