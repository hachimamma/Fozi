import discord
import io
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageOps

def rounded_rectangle(image, radius):
    mask = Image.new('L', image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), image.size], radius, fill=255)
    image.putalpha(mask)
    return image

def load_font(possible_names, size):
    for name in possible_names:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()

def fit_text(draw, text, font_paths, max_width, max_size, min_size):
    size = max_size
    while size >= min_size:
        font = load_font(font_paths, size)
        width = draw.textlength(text, font=font)
        if width <= max_width:
            return font, text
        size -= 2
    font = load_font(font_paths, min_size)
    ellipsis = "..."
    display_text = text
    while draw.textlength(display_text + ellipsis, font=font) > max_width and len(display_text) > 0:
        display_text = display_text[:-1]
    return font, display_text + ellipsis

def create_true_gradient(width, height):
    grad = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(grad)
    for x in range(width):
        alpha = int(255 * (1 - (x / width)) ** 3.5)
        draw.line([(x, 0), (x, height)], fill=(0, 0, 0, alpha))
    return grad

async def generate_spotify_card(title, artists, album_url, elapsed, duration):
    width, height = 1200, 600

    async with aiohttp.ClientSession() as session:
        async with session.get(album_url) as resp:
            cover_data = await resp.read()
    cover = Image.open(io.BytesIO(cover_data)).convert("RGBA")
    cover = ImageOps.fit(cover, (width, height), centering=(0.5, 0.5), method=Image.LANCZOS)

    card = Image.new("RGBA", (width, height))
    card.paste(cover, (0, 0))

    grad = create_true_gradient(width, height)
    card = Image.alpha_composite(card, grad)

    draw = ImageDraw.Draw(card)
    font_bold_names = [
        "fonts/DejaVuSans-Bold.ttf"
    ]
    font_regular_names = [
        "fonts/DejaVuSans.ttf"
    ]

    font_title, display_title = fit_text(draw, title, font_bold_names, 1040, 84, 40)
    draw.text((80, 120), display_title, font=font_title, fill=(255, 255, 255, 255))

    font_artist = load_font(font_regular_names, 40)
    draw.text((80, 120 + font_title.size + 20), ", ".join(artists), font=font_artist, fill=(220, 220, 220, 255))

    bar_y = height - 80
    bar_x = 80
    bar_w = width - 2 * bar_x
    bar_h = 8
    knob_r = 12
    progress = min(max(elapsed / duration, 0), 1.0) if duration > 0 else 0
    knob_x = bar_x + int(bar_w * progress)
    knob_y = bar_y

    draw.rectangle([bar_x, bar_y, knob_x, bar_y + bar_h], fill=(255, 255, 255, 180))
    draw.line([(knob_x, bar_y + bar_h // 2), (bar_x + bar_w, bar_y + bar_h // 2)], fill=(255, 255, 255, 100), width=2)
    draw.ellipse([knob_x - knob_r, knob_y - knob_r + 4, knob_x + knob_r, knob_y + knob_r + 4], fill=(255, 255, 255, 230))

    font_time = load_font(font_regular_names, 32)
    elapsed_str = f"{int(elapsed // 60):02}:{int(elapsed % 60):02}"
    duration_str = f"{int(duration // 60):02}:{int(duration % 60):02}"
    draw.text((bar_x, bar_y + 20), elapsed_str, font=font_time, fill=(255, 255, 255, 180))
    time_w = draw.textlength(duration_str, font=font_time)
    draw.text((bar_x + bar_w - time_w, bar_y + 20), duration_str, font=font_time, fill=(255, 255, 255, 180))

    card = rounded_rectangle(card, 40)

    buf = io.BytesIO()
    card.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return discord.File(buf, filename="spotify_card.png")
