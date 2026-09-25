"""Generate a branded image when an RSS article has no usable illustration."""

from io import BytesIO
from PIL import Image, ImageDraw, ImageFont


def branded_image() -> BytesIO:
    image = Image.new("RGB", (1200, 630), "#0c1527")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((54, 54, 1146, 576), radius=36, outline="#4c789f", width=3)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    try:
        large = ImageFont.truetype(font_path, 75)
        small = ImageFont.truetype(font_path, 35)
    except OSError:
        large = ImageFont.load_default()
        small = large
    draw.text((110, 180), "CRYPTO NEWS", fill="#f3f7ff", font=large)
    draw.text((114, 310), "WORLD  /  MARKETS  /  ANALYSIS", fill="#6ed3db", font=small)
    output = BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    output.name = "crypto-news.png"
    return output
