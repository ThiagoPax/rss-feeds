from flask import Flask, Response
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.parse import urlparse, urlunparse
import os
import json

app = Flask(__name__)

# Configuração dos feeds
feeds = [
    {"name": "Botafogo", "url": "https://ge.globo.com/busca/?q=Botafogo&order=recent&species=not%C3%ADcias"},
    {"name": "Flamengo", "url": "https://ge.globo.com/busca/?q=Flamengo&order=recent&species=not%C3%ADcias"},
    {"name": "Vasco", "url": "https://ge.globo.com/busca/?q=Vasco&order=recent&species=not%C3%ADcias"},
    {"name": "Fluminense", "url": "https://ge.globo.com/busca/?q=Fluminense&order=recent&species=not%C3%ADcias"},
    {"name": "Carioca", "url": "https://ge.globo.com/busca/?q=Carioca&order=recent&species=not%C3%ADcias&from=now-1w"}
]

CACHE_FILE = "cache.json"

# Carrega o cache existente ou cria um novo
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
        cache = json.load(f)
else:
    cache = {}

def save_cache():
    """Salva o cache no disco."""
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)

def normalize_url(url):
    """Remove parâmetros desnecessários dos links."""
    parsed_url = urlparse(url)
    clean_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, "", "", ""))
    return clean_url

def gerar_rss(feed):
    response = requests.get(feed["url"])
    soup = BeautifulSoup(response.text, "html.parser")

    item_selector = "li.widget--card.widget--info"
    title_selector = "div.widget--info__title"
    url_selector = "a"

    # Inicializa o cache para o feed, se não existir
    if feed["name"] not in cache:
        cache[feed["name"]] = {"links": set(), "titles": set()}

    rss_items = ""
    now = datetime.utcnow()

    for item in soup.select(item_selector):
        title = item.select_one(title_selector).get_text(strip=True) if item.select_one(title_selector) else "Sem título"
        link = item.select_one(url_selector)["href"] if item.select_one(url_selector) else "#"
        link = normalize_url(link)

        # Verifica duplicação por link e título
        if link in cache[feed["name"]]["links"] or title in cache[feed["name"]]["titles"]:
            continue

        # Adiciona ao cache e ao feed
        cache[feed["name"]]["links"].add(link)
        cache[feed["name"]]["titles"].add(title)
        rss_items += f"""
        <item>
          <title>{title}</title>
          <link>{link}</link>
          <pubDate>{now.strftime('%a, %d %b %Y %H:%M:%S GMT')}</pubDate>
        </item>
        """

    # Salva o cache após processar
    save_cache()
    return rss_items

@app.route("/<team>")
def feed(team):
    feed = next((f for f in feeds if f["name"].lower() == team.lower()), None)
    if not feed:
        return Response("Feed não encontrado.", status=404)
    rss_content = f"""<?xml version="1.0" encoding="UTF-8" ?>
    <rss version="2.0">
      <channel>
        <title>Notícias do {feed['name']} - ge.globo.com</title>
        <link>{feed['url']}</link>
        <description>Feed de notícias recentes do {feed['name']} no site ge.globo.com</description>
        <language>pt-BR</language>
        <lastBuildDate>{datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')}</lastBuildDate>
        {gerar_rss(feed)}
      </channel>
    </rss>"""
    return Response(rss_content, mimetype="application/rss+xml")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
