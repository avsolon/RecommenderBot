import requests
from bs4 import BeautifulSoup

def parse_url(url):
    try:
        r = requests.get(url, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        return soup.title.string if soup.title else None
    except:
        return None