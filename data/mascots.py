"""The five BiliNaKayo! mascots, drawn with Pillow.

Every drawer has the same signature and fits in roughly the same box (about 450 wide, 400 tall
around the centre point), so any of them can sit in the bottom-left corner of the video.
The names must match the "name" values in config.CHARACTERS.
"""
import math

INK = (45, 32, 60)
SKIN = (240, 190, 150)
DEEP_RED = (120, 30, 50)


# --- shared pieces ----------------------------------------------------------------
def _eyes(d, P, w, t, y=-37, dx=55, r=32):
    blink = (t % 3.2) < 0.14
    look = math.sin(t * 2) * r / 5
    for ex in (-dx, dx):
        if blink:
            d.line([P(ex - r * 0.8, y), P(ex + r * 0.8, y)], fill=INK, width=w(8))
        else:
            d.ellipse([*P(ex - r, y - r * 1.03), *P(ex + r, y + r * 1.03)], fill="white", outline=INK, width=w(6))
            pr = r * 0.4
            d.ellipse([*P(ex - pr + look, y - pr + r * 0.15), *P(ex + pr + look, y + pr + r * 0.15)], fill=INK)
            hr = pr * 0.3
            d.ellipse([*P(ex - hr + look - 2, y - pr * 0.5), *P(ex + hr + look - 2, y - pr * 0.5 + hr * 2)], fill="white")


def _mouth(d, P, w, t, talking, y=35, half=30):
    if talking:
        open_h = 14 + 26 * abs(math.sin(t * 13))
        d.ellipse([*P(-half, y), *P(half, y + open_h)], fill=DEEP_RED, outline=INK, width=w(6))
    else:
        d.arc([*P(-half - 4, y - 20), *P(half + 4, y + 30)], 20, 160, fill=INK, width=w(8))


def _cheeks(d, P, dx, y, r=20):
    for ex in (-dx, dx):
        d.ellipse([*P(ex - r, y), *P(ex + r, y + r * 1.25)], fill=(255, 140, 150))


def _arms(d, P, w, t, colour, sx, sy, left=True):
    """Left arm hangs down, right arm waves. Hands are small circles."""
    wave = math.sin(t * 9) * 38
    if left:
        d.line([P(-sx, sy), P(-sx - 80, sy + 30)], fill=INK, width=w(18))
        d.line([P(-sx, sy), P(-sx - 80, sy + 30)], fill=colour, width=w(10))
        d.ellipse([*P(-sx - 100, sy + 12), *P(-sx - 60, sy + 52)], fill=colour, outline=INK, width=w(6))
    d.line([P(sx, sy), P(sx + 80, sy - 50 + wave)], fill=INK, width=w(18))
    d.line([P(sx, sy), P(sx + 80, sy - 50 + wave)], fill=colour, width=w(10))
    d.ellipse([*P(sx + 60, sy - 70 + wave), *P(sx + 100, sy - 30 + wave)], fill=colour, outline=INK, width=w(6))


# --- Kayo: a cheerful round chick in a tiny shopping bag ----------------------------
def _kayo(d, P, w, t, talking, font_fn):
    yellow, yellow_dark, orange = (255, 214, 60), (245, 170, 30), (255, 140, 40)
    wave = math.sin(t * 9) * 38
    for x0, x1 in ((-70, -15), (15, 70)):  # feet
        d.ellipse([*P(x0, 150), *P(x1, 190)], fill=orange, outline=INK, width=w(6))
    d.ellipse([*P(-30, -170), *P(30, -120)], fill=yellow, outline=INK, width=w(6))  # head tuft
    d.ellipse([*P(-120, -135), *P(120, 105)], fill=yellow, outline=INK, width=w(9))  # round body
    d.ellipse([*P(-165, -15), *P(-110, 55)], fill=yellow_dark, outline=INK, width=w(6))  # wings
    d.ellipse([*P(110, -45 + wave), *P(165, 25 + wave)], fill=yellow_dark, outline=INK, width=w(6))
    d.rounded_rectangle([*P(-105, 60), *P(105, 170)], w(26), fill=(255, 90, 110), outline=INK, width=w(8))  # tiny bag
    d.rounded_rectangle([*P(-105, 60), *P(105, 90)], w(16), fill=(225, 60, 90), outline=INK, width=w(8))
    for x0 in (-85, 25):  # bag handles
        d.arc([*P(x0, 20), *P(x0 + 60, 100)], 180, 360, fill=INK, width=w(9))
    _eyes(d, P, w, t, y=-55, dx=50, r=28)
    _cheeks(d, P, 88, -15, 18)
    _mouth(d, P, w, t, talking, y=22, half=22)
    d.polygon([P(-22, -22), P(22, -22), P(0, 12)], fill=orange, outline=INK)  # beak
    d.line([P(-22, -22), P(22, -22), P(0, 12), P(-22, -22)], fill=INK, width=w(5))


