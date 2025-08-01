import discord
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import aiohttp

CHANNEL_ID = 1263067254803796030 #lobby/lounge/general

async def generate_welcome_image(member: discord.Member) -> BytesIO:
    bg = Image.new("RGBA", (512, 200), "#000000")
    draw = ImageDraw.Draw(bg)

    async with aiohttp.ClientSession() as session:
        async with session.get(member.display_avatar.url) as resp:
            avatar_data = await resp.read()
    pfp = Image.open(BytesIO(avatar_data)).convert("RGBA").resize((100, 100))

    mask = Image.new("L", (100, 100), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 100, 100), fill=255)
    bg.paste(pfp, (30, 50), mask)

    font_large = ImageFont.truetype("arial.ttf", 28)
    font_small = ImageFont.truetype("arial.ttf", 18)

    draw.text((150, 40), f"Welcome to The Coding Realm", font=font_large, fill="white")
    draw.text((150, 80), f"{member.name}#{member.discriminator}", font=font_small, fill="white")
    draw.text((150, 110), f"ID: {member.id}", font=font_small, fill="white")

    output = BytesIO()
    bg.save(output, format="PNG")
    output.seek(0)
    return output

async def handle_member_join(bot: discord.Client, member: discord.Member):
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return

    image_bytes = await generate_welcome_image(member)
    file = discord.File(image_bytes, filename="welcome.png")

    embed = discord.Embed(
        title="Welcome to The Coding Realm",
        description=f"Hey {member.mention}, glad to have you with us!",
        color=discord.Color.purple()
    )
    embed.set_image(url="attachment://welcome.png")

    await channel.send(file=file, embed=embed)
