import aiohttp
import re
from bs4 import BeautifulSoup

GENIUS_SEARCH_URL = "https://genius.com/api/search/multi"

async def fetch(artist: str, title: str) -> str | None:
    query = f"{title} {artist}"
    async with aiohttp.ClientSession() as session:
        async with session.get(GENIUS_SEARCH_URL, params={"q": query}) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()

    hits = [
        section for section in data["response"]["sections"]
        if section["type"] == "song"
    ]
    if not hits or not hits[0]["hits"]:
        return None

    url = hits[0]["hits"][0]["result"]["url"]

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as page:
            if page.status != 200:
                return None
            html = await page.text()

    soup = BeautifulSoup(html, "html.parser")
    lyrics_divs = soup.find_all("div", attrs={"data-lyrics-container": "true"})
    if not lyrics_divs:
        return None

    lyrics = "\n".join(div.get_text(separator="\n").strip() for div in lyrics_divs)
    lyrics = re.sub(r'\n{3,}', '\n\n', lyrics).strip()
    return lyrics