# --- Mang Bili: a friendly sari-sari store uncle with a big smile -------------------
def _mang_bili(d, P, w, t, talking, font_fn):
    skin, shirt, cap = (224, 172, 120), (35, 170, 160), (235, 60, 70)
    _arms(d, P, w, t, skin, 110, 40)
    d.rounded_rectangle([*P(-115, -10), *P(115, 175)], w(40), fill=shirt, outline=INK, width=w(9))  # shirt
    d.rounded_rectangle([*P(-80, 55), *P(80, 175)], w(26), fill="white", outline=INK, width=w(6))  # apron
    d.rounded_rectangle([*P(-45, 90), *P(45, 135)], w(12), fill=(255, 235, 200), outline=INK, width=w(5))  # pocket
    d.ellipse([*P(-90, -195), *P(90, -15)], fill=skin, outline=INK, width=w(9))  # head
    d.pieslice([*P(-92, -205), *P(92, -35)], 180, 360, fill=cap, outline=INK, width=w(8))  # cap
    d.rounded_rectangle([*P(-105, -130), *P(105, -112)], w(8), fill=(200, 40, 55), outline=INK, width=w(6))  # brim
    _eyes(d, P, w, t, y=-80, dx=38, r=20)
    _cheeks(d, P, 66, -60, 16)
    _mouth(d, P, w, t, talking, y=-33, half=24)
    for sign in (-1, 1):  # moustache
        x0, x1 = (-42, 0) if sign < 0 else (0, 42)
        d.ellipse([*P(x0, -64), *P(x1, -44)], fill=(70, 45, 35), outline=INK, width=w(4))


# --- Ate Deals: a savvy girl with a bargain tag necklace ---------------------------
def _ate_deals(d, P, w, t, talking, font_fn):
    hair, dress, tag = (85, 52, 40), (255, 105, 180), (255, 225, 80)
    _arms(d, P, w, t, SKIN, 112, 40)
    d.polygon([P(-80, -20), P(80, -20), P(135, 175), P(-135, 175)], fill=dress, outline=INK)  # dress
    d.line([P(-80, -20), P(80, -20), P(135, 175), P(-135, 175), P(-80, -20)], fill=INK, width=w(9))
    for cx in (-125, 125):  # pigtails
        d.ellipse([*P(cx - 38, -170), *P(cx + 38, -88)], fill=hair, outline=INK, width=w(7))
    d.ellipse([*P(-100, -205), *P(100, -15)], fill=hair, outline=INK, width=w(8))  # back hair
    d.ellipse([*P(-88, -190), *P(88, -20)], fill=SKIN, outline=INK, width=w(8))  # face
    d.pieslice([*P(-92, -196), *P(92, -22)], 180, 360, fill=hair, outline=INK, width=w(6))  # bangs
    for cx in (-86, 86):  # scrunchies
        d.ellipse([*P(cx - 14, -128), *P(cx + 14, -104)], fill=(235, 40, 60), outline=INK, width=w(4))
    _eyes(d, P, w, t, y=-68, dx=38, r=24)
    _cheeks(d, P, 62, -45, 16)
    _mouth(d, P, w, t, talking, y=-32, half=20)
    d.arc([*P(-60, -50), *P(60, 85)], 20, 160, fill=INK, width=w(5))  # necklace string
    d.rounded_rectangle([*P(-26, 40), *P(26, 92)], w(10), fill=tag, outline=INK, width=w(6))  # bargain tag
    d.text(P(0, 66), "%", font=font_fn(w(36)), fill=(235, 40, 60), anchor="mm")


