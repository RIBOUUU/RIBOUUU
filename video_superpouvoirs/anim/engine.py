"""Moteur de dessin : style vectoriel sombre (fond bleu-pétrole, bonhomme à tête noire, légendes grasses)."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, S, FPS = 1920, 1080, 2, 30
GY = 800                      # ligne du sol
FK = '/usr/share/fonts/opentype/inter/Inter-Black.otf'
FB = '/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf'
HOOD = (232, 108, 52); HOOD_D = (190, 80, 38)
YEL = (255, 206, 64); RED = (235, 70, 60); CYAN = (110, 220, 235); WHITE = (240, 240, 236)
BLK = (14, 14, 18); GREY = (205, 210, 214)
_fonts = {}


def font(size, black=True):
    k = (size, black)
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(FK if black else FB, max(6, int(size)))
    return _fonts[k]


def ease(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


def back(t, c=1.7):
    t = max(0.0, min(1.0, t)); return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


def lerp(a, b, t): return a + (b - a) * t


def mix(c1, c2, t): return tuple(int(lerp(a, b, max(0, min(1, t)))) for a, b in zip(c1, c2))


# ---------------------------------------------------------------- canvas
class C:
    """Toile en supersampling S, coordonnées logiques 1920x1080."""
    def __init__(self, base):
        self.im = base.copy(); self.d = ImageDraw.Draw(self.im)

    def p(self, pts): return [(x * S, y * S) for x, y in pts]

    def poly(self, pts, fill, outline=None, w=0):
        self.d.polygon(self.p(pts), fill=fill, outline=outline, width=int(w * S) if w else 0)

    def line(self, pts, col, w, cap=True):
        self.d.line(self.p(pts), fill=col, width=max(1, int(w * S)), joint='curve')
        if cap:
            for x, y in (pts[0], pts[-1]):
                r = w / 2; self.d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=col)

    def ell(self, cx, cy, rx, ry=None, fill=None, outline=None, w=0):
        ry = rx if ry is None else ry
        self.d.ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S], fill=fill, outline=outline,
                       width=int(w * S) if w else 0)

    def rect(self, x0, y0, x1, y1, fill=None, r=0, outline=None, w=0):
        if x1 < x0: x0, x1 = x1, x0
        if y1 < y0: y0, y1 = y1, y0
        if r:
            self.d.rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], radius=r * S, fill=fill, outline=outline,
                                     width=int(w * S) if w else 0)
        else:
            self.d.rectangle([x0 * S, y0 * S, x1 * S, y1 * S], fill=fill, outline=outline, width=int(w * S) if w else 0)

    def arc(self, cx, cy, r, a0, a1, col, w):
        self.d.arc([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], a0, a1, fill=col, width=int(w * S))

    def text(self, x, y, s, size, col=WHITE, anchor='mm', stroke=0, scol=BLK, black=True):
        self.d.text((x * S, y * S), s, font=font(size * S, black), fill=col, anchor=anchor,
                    stroke_width=int(stroke * S), stroke_fill=scol)

    def glow(self, cx, cy, rx, ry, col, a=1.0):
        """Halo doux (sprite pré-flouté)."""
        if a <= 0.01 or rx < 2 or ry < 2: return
        spr = _glow_sprite()
        w, h = int(rx * 2 * S), int(ry * 2 * S)
        if w < 2 or h < 2: return
        m = spr.resize((w, h), Image.BILINEAR)
        if a < 1: m = m.point(lambda v: int(v * a))
        self.im.paste(col, (int((cx - rx) * S), int((cy - ry) * S)), m)
        self.d = ImageDraw.Draw(self.im)


_GS = None


def _glow_sprite():
    global _GS
    if _GS is None:
        n = 256; y, x = np.mgrid[0:n, 0:n]; r = np.sqrt((x - n / 2) ** 2 + (y - n / 2) ** 2) / (n / 2)
        _GS = Image.fromarray((np.clip(1 - r, 0, 1) ** 2 * 255).astype(np.uint8), 'L')
    return _GS


# ---------------------------------------------------------------- backgrounds (cache)
_bg = {}


def _grad(top, bot, y0=0, y1=H, im=None):
    if im is None: im = Image.new('RGB', (W * S, H * S), bot)
    d = ImageDraw.Draw(im)
    for y in range(y0, y1):
        k = (y - y0) / max(1, (y1 - y0)); d.line([(0, y * S), (W * S, y * S)], fill=mix(top, bot, k), width=S)
    return im


def _streaks(im, n=8, col=(90, 150, 170), seed=1, ymax=GY):
    for k in range(n):
        r = random.Random(seed * 100 + k); x = r.uniform(0, W); w = r.uniform(30, 90)
        ov = Image.new('L', (W * S, H * S), 0); ImageDraw.Draw(ov).rectangle([x * S, 0, (x + w) * S, ymax * S], fill=16)
        im.paste(col, (0, 0), ov.filter(ImageFilter.GaussianBlur(40 * S)))


def _floor(im, top=(72, 50, 40), bot=(36, 26, 22)):
    _grad(top, bot, GY, H, im)
    ImageDraw.Draw(im).rectangle([0, GY * S, W * S, (GY + 5) * S], fill=(92, 66, 52))


def _buildings(im, spots, seed=3):
    d = ImageDraw.Draw(im)
    for i, (bx, bw, bh) in enumerate(spots):
        col = (38, 78, 98) if i % 2 else (44, 88, 110)
        d.rounded_rectangle([bx * S, (GY - bh) * S, (bx + bw) * S, GY * S], radius=10 * S, fill=col)
        d.rectangle([bx * S, (GY - bh) * S, (bx + bw) * S, (GY - bh + 14) * S], fill=(56, 104, 128))
        for wy in range(GY - bh + 40, GY - 40, 60):
            for wx in range(bx + 22, bx + bw - 30, 48):
                lit = random.Random(wx * 7 + wy + seed).random() < 0.45
                d.rounded_rectangle([wx * S, wy * S, (wx + 24) * S, (wy + 34) * S], radius=4 * S,
                                    fill=(255, 214, 120) if lit else (30, 60, 76))


def _stars(im, n=160, seed=5, ymax=H):
    d = ImageDraw.Draw(im)
    for k in range(n):
        r = random.Random(seed * 1000 + k); x = r.uniform(0, W); y = r.uniform(0, ymax); s = r.uniform(1, 3.2)
        c = int(r.uniform(140, 255)); d.ellipse([(x - s) * S, (y - s) * S, (x + s) * S, (y + s) * S], fill=(c, c, min(255, c + 20)))


def bg(name):
    if name in _bg: return _bg[name]
    if name == 'plain':
        im = _grad((22, 58, 76), (36, 80, 94), 0, GY); _streaks(im); _floor(im)
    elif name == 'city':
        im = _grad((22, 58, 76), (36, 80, 94), 0, GY); _streaks(im)
        _buildings(im, [(30, 200, 420), (250, 150, 300), (1460, 220, 470), (1700, 180, 330)]); _floor(im)
    elif name == 'citywide':  # immeubles bas, pour le géant
        im = _grad((22, 58, 76), (36, 80, 94), 0, GY); _streaks(im)
        _buildings(im, [(20, 170, 240), (210, 130, 170), (380, 150, 210), (1300, 160, 220), (1480, 140, 170), (1650, 200, 250)]); _floor(im)
    elif name == 'room':
        im = _grad((26, 46, 64), (34, 60, 76), 0, GY); _floor(im, (66, 46, 38), (34, 24, 20))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([1300 * S, 180 * S, 1640 * S, 470 * S], radius=10 * S, fill=(18, 30, 44), outline=(70, 96, 112), width=8 * S)
        d.line([(1470 * S, 180 * S), (1470 * S, 470 * S)], fill=(70, 96, 112), width=6 * S)
        _stars(im, 25, 9, 0) if False else None
        for k in range(18):
            r = random.Random(k); x = r.uniform(1310, 1630); y = r.uniform(190, 460)
            d.ellipse([(x - 2) * S, (y - 2) * S, (x + 2) * S, (y + 2) * S], fill=(200, 210, 230))
        d.rounded_rectangle([220 * S, 640 * S, 760 * S, 720 * S], radius=16 * S, fill=(70, 96, 140))   # lit
        d.rounded_rectangle([200 * S, 700 * S, 780 * S, 800 * S], radius=12 * S, fill=(52, 70, 104))
        d.rounded_rectangle([230 * S, 610 * S, 380 * S, 660 * S], radius=20 * S, fill=(220, 226, 232))
    elif name == 'sky':
        im = _grad((40, 96, 140), (110, 170, 200), 0, H)
        d = ImageDraw.Draw(im)
        for cx, cy, sc in [(260, 260, 1.2), (900, 160, 0.9), (1500, 300, 1.3), (500, 820, 1.6), (1300, 900, 1.8)]:
            for dx, dy, r in [(0, 0, 60), (70, -25, 75), (150, 0, 60), (70, 25, 55)]:
                d.ellipse([(cx + dx * sc - r * sc) * S, (cy + dy * sc - r * sc) * S, (cx + dx * sc + r * sc) * S,
                           (cy + dy * sc + r * sc) * S], fill=(225, 236, 242))
    elif name == 'highsky':
        im = _grad((10, 18, 40), (46, 96, 150), 0, H); _stars(im, 90, 7, 500)
        d = ImageDraw.Draw(im)
        d.ellipse([-600 * S, 820 * S, (W + 600) * S, 2200 * S], fill=(60, 120, 170))
        d.ellipse([-600 * S, 840 * S, (W + 600) * S, 2200 * S], fill=(44, 96, 140))
    elif name == 'space':
        im = _grad((6, 10, 22), (14, 22, 44), 0, H); _stars(im, 260, 11)
    elif name == 'track':
        im = _grad((22, 50, 70), (32, 70, 90), 0, GY); _streaks(im, 5)
        d = ImageDraw.Draw(im)
        for k in range(14):  # tribunes
            d.rectangle([0, (420 + k * 26) * S, W * S, (432 + k * 26) * S], fill=(30 + k, 62 + k, 80 + k))
        _grad((170, 70, 54), (120, 46, 38), GY, H, im)
        for y in (860, 940, 1030):
            d.line([(0, y * S), (W * S, y * S)], fill=(230, 220, 210), width=4 * S)
    elif name == 'desert':
        im = _grad((40, 90, 120), (210, 170, 120), 0, GY)
        _grad((190, 150, 100), (140, 104, 70), GY, H, im)
        d = ImageDraw.Draw(im)
        for x0, w, h in [(0, 600, 120), (500, 700, 80), (1300, 700, 140)]:
            d.ellipse([x0 * S, (GY - h) * S, (x0 + w) * S, (GY + h) * S], fill=(170, 134, 96))
        d.rectangle([0, (GY + 40) * S, W * S, (GY + 52) * S], fill=(90, 90, 100))   # rails
        d.rectangle([0, (GY + 70) * S, W * S, (GY + 82) * S], fill=(90, 90, 100))
    elif name == 'lab':
        im = _grad((16, 30, 44), (26, 46, 62), 0, GY); _floor(im, (40, 52, 62), (22, 28, 34))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([200 * S, 600 * S, 1720 * S, 650 * S], radius=10 * S, fill=(70, 86, 100))
        for x in range(260, 1700, 90):
            d.ellipse([(x - 6) * S, 612 * S, (x + 6) * S, 624 * S], fill=(110, 130, 150))
    elif name == 'ocean':
        im = _grad((10, 60, 100), (4, 20, 44), 0, H)
        ov = Image.new('L', (W * S, H * S), 0); od = ImageDraw.Draw(ov)
        for k in range(7):
            x = 200 + k * 260; od.polygon([(x * S, 0), ((x + 80) * S, 0), ((x + 260) * S, H * S), ((x + 120) * S, H * S)], fill=26)
        im.paste((120, 200, 230), (0, 0), ov.filter(ImageFilter.GaussianBlur(30 * S)))
    elif name == 'mountain':
        im = _grad((20, 44, 74), (90, 140, 180), 0, H)
        d = ImageDraw.Draw(im)
        d.polygon([(0, H * S), (520 * S, 380 * S), (760 * S, 520 * S), (960 * S, 240 * S), (1260 * S, 600 * S),
                   (1500 * S, 420 * S), (W * S, H * S)], fill=(70, 92, 118))
        d.polygon([(860 * S, 360 * S), (960 * S, 240 * S), (1060 * S, 360 * S), (1010 * S, 340 * S), (960 * S, 370 * S),
                   (910 * S, 340 * S)], fill=(236, 242, 248))
        d.polygon([(450 * S, 460 * S), (520 * S, 380 * S), (600 * S, 450 * S), (520 * S, 440 * S)], fill=(230, 238, 246))
    elif name == 'map':
        im = _grad((14, 40, 60), (20, 54, 76), 0, H)
    elif name == 'hospital':
        im = _grad((20, 44, 56), (30, 64, 76), 0, GY); _floor(im, (56, 70, 78), (30, 38, 44))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 520 * S, W * S, 540 * S], fill=(46, 86, 100))
    elif name == 'station':
        im = _grad((22, 50, 66), (34, 72, 86), 0, GY); _floor(im, (80, 80, 86), (40, 40, 46))
        d = ImageDraw.Draw(im)
        for x in range(0, W, 320):
            d.rectangle([(x + 40) * S, 120 * S, (x + 70) * S, GY * S], fill=(30, 62, 78))
        d.rectangle([0, 100 * S, W * S, 130 * S], fill=(40, 76, 92))
    else:
        raise KeyError(name)
    _bg[name] = im
    return im


# ---------------------------------------------------------------- personnage
ARM = {  # angles (épaule, coude) en degrés depuis le bas, vers l'extérieur
    'down': (12, 6), 'up': (165, 175), 'shrug': (70, 150), 'point': (95, 92), 'hip': (40, -50), 'hold': (40, 100),
    'wave': (140, 190), 'cover': (60, 170), 'run_f': (60, 110), 'run_b': (-40, -10), 'fly': (175, 180),
    'cross': (40, 150), 'think': (35, 150), 'tense': (55, 30), 'flail': (130, 60),
}


def character(c, x, gy, s=1.0, pose=None, t=0.0):
    """Dessine le personnage. pose: dict(arms=(l,r), legs='stand'|'run'|'sit'|'fly'|'kneel', knee=0..1,
    mood, blink, rot (rad), col (hoodie), tremble, phase, flip, shadow, eyes_red, mask)."""
    P = pose or {}
    rot = P.get('rot', 0.0); col = P.get('col', HOOD); dcol = tuple(int(v * 0.8) for v in col)
    trem = P.get('tremble', 0) * math.sin(t * 90)
    legs = P.get('legs', 'stand'); knee = P.get('knee', 0.0); ph = P.get('phase', 0.0)
    hip = 150 * (1 - 0.5 * knee) if legs != 'sit' else 70
    pivot = hip + 60
    cr, sr = math.cos(rot), math.sin(rot)
    flip = P.get('flip', 1)

    def L(px, py):
        px *= flip
        dx, dy = px, py - pivot
        rx, ry = dx * cr - dy * sr, dx * sr + dy * cr
        return (x + (rx + trem * (py / 300)) * s, gy - (ry + pivot) * s)

    if P.get('shadow', True) and legs not in ('fly',):
        c.ell(x, gy + 4, 110 * s, 13 * s, fill=(28, 20, 16) if gy >= GY - 5 else (20, 30, 40))
    # jambes
    if legs == 'run':
        for k, sgn in ((0, 1), (1, -1)):
            a = math.sin(ph + k * math.pi)
            hipp = L(sgn * 6, hip); kn = L(sgn * 6 + 46 * a, hip * 0.55 + 10 * abs(a))
            ft = L(sgn * 6 + 40 * a - 30 * max(0, -a), 14 + 30 * max(0, a))
            c.line([ft, kn, hipp], BLK, 11 * s)
            c.rect(ft[0] - 20 * s, ft[1] - 10 * s, ft[0] + 24 * s, ft[1] + 8 * s, fill=(50, 50, 58), r=7 * s)
    elif legs == 'fly':
        for sgn in (-1, 1):
            c.line([L(sgn * 14, hip), L(sgn * 18, hip * 0.5), L(sgn * 20, 20)], BLK, 11 * s)
            f = L(sgn * 22, 8); c.ell(f[0], f[1], 18 * s, 10 * s, fill=(50, 50, 58))
    elif legs == 'sit':
        for sgn in (-1, 1):
            c.line([L(sgn * 14, hip), L(sgn * 60, hip - 4), L(sgn * 66, 12)], BLK, 11 * s)
            f = L(sgn * 70, 6); c.rect(f[0] - 22 * s, f[1] - 10 * s, f[0] + 22 * s, f[1] + 8 * s, fill=(50, 50, 58), r=7 * s)
    else:  # stand / kneel
        kx = 14 + 40 * knee
        for sgn in (-1, 1):
            c.line([L(sgn * 20, 10), L(sgn * kx, hip * 0.5), L(sgn * 12, hip)], BLK, 11 * s)
            f = L(sgn * 26, 6)
            c.rect(f[0] - 24 * s, f[1] - 12 * s, f[0] + 22 * s, f[1] + 8 * s, fill=(50, 50, 58), r=8 * s)
            c.rect(f[0] - 24 * s, f[1] + 2 * s, f[0] + 22 * s, f[1] + 8 * s, fill=(220, 220, 225))
    # torse (sweat)
    top = hip + 150
    c.poly([L(-46, top), L(46, top), L(52, hip + 8), L(-52, hip + 8)], col)
    c.poly([L(-52, hip + 22), L(52, hip + 22), L(52, hip - 2), L(-52, hip - 2)], dcol)
    c.poly([L(-28, hip + 70), L(28, hip + 70), L(28, hip + 36), L(-28, hip + 36)], dcol)
    for sgn in (-1, 1):
        c.line([L(sgn * 12, top - 4), L(sgn * 14, top - 58)], (245, 240, 230), 4 * s)
    hc = L(0, top); c.ell(hc[0], hc[1], 50 * s, 24 * s, fill=dcol)
    if P.get('glowchest'):
        gc = L(0, top - 50); c.glow(gc[0], gc[1], 120 * s, 120 * s, P['glowchest'], 0.9)
    # bras
    arms = P.get('arms', ('down', 'down'))
    hands = []
    for side, a in zip((-1, 1), arms):
        a1, a2 = ARM[a] if isinstance(a, str) else a
        sh = (side * 44, top - 12)
        r1, r2 = 62, 62
        e = (sh[0] + side * flip * 0 + side * r1 * math.sin(math.radians(a1)), sh[1] - r1 * math.cos(math.radians(a1)))
        hnd = (e[0] + side * r2 * math.sin(math.radians(a2)), e[1] - r2 * math.cos(math.radians(a2)))
        c.line([L(*sh), L(*e), L(*hnd)], col, 24 * s)
        hp = L(*hnd); c.ell(hp[0], hp[1], 12 * s, fill=BLK); hands.append(hp)
    # cou + tête
    n = L(0, top + 6); c.ell(n[0], n[1] - 6 * s, 9 * s, 12 * s, fill=BLK)
    hx, hy = L(0, top + 68); r = 62 * s
    c.ell(hx, hy, r, fill=BLK)
    hair = P.get('hair', (120, 40, 36))
    c.d.chord([(hx - r * 0.95) * S, (hy - r * 1.08) * S, (hx + r * 0.95) * S, (hy - r * 0.2) * S], 190, 350, fill=hair)
    c.ell(hx + r * 0.45 * flip, hy - r * 0.93, r * 0.3, r * 0.22, fill=hair)
    face(c, hx, hy, s, P.get('mood', 'happy'), P.get('blink', False), P.get('look', (3, 2)), P.get('eyes_red', False))
    if P.get('mask'):
        c.rect(hx - 30 * s, hy + 14 * s, hx + 30 * s, hy + 50 * s, fill=(250, 210, 60), r=12 * s)
    return dict(head=(hx, hy, r), hands=hands, chest=L(0, top - 50), hip=L(0, hip), knees=(L(-30, hip * 0.5), L(30, hip * 0.5)))


def face(c, hx, hy, s, mood, blink=False, look=(3, 2), red=False):
    w = 5 * s
    for sx in (-1, 1):
        ex, ey = hx + sx * 24 * s, hy - 2 * s
        er = (22 if mood in ('shock', 'scared') else 17) * s
        if mood in ('hurt', 'ko'):
            k = 11 * s
            c.d.line([(ex - k) * S, (ey - k) * S, (ex + k) * S, (ey + k) * S], fill='white', width=int(w * S))
            c.d.line([(ex - k) * S, (ey + k) * S, (ex + k) * S, (ey - k) * S], fill='white', width=int(w * S))
            continue
        if blink or mood in ('sleep', 'calm'):
            c.arc(ex, ey - 4 * s, 13 * s, 20, 160, WHITE, 5 * s); continue
        if mood == 'happy2':
            c.arc(ex, ey + 6 * s, 14 * s, 200, 340, WHITE, 6 * s); continue
        c.ell(ex, ey, er, fill=(255, 220, 220) if red else 'white')
        if red:
            for k in range(3):
                c.d.line([(ex - er * 0.8) * S, (ey + (k - 1) * 6 * s) * S, (ex - er * 0.2) * S, (ey + (k - 1) * 3 * s) * S], fill=RED, width=max(1, int(2 * s * S)))
        pr = (8 if mood not in ('shock', 'scared') else 6) * s
        c.ell(ex + look[0] * s, ey + look[1] * s, pr, fill=BLK)
        c.ell(ex + look[0] * s + 3 * s, ey + look[1] * s - 3 * s, 2.5 * s, fill='white')
        if mood in ('worry', 'shock', 'scared', 'cold'):
            c.d.line([(ex - 16 * s) * S, (ey - er - 8 * s + sx * -6 * s) * S, (ex + 16 * s) * S, (ey - er - 8 * s + sx * 6 * s) * S], fill='white', width=int(w * S))
        if mood in ('angry', 'determined'):
            c.d.line([(ex - 16 * s) * S, (ey - er - 10 * s + sx * 6 * s) * S, (ex + 16 * s) * S, (ey - er - 10 * s - sx * 6 * s) * S], fill='white', width=int(w * S))
    my = hy + 30 * s
    if mood in ('happy', 'happy2', 'calm'):
        c.arc(hx, my - 8 * s, 14 * s, 20, 160, WHITE, 5 * s)
    elif mood in ('worry', 'cold'):
        c.arc(hx, my + 10 * s, 12 * s, 200, 340, WHITE, 5 * s)
    elif mood in ('shock', 'scared'):
        c.ell(hx, my + 4 * s, 8 * s, 10 * s, outline=WHITE, w=4 * s)
    elif mood in ('hurt', 'ko'):
        pts = [(hx - 16 * s + i * 6 * s, my + (4 * s if i % 2 else -2 * s)) for i in range(6)]
        c.d.line(c.p(pts), fill=WHITE, width=int(4 * s * S))
    elif mood == 'determined':
        c.d.line([(hx - 12 * s) * S, (my + 2 * s) * S, (hx + 12 * s) * S, (my + 2 * s) * S], fill=WHITE, width=int(5 * s * S))
    elif mood == 'sleep':
        c.d.line([(hx - 8 * s) * S, (my + 2 * s) * S, (hx + 8 * s) * S, (my + 2 * s) * S], fill=WHITE, width=int(4 * s * S))
    else:
        c.d.line([(hx - 10 * s) * S, (my) * S, (hx + 10 * s) * S, (my) * S], fill=WHITE, width=int(4 * s * S))


# ---------------------------------------------------------------- éléments graphiques
def bubble(c, txt, x, y, p, size=46, tail=-1):
    if p <= 0.02: return
    sz = size * min(1.0, p)
    tw = c.d.textlength(txt, font=font(sz * S)) / S
    c.rect(x - tw / 2 - 30, y - sz * 0.9, x + tw / 2 + 30, y + sz * 0.9, fill=(232, 234, 236), r=sz * 0.9)
    c.poly([(x + tail * 20, y + sz * 0.8), (x + tail * 60, y + sz * 0.8), (x + tail * 10, y + sz * 1.7)], (232, 234, 236))
    c.text(x, y, txt, sz, (55, 60, 66))


def tag(c, txt, x, y, p=1.0, size=44, col=YEL, bg=(16, 22, 30), tcol=None):
    """Étiquette arrondie (chiffre clé)."""
    if p <= 0.02: return
    sz = size * min(1.15, p)
    tw = c.d.textlength(txt, font=font(sz * S)) / S
    c.rect(x - tw / 2 - 26, y - sz * 0.85, x + tw / 2 + 26, y + sz * 0.85, fill=bg, r=sz * 0.5, outline=col, w=4)
    c.text(x, y, txt, sz, tcol or col)


def stopwatch(c, x, y, r, frac, col=RED, label=None):
    c.glow(x, y, r * 1.8, r * 1.8, col, 0.5)
    c.rect(x - r * 0.18, y - r * 1.28, x + r * 0.18, y - r * 1.05, fill=GREY, r=4)
    c.ell(x, y, r * 1.06, fill=GREY); c.ell(x, y, r * 0.92, fill=(24, 30, 40))
    c.d.pieslice([(x - r * 0.85) * S, (y - r * 0.85) * S, (x + r * 0.85) * S, (y + r * 0.85) * S], -90, -90 + 360 * frac, fill=col)
    c.ell(x, y, r * 0.55, fill=(24, 30, 40))
    if label: c.text(x, y, label, r * 0.5, WHITE)


def gauge(c, x, y, r, v, label, ok=True):
    col = (80, 210, 120) if ok else RED
    c.ell(x, y, r, fill=(20, 28, 38), outline=GREY, w=5)
    c.arc(x, y, r * 0.78, 150, 390, (60, 70, 80), 12)
    c.arc(x, y, r * 0.78, 150, 150 + 240 * v, col, 12)
    a = math.radians(150 + 240 * v)
    c.line([(x, y), (x + math.cos(a) * r * 0.62, y + math.sin(a) * r * 0.62)], WHITE, 6)
    c.ell(x, y, 9, fill=WHITE)
    c.text(x, y + r + 34, label, 30, WHITE, black=False)


def heart(c, x, y, r, beat=1.0, col=(230, 60, 70)):
    r *= beat
    c.ell(x - r * 0.48, y - r * 0.2, r * 0.55, fill=col); c.ell(x + r * 0.48, y - r * 0.2, r * 0.55, fill=col)
    c.poly([(x - r * 1.0, y - r * 0.05), (x + r * 1.0, y - r * 0.05), (x, y + r * 1.05)], col)
    c.ell(x - r * 0.55, y - r * 0.4, r * 0.16, fill=(255, 150, 150))


def bolt(c, x0, y0, x1, y1, seed, col=(170, 230, 255), w=6, seg=8, amp=40):
    r = random.Random(seed); pts = [(x0, y0)]
    for k in range(1, seg):
        t = k / seg; pts.append((lerp(x0, x1, t) + r.uniform(-amp, amp), lerp(y0, y1, t) + r.uniform(-amp, amp)))
    pts.append((x1, y1))
    c.glow((x0 + x1) / 2, (y0 + y1) / 2, abs(x1 - x0) / 2 + 60, abs(y1 - y0) / 2 + 60, col, 0.35)
    c.line(pts, col, w * 2.2, cap=False); c.line(pts, (255, 255, 255), w * 0.8, cap=False)


def thermometer(c, x, y, h, v, label=None):
    c.rect(x - 18, y - h, x + 18, y, fill=(230, 234, 238), r=18)
    c.ell(x, y + 10, 32, fill=(230, 234, 238))
    col = mix((90, 170, 255), RED, v)
    c.rect(x - 9, y - 10 - (h - 30) * v, x + 9, y, fill=col, r=9); c.ell(x, y + 10, 23, fill=col)
    if label: c.text(x, y - h - 40, label, 40, col)


def globe(c, x, y, r, spin, night=False):
    c.glow(x, y, r * 1.3, r * 1.3, (80, 160, 255), 0.5)
    c.ell(x, y, r, fill=(30, 90, 170))
    rnd = random.Random(4)
    for k in range(9):
        lon = rnd.uniform(0, 2 * math.pi); lat = rnd.uniform(-1.1, 1.1); sz = rnd.uniform(0.18, 0.4)
        a = lon + spin; cx = math.sin(a) * math.cos(lat); vis = math.cos(a)
        if vis <= 0.05: continue
        px = x + cx * r; py = y - math.sin(lat) * r
        c.ell(px, py, r * sz * vis, r * sz * 0.8, fill=(70, 170, 100))
    c.ell(x, y, r, outline=(140, 200, 255), w=4)
    if night:
        c.d.pieslice([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], 90, 270, fill=None)


def eiffel(c, x, gy, h, col=(26, 40, 52)):
    w = h * 0.36
    c.poly([(x - w, gy), (x - w * 0.28, gy - h * 0.45), (x - w * 0.12, gy - h * 0.92), (x, gy - h), (x + w * 0.12, gy - h * 0.92),
            (x + w * 0.28, gy - h * 0.45), (x + w, gy), (x + w * 0.55, gy), (x, gy - h * 0.2), (x - w * 0.55, gy)], col)
    c.rect(x - w * 0.62, gy - h * 0.3, x + w * 0.62, gy - h * 0.26, fill=col)
    c.rect(x - w * 0.35, gy - h * 0.58, x + w * 0.35, gy - h * 0.55, fill=col)


def particles(c, x, y, n, t, seed, col=(160, 240, 255), spread=200, rise=200, size=6):
    for k in range(n):
        r = random.Random(seed * 77 + k); ph = (t * r.uniform(0.3, 0.8) + r.random()) % 1
        px = x + r.uniform(-spread, spread); py = y - ph * rise
        a = math.sin(ph * math.pi); c.ell(px, py, size * a + 1, fill=mix((30, 50, 60), col, a))


def dust(c, x, gy, p, n=12, spread=480, col=(96, 74, 60)):
    for k in range(n):
        r = random.Random(k); side = -1 if k % 2 else 1; dist = p * r.uniform(spread * 0.3, spread)
        px = x + side * dist; py = gy - 8 - p * r.uniform(10, 70); rad = (1 - p * 0.5) * r.uniform(25, 55)
        c.ell(px, py, rad, fill=col)


def speedlines(c, t, n=16, col=(160, 210, 230), y0=150, y1=760, dirx=-1):
    for k in range(n):
        r = random.Random(k * 3); y = r.uniform(y0, y1); ln = r.uniform(150, 420)
        x = (r.uniform(0, W) - dirx * t * 2600 * r.uniform(0.6, 1.2)) % (W + ln) - ln * 0.5
        c.line([(x, y), (x + ln, y)], mix((30, 60, 80), col, 0.6), 5, cap=True)


# ---------------------------------------------------------------- titre de section
def title_card(c, num, txt, t, icon=None):
    p = back(t / 0.5)
    c.glow(W / 2, 430, 520, 320, CYAN, 0.35)
    if num:
        c.text(W / 2, 330, num, 190 * min(1.1, p), YEL, stroke=8)
    c.text(W / 2, 520, txt, 96 * min(1.05, back((t - 0.25) / 0.5)), WHITE, stroke=7)
    if t > 0.5:
        w = 260 * ease((t - 0.5) / 0.4); c.rect(W / 2 - w, 600, W / 2 + w, 612, fill=RED, r=6)


# ---------------------------------------------------------------- finition image
_vig = None
_grain = None


def finish(im_s, zoom=1.0, dark=0.0):
    """Recadrage léger (zoom), réduction, vignettage + grain fixe, fondu au noir éventuel."""
    global _vig, _grain
    if zoom > 1.001:
        cw, ch = W * S / zoom, H * S / zoom; x0 = (W * S - cw) / 2; y0 = (H * S - ch) / 2
        im = im_s.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))
    else:
        im = im_s.resize((W, H), Image.LANCZOS)
    if _vig is None:
        yy, xx = np.mgrid[0:H, 0:W]
        v = 1 - 0.5 * (((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H * 0.45) / (H * 0.78)) ** 2)
        _vig = np.clip(v, 0.4, 1)[..., None].astype(np.float32)
        _grain = np.random.default_rng(0).normal(0, 3.2, (H, W, 1)).astype(np.float32)
    a = np.asarray(im).astype(np.float32) * _vig + _grain
    if dark > 0: a *= (1 - dark)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


# ---------------------------------------------------------------- légendes
NUMW = {'un', 'deux', 'trois', 'quatre', 'cinq', 'six', 'sept', 'huit', 'neuf', 'dix', 'onze', 'cent', 'cents', 'mille',
        'dix-sept', 'dix-neuf', 'trente', 'trente-huit', 'trente-sept', 'trente-quatre', 'quarante-cinq', 'quarante-six',
        'cinquante-huit', 'cinquante-quatre', 'soixante', 'soixante-dix', 'soixante-dix-huit', 'quatre-vingts', 'vingt-deux',
        'quinze', 'dix-neuf,'}


def caption(c1, chunk, t, y=965, size=74):
    """chunk: list of (WORD, start, yellow). c1: ImageDraw at 1x."""
    d = c1
    fs = font(size)
    words = [w for w, _, _ in chunk]
    ws = [d.textlength(w, font=fs) for w in words]
    gap = 22; tot = sum(ws) + gap * (len(ws) - 1)
    scale = 1.0
    if tot > W - 140: scale = (W - 140) / tot; ws = [v * scale for v in ws]; tot = (W - 140)
    x = W / 2 - tot / 2
    for (w, st, yel), wl in zip(chunk, ws):
        p = back((t - st + 0.05) / 0.16)
        if p > 0.02:
            f2 = font(size * scale * (0.6 + 0.4 * min(p, 1.15)))
            d.text((x + wl / 2, y), w, font=f2, fill=YEL if yel else (245, 245, 240), anchor='mm', stroke_width=7,
                   stroke_fill=(10, 12, 16))
        x += wl + gap
