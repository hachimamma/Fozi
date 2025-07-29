import discord
from discord.ext import commands
from datetime import datetime, timezone
import os

from dotenv import load_dotenv
from cardgen import generate_spotify_card

load_dotenv()

DISCORD_KEY = os.getenv("DISCORD_KEY")
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

bot.run(DISCORD_KEY)
