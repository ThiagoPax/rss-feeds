from flask import Flask, Response
import requests
from bs4 import BeautifulSoup
from datetime import datetime

app = Flask(__name__)

# Configuração dos feeds
feeds = [
    {"name": "Botafogo", "url": "https://ge.globo.com/busca/?q=Botafogo&order=recent&species=not%C3%ADcias"},
    {"name": "Flamengo", "url": "https://ge.globo.com/busca/?q=Flamengo&order=recent&species=not%C3%ADcias"},
    {"name": "Vasco", "url": "https://ge.globo.com/busca/?q=Vasco&order=recent&species=not%C3%ADcias"},
    {"name": "Fluminense", "url": "https://ge.globo.com/busca/?q=Fluminense&order=recent&species=not%C3%ADcias"},
    {"name": "Carioca", "url": "https://ge.globo.com/busca/?q=Carioca&order=recent&species=not%C3%ADcias&from=now-1w"}
]

# Função para gerar os itens do feed
def gerar_rss(feed):
    response = requests.get(feed["url"])
    soup = BeautifulSoup(response.text, "html.parser")

    item_selector = "li.widget--card.widget--info"
    title_selector = "div.widget--info__title"
    url_selector = "a"

    rss_items = ""
    for item in soup.select(item_selector):
        title = item.select_one(title_selector).get_text(strip=True) if item.select_one(title_selector) else "Sem título"
        link = item.select_one(url_selector)["href"] if item.select_one(url_selector) else "#"
        rss_items += f"""
        <item>
          <title>{title}</title>
          <link>{link}</link>
          <pubDate>{datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')}</pubDate>
        </item>
        """
    return rss_items

# Rota para exibir o feed RSS
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
        <lastBuildDate>{datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')}</lastBuildDate>
        {gerar_rss(feed)}
      </channel>
    </rss>"""
    return Response(rss_content, mimetype="application/rss+xml")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
