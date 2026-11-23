"""图片验证码生成（基于 Pillow），无第三方验证码依赖。"""
import io
import random

from PIL import Image, ImageDraw, ImageFont

# 验证码字符集（去除易混淆字符）
CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

# 候选字体：Windows 常见字体，找不到时回退默认字体
FONT_CANDIDATES = ["arial.ttf", "times.ttf", "simhei.ttf"]


def _load_font(size=32):
    """按优先级加载本地字体，失败则使用 Pillow 默认字体。"""
    for name in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def random_code(length=4):
    """生成随机验证码字符串。"""
    return "".join(random.choice(CHARS) for _ in range(length))


def generate_captcha_image(code):
    """根据验证码字符串绘制 PNG 图片，返回字节流。"""
    width, height = 130, 44
    image = Image.new("RGB", (width, height), (245, 247, 250))
    draw = ImageDraw.Draw(image)
    font = _load_font(30)

    # 干扰线
    for _ in range(4):
        start = (random.randint(0, width), random.randint(0, height))
        end = (random.randint(0, width), random.randint(0, height))
        draw.line([start, end], fill=(random.randint(150, 220),) * 3, width=1)
    # 干扰点
    for _ in range(60):
        draw.point(
            (random.randint(0, width), random.randint(0, height)),
            fill=(random.randint(120, 220),) * 3,
        )

    # 逐字符绘制，带轻微颜色差异
    x = 14
    for ch in code:
        color = (random.randint(40, 140), random.randint(40, 140), random.randint(40, 140))
        draw.text((x, random.randint(4, 10)), ch, font=font, fill=color)
        x += 26

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()
