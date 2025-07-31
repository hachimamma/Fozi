import random
import discord

DAD_JOKES = [
    "Why don't skeletons fight each other? They don't have the guts.",
    "I'm reading a book about anti-gravity. It's impossible to put down!",
    "Why did the scarecrow win an award? Because he was outstanding in his field.",
    "What do you call fake spaghetti? An impasta!"
]

VIBES = [
    "The vibe is immaculate (absolute chad)",
    "Hmm... questionable vibes detected (nuh uh go away)",
    "Vibe check failed. Try again (dude u stink)",
    "Vibes are off the charts (cool guy fr)",
    "Vibe is strong with this one XD",
    "The vibes are... undefined D;"
]

FORTUNES = [
    "You will have a pleasant surprise.",
    "Now is a good time to try something new.",
    "A thrilling time is in your immediate future.",
    "You will find what you seek.",
    "Adventure awaits you soon.",
    "Don't pursue happiness- create it."
]

WAIFUS = ["Rem", "Zero Two", "Asuna", "Hinata", "Saber", "Kurisu", "Rias Gremory"]
HUSBANDOS = ["Levi", "Kakashi", "Lelouch", "Gojo", "Roy Mustang", "Kazuma", "Kamina"]

DRIP_LEVELS = [
    "Dripless (u wont EVER get the huzz bro)",
    "Just a little drip :] (u stink, get better)",
    "Decent drip :) (ur cool bro alright)",
    "Certified drip :> (lord have mercy)",
    "Drip overload XD (leave some for the rest of us dude)"
]

EMBED_COLOR = discord.Color.purple()

def dad_joke(user=None):
    embed = discord.Embed(
        title="Dad Joke",
        description=random.choice(DAD_JOKES),
        color=EMBED_COLOR
    )
    if user:
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
    return embed

def vibe_cmd(user=None):
    embed = discord.Embed(
        title="Vibe Check",
        description=random.choice(VIBES),
        color=EMBED_COLOR
    )
    if user:
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
    return embed

def fortune_cmd(user=None):
    embed = discord.Embed(
        title="Fortune Cookie",
        description=random.choice(FORTUNES),
        color=EMBED_COLOR
    )
    if user:
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
    return embed

def waifu_cmd(user=None):
    embed = discord.Embed(
        title="Random Waifu",
        description=f"Your random waifu: {random.choice(WAIFUS)} UwU",
        color=EMBED_COLOR
    )
    if user:
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
    return embed

def husbando_cmd(user=None):
    embed = discord.Embed(
        title="Random Husbando",
        description=f"Your random husbando: {random.choice(HUSBANDOS)} UwU",
        color=EMBED_COLOR
    )
    if user:
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
    return embed

def rate_cmd(thing: str, user=None):
    rating = random.randint(1, 10)
    embed = discord.Embed(
        title="Rating",
        description=f"I rate {thing} a {rating}/10 :3",
        color=EMBED_COLOR
    )
    if user:
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
    return embed

def drip_cmd(user_mention: str, user=None):
    embed = discord.Embed(
        title="Drip Check",
        description=f"{user_mention}'s drip: {random.choice(DRIP_LEVELS)}",
        color=EMBED_COLOR
    )
    if user:
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
    return embed

def battleroyale_cmd(user_mentions, user=None):
    if len(user_mentions) < 2:
        embed = discord.Embed(
            title="Battle Royale",
            description="You need at least two fighters!",
            color=EMBED_COLOR
        )
    else:
        winner = random.choice(user_mentions)
        msg = f"Battle Royale: {', '.join(user_mentions)}\nWinner: {winner}!"
        embed = discord.Embed(
            title="Battle Royale",
            description=msg,
            color=EMBED_COLOR
        )
    if user:
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
    return embed