import discord
from discord.ext import commands
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import aiohttp
import io
import os
from collections import Counter

GUILD_ID = 1381641115618377788

intents = discord.Intents.default()
intents.presences = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='.', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command()
async def test(ctx):
    await ctx.send("Fozi is alive!")

def get_dominant_color(image):
    image = image.resize((50, 50))
    pixels = list(image.getdata())
    pixels = [p for p in pixels if sum(p) > 100]  # avoid too-dark pixels
    most_common = Counter(pixels).most_common(1)[0][0] if pixels else (255, 140, 0)
    return most_common

async def generate_spotify_card(title, artists, album_url, elapsed, duration):
    width, height = 1500, 600
    bg_color = (28, 28, 28)
    image = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(image)

    async with aiohttp.ClientSession() as session:
        async with session.get(album_url) as resp:
            cover_data = await resp.read()
    cover = Image.open(io.BytesIO(cover_data)).resize((600, 600))
    image.paste(cover, (0, 0))

    accent_color = get_dominant_color(cover)

    def brighten(color, factor=1.8):
        return tuple(min(int(c * factor), 255) for c in color)
    accent_color = brighten(accent_color)

    def load_font(font_name, size):
        try:
            return ImageFont.truetype(font_name, size)
        except:
            return ImageFont.load_default()

    title_font = load_font("arial.ttf", 56)
    artist_font = load_font("arial.ttf", 48)
    time_font = load_font("arial.ttf", 44)

    draw.text((660, 80), title.upper(), font=title_font, fill=accent_color)
    draw.text((660, 160), ", ".join(artists), font=artist_font, fill=(180, 180, 180))

    bar_x, bar_y = 660, 240
    bar_w, bar_h = 780, 24
    progress = min(elapsed / duration, 1)
    filled = int(bar_w * progress)

    draw.rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], fill=(70, 70, 70))
    draw.rectangle([bar_x, bar_y, bar_x + filled, bar_y + bar_h], fill=accent_color)

    draw.text((bar_x, bar_y + 30), f"{int(elapsed//60):02}:{int(elapsed%60):02}", font=time_font, fill="gray")
    draw.text((bar_x + bar_w - 100, bar_y + 30), f"{int(duration//60):02}:{int(duration%60):02}", font=time_font, fill="gray")

    buffer = io.BytesIO()
    image.save(buffer, format="PNG", quality=95)
    buffer.seek(0)
    return discord.File(buffer, filename="spotify.png")

@bot.command()
async def sp(ctx):
    if ctx.guild is None or ctx.guild.id != GUILD_ID:
        return await ctx.send("This command is only available in the main server.")

    user = ctx.author

    if not hasattr(user, 'activities') or not user.activities:
        return await ctx.send("No activity detected.")

    spotify = next((a for a in user.activities if isinstance(a, discord.Spotify)), None)

    if not spotify:
        return await ctx.send("You're not listening to Spotify right now.")

    now = datetime.now(timezone.utc)
    elapsed = (now - spotify.start).total_seconds()
    duration = (spotify.end - spotify.start).total_seconds()

    file = await generate_spotify_card(
        title=spotify.title,
        artists=spotify.artists,
        album_url=spotify.album_cover_url,
        elapsed=elapsed,
        duration=duration
    )

    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Open in Spotify", url=f"https://open.spotify.com/track/{spotify.track_id}"))

    await ctx.send(file=file, view=view)

@bot.command()
async def debug(ctx):
    if ctx.guild is None or ctx.guild.id != GUILD_ID:
        return await ctx.send("This command is only available in the main server.")

    user = ctx.author
    if not hasattr(user, 'activities') or not user.activities:
        return await ctx.send("No activities found.")

    msg = "\n".join(str(a) for a in user.activities)
    await ctx.send(f"Activities:\n```{msg}```")

bot.run("MTM5OTMwNjYyMDg0ODA0NjE2MQ.GdhGWV.hU-b-rD5huXzPrGfM6qQgoO1JVDhO7Srt0wud4")
