from flask import Flask, Response
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import os

app = Flask(__name__)

# Feeds configurados
feeds = [
    {"name": "Botafogo", "url": "https://ge.globo.com/futebol/times/botafogo/"},
    {"name": "Flamengo", "url": "https://ge.globo.com/futebol/times/flamengo/"},
    {"name": "Vasco", "url": "https://ge.globo.com/futebol/times/vasco/"},
    {"name": "Fluminense", "url": "https://ge.globo.com/futebol/times/fluminense/"},
]

CACHE_FILE = "cache.json"

# Carregar ou criar cache
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
    """Normaliza URLs removendo parâmetros desnecessários."""
    from urllib.parse import urlparse, urlunparse
    parsed_url = urlparse(url)
    return urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, "", "", ""))

def gerar_rss(feed):
    """Gera RSS a partir do feed."""
    response = requests.get(feed["url"])
    soup = BeautifulSoup(response.text, "html.parser")

    # Seletores para extrair dados
    item_selector = "div.feed-post-body"
    title_selector = "a.feed-post-link"
    url_selector = "a.feed-post-link"

    # Inicializa cache para o feed
    if feed["name"] not in cache:
        cache[feed["name"]] = {"links": set(), "titles": set()}

    rss_items = ""
    now = datetime.utcnow()

    for item in soup.select(item_selector):
        title = item.select_one(title_selector).get_text(strip=True) if item.select_one(title_selector) else "Sem título"
        link = item.select_one(url_selector)["href"] if item.select_one(url_selector) else "#"
        link = normalize_url(link)

        # Evitar duplicações
        if link in cache[feed["name"]]["links"] or title in cache[feed["name"]]["titles"]:
            continue

        # Adicionar ao cache e ao RSS
        cache[feed["name"]]["links"].add(link)
        cache[feed["name"]]["titles"].add(title)
        rss_items += f"""
        <item>
          <title>{title}</title>
          <link>{link}</link>
          <pubDate>{now.strftime('%a, %d %b %Y %H:%M:%S GMT')}</pubDate>
        </item>
        """

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
        <title>Notícias do {feed['name']} - Globo Esporte</title>
        <link>{feed['url']}</link>
        <description>Últimas notícias do {feed['name']} no site Globo Esporte</description>
        <language>pt-BR</language>
        <lastBuildDate>{datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')}</lastBuildDate>
        {gerar_rss(feed)}
      </channel>
    </rss>"""
    return Response(rss_content, mimetype="application/rss+xml")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
