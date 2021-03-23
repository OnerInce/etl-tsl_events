import requests
from bs4 import BeautifulSoup

html = requests.get("http://tff.org")
print(html.content)