# --- Boss Tipid: a chubby piggy bank wearing sunglasses -----------------------------
def _boss_tipid(d, P, w, t, talking, font_fn):
    pink, pink_dark, snout = (255, 150, 180), (240, 110, 150), (255, 120, 160)
    d.arc([*P(115, -10), *P(185, 70)], 270, 120, fill=INK, width=w(10))  # curly tail
    for x0, x1 in ((-95, -45), (45, 95)):  # legs
        d.rounded_rectangle([*P(x0, 120), *P(x1, 190)], w(18), fill=pink_dark, outline=INK, width=w(7))
    for pts in ([(-115, -90), (-65, -180), (-30, -110)], [(115, -90), (65, -180), (30, -110)]):  # ears
        d.polygon([P(*p) for p in pts], fill=pink_dark)
        d.line([P(*p) for p in pts] + [P(*pts[0])], fill=INK, width=w(7))
    d.ellipse([*P(-140, -125), *P(140, 165)], fill=pink, outline=INK, width=w(9))  # body
    d.ellipse([*P(-24, -200), *P(24, -148)], fill=(255, 215, 50), outline=INK, width=w(6))  # coin
    d.rounded_rectangle([*P(-48, -138), *P(48, -118)], w(8), fill=INK)  # coin slot
    for x0, x1 in ((-90, -12), (12, 90)):  # sunglasses
        d.rounded_rectangle([*P(x0, -80), *P(x1, -22)], w(20), fill=INK)
        d.line([P(x0 + 14, -68), P(x0 + 36, -68)], fill="white", width=w(6))
    d.line([P(-12, -62), P(12, -62)], fill=INK, width=w(8))
    d.ellipse([*P(-52, -8), *P(52, 58)], fill=snout, outline=INK, width=w(7))  # snout
    for nx in (-18, 18):
        d.ellipse([*P(nx - 7, 16), *P(nx + 7, 38)], fill=INK)
    if talking:
        open_h = 10 + 20 * abs(math.sin(t * 13))
        d.ellipse([*P(-26, 70), *P(26, 70 + open_h)], fill=DEEP_RED, outline=INK, width=w(6))
    else:
        d.arc([*P(-34, 55), *P(34, 100)], 20, 160, fill=INK, width=w(8))


# --- Lola Sulit: a sweet grandma holding a basket of finds --------------------------
def _lola_sulit(d, P, w, t, talking, font_fn):
    grey, dress, wood = (214, 214, 226), (180, 130, 225), (170, 110, 60)
    wave = math.sin(t * 9) * 38
    d.line([P(115, 40), P(195, -30 + wave)], fill=INK, width=w(18))  # waving arm (behind)
    d.line([P(115, 40), P(195, -30 + wave)], fill=SKIN, width=w(10))
    d.ellipse([*P(175, -50 + wave), *P(215, -10 + wave)], fill=SKIN, outline=INK, width=w(6))
    d.rounded_rectangle([*P(-120, -10), *P(120, 175)], w(40), fill=dress, outline=INK, width=w(9))  # dress
    for x, y in ((-80, 20), (-30, 45), (60, 15), (95, 55), (20, 5)):  # flower print
        d.ellipse([*P(x - 9, y - 9), *P(x + 9, y + 9)], fill=(255, 240, 130))
    d.ellipse([*P(-38, -245), *P(38, -170)], fill=grey, outline=INK, width=w(7))  # hair bun
    d.ellipse([*P(-85, -195), *P(85, -25)], fill=SKIN, outline=INK, width=w(9))  # head
    d.pieslice([*P(-88, -199), *P(88, -21)], 180, 360, fill=grey, outline=INK, width=w(7))  # grey hair
    _eyes(d, P, w, t, y=-78, dx=42, r=16)
    for ex in (-42, 42):  # glasses
        d.ellipse([*P(ex - 30, -108), *P(ex + 30, -48)], outline=INK, width=w(5))
    d.line([P(-12, -80), P(12, -80)], fill=INK, width=w(5))
    _cheeks(d, P, 66, -50, 16)
    _mouth(d, P, w, t, talking, y=-35, half=20)
    for x, y, col in ((-45, 88, (235, 60, 60)), (5, 78, (255, 165, 40)), (50, 90, (110, 200, 90))):  # finds
        d.ellipse([*P(x - 26, y - 26), *P(x + 26, y + 26)], fill=col, outline=INK, width=w(5))
    d.arc([*P(-85, 35), *P(85, 175)], 180, 360, fill=INK, width=w(8))  # basket handle
    d.rounded_rectangle([*P(-95, 110), *P(95, 185)], w(20), fill=wood, outline=INK, width=w(8))  # basket
    for x in (-50, 0, 50):
        d.line([P(x, 112), P(x, 183)], fill=(130, 80, 40), width=w(5))
    d.ellipse([*P(-150, 95), *P(-110, 135)], fill=SKIN, outline=INK, width=w(6))  # hand on basket
    d.line([P(-120, 40), P(-130, 105)], fill=INK, width=w(18))
    d.line([P(-120, 40), P(-130, 105)], fill=SKIN, width=w(10))


DRAWERS = {
    "Kayo": _kayo,
    "Mang Bili": _mang_bili,
    "Ate Deals": _ate_deals,
    "Boss Tipid": _boss_tipid,
    "Lola Sulit": _lola_sulit,
}


def draw(d, name, cx, cy, t, talking, s, font_fn):
    """Draw the mascot called `name` (falls back to Kayo) centred at (cx, cy), bouncing with time t."""
    cy += -abs(math.sin(t * math.pi * 2.2)) * 26 * s

    def P(x, y):
        return (cx + x * s, cy + y * s)

    def w(n):
        return max(1, int(n * s))

    DRAWERS.get(name, _kayo)(d, P, w, t, talking, font_fn)
