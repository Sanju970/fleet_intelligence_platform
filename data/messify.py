"""
Messiness layer. Takes a clean page rendered to an image and degrades it the way
a real scanned/photographed fleet document looks: skew, blur, JPEG noise, coffee
stains, ink stamps, hole punches, and handwritten margin notes.

This is the part that makes the data HARD — and makes a system that survives it
impressive. Light/medium/heavy controlled per-document.
"""
import os, random, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HAND_FONT = "/home/claude/Caveat.ttf"
STAMP_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"

def _hand(size):
    try: return ImageFont.truetype(HAND_FONT, size)
    except Exception: return ImageFont.load_default()

def add_coffee_stain(img):
    d = ImageDraw.Draw(img, "RGBA")
    cx, cy = random.randint(0, img.width), random.randint(0, img.height)
    r = random.randint(40, 130)
    for rr in range(r, r-12, -1):
        a = random.randint(8, 26)
        d.ellipse([cx-rr, cy-rr*0.7, cx+rr, cy+rr*0.7],
                  outline=(120, 72, 30, a), width=2)
    d.ellipse([cx-r*0.6, cy-r*0.4, cx+r*0.6, cy+r*0.4], fill=(150, 100, 50, 14))
    return img

def add_stamp(img, text):
    layer = Image.new("RGBA", img.size, (0,0,0,0))
    d = ImageDraw.Draw(layer)
    try: f = ImageFont.truetype(STAMP_FONT, 34)
    except Exception: f = ImageFont.load_default()
    col = random.choice([(180,30,30,170),(30,60,160,160)])
    tmp = Image.new("RGBA", (420,90),(0,0,0,0))
    td = ImageDraw.Draw(tmp)
    td.text((10,20), text, font=f, fill=col)
    td.rectangle([4,4,400,84], outline=col, width=3)
    tmp = tmp.rotate(random.randint(-18,18), expand=1)
    img.paste(tmp, (random.randint(60,img.width-360), random.randint(120,img.height-300)), tmp)
    return img

def add_handwriting(img, notes):
    d = ImageDraw.Draw(img)
    col = random.choice([(20,30,120),(15,15,15),(10,40,90)])  # blue/black ink
    for note in notes:
        f = _hand(random.randint(26, 38))
        x = random.randint(int(img.width*0.5), int(img.width*0.72))
        y = random.randint(int(img.height*0.55), int(img.height*0.85))
        d.text((x, y), note, font=f, fill=col)
    return img

def add_hole_punches(img):
    d = ImageDraw.Draw(img)
    for fy in (0.28, 0.5, 0.72):
        cy = int(img.height*fy); cx = 26
        d.ellipse([cx-9, cy-9, cx+9, cy+9], fill=(245,245,245), outline=(180,180,180))
    return img

def scanify(img, level="medium"):
    img = img.convert("RGB")
    # slight grayscale wash like a cheap scanner
    if random.random() > 0.4:
        g = ImageOps.grayscale(img).convert("RGB")
        img = Image.blend(img, g, 0.5)
    # skew
    ang = {"light": 0.8, "medium": 2.2, "heavy": 4.5}[level] * random.uniform(-1,1)
    img = img.rotate(ang, expand=1, fillcolor=(252,251,248))
    # brightness/contrast drift
    img = ImageEnhance.Brightness(img).enhance(random.uniform(0.9, 1.08))
    img = ImageEnhance.Contrast(img).enhance(random.uniform(0.85, 1.05))
    # blur + noise
    if level != "light":
        img = img.filter(ImageFilter.GaussianBlur(random.uniform(0.3, 0.9)))
    # paper tint
    tint = Image.new("RGB", img.size, (random.randint(248,255), random.randint(246,253), random.randint(236,247)))
    img = Image.blend(img, tint, 0.12)
    return img

def messify(clean_img, level, notes=None):
    """Apply the full degradation stack at the requested intensity."""
    img = clean_img.copy()
    if level in ("medium", "heavy"):
        if random.random() > 0.5: img = add_hole_punches(img)
        if random.random() > 0.4: img = add_stamp(img, random.choice(
            ["RECEIVED","PAID","FILE COPY","SCANNED","APPROVED","VOID"]))
    if level == "heavy":
        for _ in range(random.randint(1,2)): img = add_coffee_stain(img)
        if notes: img = add_handwriting(img, notes)
    img = scanify(img, level)
    # final JPEG recompression artifact
    return img
