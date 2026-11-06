"""Draws the 1080x1920 cartoon video frame by frame with Pillow, then encodes it with ffmpeg.

Layout: header, big hook text, product card with price sticker, product name,
speech subtitles, the mascot "Bili" (a talking shopping bag) and a "link sa comments" button.
"""
import hashlib
import math
import random
import subprocess
import tempfile
from functools import lru_cache
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

import config
import tts
from products import price_label

W, H, FPS = 1080, 1920, 24
INK = (45, 32, 60)

PALETTES = [  # (top colour, bottom colour)
    ((255, 107, 107), (255, 201, 113)),
    ((108, 99, 255), (110, 207, 255)),
    ((0, 184, 148), (162, 235, 120)),
    ((255, 118, 188), (255, 189, 105)),
    ((52, 152, 255), (140, 255, 210)),
    ((255, 140, 50), (255, 80, 120)),
]

CARD_W, CARD_H = 900, 700
CARD_CY = 880


# --- small helpers ------------------------------------------------------------
@lru_cache(maxsize=64)
def font(size):
    for path in (config.ASSETS_DIR / "fonts" / "DejaVuSans-Bold.ttf", Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")):
        try:
            return ImageFont.truetype(str(path), size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def clamp01(x):
    return max(0.0, min(1.0, x))


def ease_out_back(x):
    x = clamp01(x)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def gradient(top, bottom):
    col = Image.new("RGB", (1, H))
    px = col.load()
    for y in range(H):
        t = y / (H - 1)
        px[0, y] = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
    return col.resize((W, H))


def wrap(text, fnt, max_w, max_lines):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if not cur or fnt.getlength(trial) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and fnt.getlength(last + "…") > max_w:
            last = last[:-1]
        lines[-1] = last.rstrip() + "…"
    return lines


def draw_lines(d, lines, fnt, cx, y, fill=(255, 255, 255), stroke=INK, sw=8, gap=1.15):
    for line in lines:
        d.text((cx, y), line, font=fnt, fill=fill, stroke_width=sw, stroke_fill=stroke, anchor="ma")
        y += int(fnt.size * gap)
    return y


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True,
        text=True,
    )
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


# --- artwork --------------------------------------------------------------------
def load_product_image(source):
    if not source:
        return None
    try:
        if source.startswith("http"):
            r = requests.get(source, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            img = Image.open(BytesIO(r.content))
        else:
            img = Image.open(source)
        img = ImageOps.exif_transpose(img)
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGBA")
            flat = Image.new("RGB", img.size, "white")
            flat.paste(img, mask=img.split()[-1])
            return flat
        return img.convert("RGB")
    except Exception as exc:
        print(f"[video] could not load the product image ({exc}); drawing a gift box instead")
        return None


def draw_gift(d, cx, cy, colour):
    light = tuple(min(255, v + 30) for v in colour)
    gold, gold_dark = (255, 235, 120), (255, 205, 60)
    d.rounded_rectangle((cx - 190, cy - 90, cx + 190, cy + 240), 24, fill=colour, outline=INK, width=8)
    d.rounded_rectangle((cx - 220, cy - 190, cx + 220, cy - 80), 24, fill=light, outline=INK, width=8)
    d.rectangle((cx - 28, cy - 190, cx + 28, cy + 240), fill=gold, outline=INK, width=6)
    d.ellipse((cx - 120, cy - 300, cx - 5, cy - 170), fill=gold, outline=INK, width=6)
    d.ellipse((cx + 5, cy - 300, cx + 120, cy - 170), fill=gold, outline=INK, width=6)
    d.ellipse((cx - 30, cy - 215, cx + 30, cy - 155), fill=gold_dark, outline=INK, width=6)


def build_card(product_img, accent):
    pad = 60
    layer = Image.new("RGBA", (CARD_W + pad * 2, CARD_H + pad * 2), (0, 0, 0, 0))
    shadow = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((pad, pad + 18, pad + CARD_W, pad + CARD_H + 18), 60, fill=(0, 0, 0, 110))
    layer.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(22)))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((pad, pad, pad + CARD_W, pad + CARD_H), 60, fill=(255, 255, 255, 255), outline=INK, width=8)
    if product_img is not None:
        fitted = ImageOps.contain(product_img, (CARD_W - 80, CARD_H - 80))
        layer.paste(fitted, (pad + (CARD_W - fitted.width) // 2, pad + (CARD_H - fitted.height) // 2))
    else:
        draw_gift(d, pad + CARD_W // 2, pad + CARD_H // 2, accent)
    return layer


def draw_sticker(d, cx, cy, text, t, scale):
    points, outer, inner = 14, 150 * scale, 122 * scale
    spin = 0.15 + math.sin(t * 3) * 0.08
    pts = []
    for i in range(points * 2):
        ang = spin + i * math.pi / points
        rad = outer if i % 2 == 0 else inner
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    d.polygon(pts, fill=(235, 40, 60), outline=INK, width=6)
    n = len(text)
    size = 70 if n <= 4 else 50 if n <= 6 else 42 if n <= 8 else 34
    d.text((cx, cy), text, font=font(max(10, int(size * scale))), fill="white", anchor="mm", stroke_width=4, stroke_fill=INK)


def draw_mascot(d, cx, cy, t, talking, s=1.0):
    """'Bili', a yellow shopping bag with arms, big eyes and a mouth that moves while talking."""
    cy += -abs(math.sin(t * math.pi * 2.2)) * 26 * s

    def P(x, y):
        return (cx + x * s, cy + y * s)

    def w(n):
        return max(1, int(n * s))

    bag, bag_dark = (255, 200, 45), (245, 160, 20)
    d.arc([*P(-75, -215), *P(75, -75)], 180, 360, fill=INK, width=w(16))  # handle
    d.ellipse([*P(-95, 135), *P(-20, 185)], fill=bag_dark, outline=INK, width=w(7))  # feet
    d.ellipse([*P(20, 135), *P(95, 185)], fill=bag_dark, outline=INK, width=w(7))
    wave = math.sin(t * 9) * 38
    d.line([P(-125, 10), P(-205, 40)], fill=INK, width=w(16))  # arms
    d.ellipse([*P(-225, 20), *P(-185, 60)], fill=bag, outline=INK, width=w(6))
    d.line([P(125, 10), P(205, -40 + wave)], fill=INK, width=w(16))
    d.ellipse([*P(185, -60 + wave), *P(225, -20 + wave)], fill=bag, outline=INK, width=w(6))
    d.rounded_rectangle([*P(-135, -130), *P(135, 160)], w(44), fill=bag, outline=INK, width=w(9))  # body
    d.rounded_rectangle([*P(-135, -130), *P(135, -90)], w(30), fill=bag_dark, outline=INK, width=w(9))
    blink = (t % 3.2) < 0.14
    look = math.sin(t * 2) * 6
    for ex in (-55, 55):  # eyes
        if blink:
            d.line([P(ex - 26, -35), P(ex + 26, -35)], fill=INK, width=w(8))
        else:
            d.ellipse([*P(ex - 32, -70), *P(ex + 32, -4)], fill="white", outline=INK, width=w(6))
            d.ellipse([*P(ex - 13 + look, -48), *P(ex + 13 + look, -22)], fill=INK)
            d.ellipse([*P(ex - 5 + look, -44), *P(ex + 3 + look, -36)], fill="white")
    for ex in (-92, 92):  # cheeks
        d.ellipse([*P(ex - 20, 5), *P(ex + 20, 30)], fill=(255, 140, 150))
    if talking:
        open_h = 14 + 26 * abs(math.sin(t * 13))
        d.ellipse([*P(-30, 35), *P(30, 35 + open_h)], fill=(120, 30, 50), outline=INK, width=w(6))
    else:
        d.arc([*P(-34, 15), *P(34, 65)], 20, 160, fill=INK, width=w(8))
    d.ellipse([*P(-26, 85), *P(26, 137)], fill="white", outline=INK, width=w(5))  # badge
    d.text(P(0, 111), "B", font=font(w(40)), fill=INK, anchor="mm")


def draw_header(d):
    d.rounded_rectangle((50, 70, 600, 175), 52, fill=(255, 255, 255), outline=INK, width=7)
    d.text((325, 122), config.PAGE_NAME, font=font(62), fill=INK, anchor="mm")
    d.rounded_rectangle((860, 85, 1030, 160), 38, fill=INK)  # affiliate disclosure tag
    d.text((945, 122), "#ad", font=font(44), fill="white", anchor="mm")


def draw_subtitle(d, text):
    f = font(56)
    lines = wrap(text, f, 900, 2)
    y0, h = 1395, 40 + len(lines) * 68
    d.rounded_rectangle((70, y0, 1010, y0 + h), 40, fill=(30, 24, 44), outline=(255, 255, 255), width=4)
    draw_lines(d, lines, f, W // 2, y0 + 24, fill="white", stroke=(30, 24, 44), sw=0)


def draw_cta(d, since):
    s = ease_out_back(since / 0.5)
    cx, cy = 720, 1760
    bw, bh = 600 * s, 190 * s
    d.rounded_rectangle((cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2), int(60 * s), fill=(255, 235, 60), outline=INK, width=8)
    if s > 0.6:
        d.text((cx, cy - 30), "LINK SA COMMENTS", font=font(int(42 * s)), fill=INK, anchor="mm")
        ay = cy + 38 + math.sin(since * 10) * 8
        d.polygon([(cx - 30, ay - 18), (cx + 30, ay - 18), (cx, ay + 22)], fill=(235, 40, 60), outline=INK, width=5)


def make_confetti(seed):
    rnd = random.Random(seed)
    return [(rnd.randint(0, W), rnd.randint(0, H), rnd.randint(10, 26), rnd.uniform(40, 120), rnd.choice([0, 1])) for _ in range(26)]


def draw_confetti(d, items, t, colour):
    for x, y, r, speed, shape in items:
        yy = (y - speed * t) % H
        if shape:
            d.ellipse((x - r, yy - r, x + r, yy + r), fill=colour)
        else:
            d.rectangle((x - r, yy - r // 2, x + r, yy + r // 2), fill=colour)


# --- subtitles ------------------------------------------------------------------
def chunk_times(text, start, span):
    words = text.split()
    if not words:
        return []
    groups = math.ceil(len(words) / 6)
    per = math.ceil(len(words) / groups)
    chunks = [" ".join(words[i : i + per]) for i in range(0, len(words), per)]
    total = sum(len(c) for c in chunks)
    out, t = [], start
    for c in chunks:
        dur = span * len(c) / total
        out.append((t, t + dur, c))
        t += dur
    return out


# --- one frame ------------------------------------------------------------------
def draw_frame(t, c, poster=False):
    """poster=True draws the 'finished' look (hook, product card, price) with no subtitles or button.
    It is used as the very first frame and as the Facebook thumbnail, so the product is always visible."""
    if poster:
        t = 2.0
    img = c["bg"].copy()
    d = ImageDraw.Draw(img)
    draw_confetti(d, c["confetti"], t, c["confetti_colour"])
    draw_header(d)

    s = ease_out_back(t / 0.6)  # hook pops in
    if s > 0.02:
        draw_lines(d, c["hook_lines"], font(max(20, int(112 * s))), W // 2, 215 + int((1 - s) * 40), sw=12)

    cs = ease_out_back((t - 0.5) / 0.7)  # product card pops in
    if cs > 0.02:
        layer = c["card"]
        sw, sh = int(layer.width * cs), int(layer.height * cs)
        if sw > 4 and sh > 4:
            scaled = layer.resize((sw, sh), Image.BILINEAR)
            img.paste(scaled, (W // 2 - sw // 2, int(CARD_CY + math.sin(t * 2.4) * 10) - sh // 2), scaled)

    ss = ease_out_back((t - 1.1) / 0.5)
    if c["price"] and ss > 0.05:
        draw_sticker(d, 905, 585 + math.sin(t * 2.4) * 10, c["price"], t, ss)

    if t > 1.2:
        draw_lines(d, c["title_lines"], font(54), W // 2, 1262, sw=6)

    if not poster:
        for a, b, text in c["subs"]:
            if a <= t < b:
                draw_subtitle(d, text)
                break

        if t >= c["cta_start"]:
            draw_cta(d, t - c["cta_start"])

    draw_mascot(d, 210, 1760, t, (not poster) and c["talk_start"] <= t < c["talk_end"], 0.8)
    return img


# --- audio ----------------------------------------------------------------------
def pick_music():
    files = [p for p in (config.ASSETS_DIR / "music").glob("*") if p.suffix.lower() in (".mp3", ".m4a", ".wav", ".ogg")]
    return random.choice(files) if files else None


def build_audio(voice, speed, duration, out):
    """Voiceover (starting at 0.3s) plus optional quiet background music, padded to the video length."""
    music = pick_music()
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    if not voice and not music:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", f"{duration:.2f}", "-c:a", "aac", "-b:a", "128k", str(out)]
        subprocess.run(cmd, check=True)
        return
    inputs, parts, labels = [], [], []
    if voice:
        inputs += ["-i", str(voice)]
        tempo = f"atempo={speed:.3f}," if speed > 1.001 else ""
        parts.append(f"[{len(labels)}:a]{tempo}adelay=300|300,aresample=48000,apad[v]")
        labels.append("[v]")
    if music:
        inputs += ["-stream_loop", "-1", "-i", str(music)]
        parts.append(f"[{len(labels)}:a]aresample=48000,volume={0.16 if voice else 0.5}[m]")
        labels.append("[m]")
    if len(labels) == 2:
        parts.append("[v][m]amix=inputs=2:duration=longest:dropout_transition=0,volume=2,alimiter=limit=0.95[a]")
    else:
        parts.append(f"{labels[0]}anull[a]")
    cmd += inputs + ["-filter_complex", ";".join(parts), "-map", "[a]", "-t", f"{duration:.2f}", "-ac", "2", "-ar", "48000", "-c:a", "aac", "-b:a", "128k", str(out)]
    subprocess.run(cmd, check=True)


# --- main entry -------------------------------------------------------------------
def render(product, copy, out_path):
    """Make the video file for one product. Returns the path."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        voice = tts.synthesize(copy["voiceover"], tmp / "voice.mp3")
        vdur, speed = 0.0, 1.0
        if voice:
            vdur = probe_duration(voice)
            if vdur > 8.6:  # long voiceover: speed it up a little so it fits
                speed = min(vdur / 8.6, 1.35)
                vdur /= speed
        duration = min(config.MAX_SECONDS, max(config.MIN_SECONDS, vdur + 2.0)) if voice else 8.0

        audio = tmp / "audio.m4a"
        build_audio(voice, speed, duration, audio)

        top, bottom = PALETTES[int(hashlib.md5(product["title"].encode()).hexdigest(), 16) % len(PALETTES)]
        talk_start = 0.3
        talk_end = talk_start + vdur if voice else duration - 2.6
        ctx = {
            "bg": gradient(top, bottom),
            "confetti": make_confetti(product["title"]),
            "confetti_colour": tuple(int(v + (255 - v) * 0.55) for v in top),
            "card": build_card(load_product_image(product.get("image_url")), bottom),
            "hook_lines": wrap((copy["hook"] or "BILI NA KAYO!").upper(), font(112), 940, 2),
            "title_lines": wrap(copy.get("short_title") or product["title"], font(54), 960, 2),
            "price": price_label(product.get("price")),
            "subs": chunk_times(copy["voiceover"], talk_start, max(talk_end - talk_start, 2.0)),
            "talk_start": talk_start,
            "talk_end": talk_end,
            "cta_start": max(duration - 2.6, 3.0),
        }

        # Thumbnail: the "finished" look with the product image. Saved next to the video as a .jpg
        # and also used as the very first frame, because Facebook often takes the first frame as the cover.
        poster = draw_frame(0, ctx, poster=True)
        try:
            poster.convert("RGB").save(out_path.with_suffix(".jpg"), quality=92)
        except Exception as exc:
            print(f"[video] could not save the thumbnail image ({exc})")

        frames = int(duration * FPS)
        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-framerate", str(FPS), "-i", "-",
            "-i", str(audio),
            "-map", "0:v", "-map", "1:a",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p",
            "-r", str(FPS), "-g", str(FPS * 2),
            "-c:a", "copy", "-t", f"{duration:.2f}", "-movflags", "+faststart",
            str(out_path),
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        try:
            for i in range(frames):
                frame = poster if i == 0 else draw_frame(i / FPS, ctx)
                proc.stdin.write(frame.tobytes())
        except BrokenPipeError:
            pass
        finally:
            try:
                proc.stdin.close()
            except BrokenPipeError:
                pass
        if proc.wait() != 0:
            raise RuntimeError("ffmpeg failed while encoding the video")

    print(f"[video] made {out_path.name} ({duration:.1f}s)")
    return out_path
