"""Short vertical « La daronne vs le daron » — style vectoriel sombre (moteur de la vidéo longue)."""
import sys, os, math, random, subprocess
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'video_superpouvoirs', 'anim'))
import engine as E
E.W, E.H = 1080, 1920
from engine import C, character, face, bubble, tag, ease, back, lerp, mix, font, HOOD, YEL, RED, CYAN, WHITE, BLK, GREY
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

W, H, S, FPS = 1080, 1920, E.S, 30
FLOOR = 1760
DUR = 67.6
N = int(DUR * FPS)

SON = dict(col=HOOD)
MOM = dict(col=(214, 76, 98), outfit='dress', longhair=True, earrings=True, hair=(74, 42, 32))
DAD = dict(col=(48, 96, 160), outfit='shirt', flathair=True, mustache=True, hair=(24, 24, 28))

# ------------------------------------------------------------ fonds verticaux
_bg = {}
PAL = {'teal': ((20, 56, 72), (34, 80, 94), (44, 98, 112)), 'navy': ((14, 20, 44), (24, 34, 66), (34, 46, 84)),
       'purple': ((34, 26, 60), (52, 40, 88), (66, 52, 108)), 'green': ((18, 56, 50), (30, 84, 72), (40, 104, 88)),
       'amber': ((64, 40, 20), (96, 62, 28), (120, 80, 36)), 'rose': ((62, 26, 42), (92, 40, 62), (112, 54, 78)),
       'red': ((70, 16, 22), (110, 26, 32), (140, 38, 42))}


def vbg(name, floor=False, burst=False):
    k = (name, floor, burst)
    if k in _bg: return _bg[k]
    top, bot, circ = PAL[name]
    im = E._grad(top, bot, 0, H, Image.new('RGB', (W * S, H * S), bot))
    d = ImageDraw.Draw(im)
    if burst:
        for i in range(24):
            if i % 2: continue
            a0, a1 = i * 15, (i + 1) * 15
            d.pieslice([(W / 2 - 2200) * S, (900 - 2200) * S, (W / 2 + 2200) * S, (900 + 2200) * S], a0, a1, fill=circ)
    else:
        for cx, cy, r in [(980, 260, 330), (90, 1180, 260), (900, 1650, 420), (200, 520, 120)]:
            d.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], fill=circ)
    if name == 'navy':
        for i in range(70):
            r = random.Random(i); x = r.uniform(0, W); y = r.uniform(0, 1300); s = r.uniform(1, 3)
            d.ellipse([(x - s) * S, (y - s) * S, (x + s) * S, (y + s) * S], fill=(190, 200, 230))
    if floor:
        E._grad((70, 50, 40), (34, 24, 20), FLOOR, H, im)
        ImageDraw.Draw(im).rectangle([0, FLOOR * S, W * S, (FLOOR + 5) * S], fill=(92, 66, 52))
    _bg[k] = im
    return im


# ------------------------------------------------------------ helpers
def who(c, x, y, label, col):
    c.rect(x - 90, y - 30, x + 90, y + 30, fill=col, r=30)
    c.text(x, y, label, 34, WHITE)


def big(c, txt, y, t, col=WHITE, size=110):
    p = back(t / 0.3)
    if p <= 0.02: return
    c.text(W / 2, y, txt, size * min(1.08, p), col, stroke=9)


def closeup(c, T, P, mood, **kw):
    pose = dict(P); pose.update(mood=mood, blink=(T % 3.1) < 0.08); pose.update(kw)
    return character(c, W / 2, 2210, 2.9, pose, T)


def two(c, T, left, right, lm='happy', rm='happy', lkw=None, rkw=None, labels=True):
    a = dict(left); a.update(mood=lm, look=(5, 2), blink=(T % 3.4) < 0.08); a.update(lkw or {})
    b = dict(right); b.update(mood=rm, look=(-5, 2), blink=(T % 2.9) < 0.08); b.update(rkw or {})
    ia = character(c, 280, FLOOR, 2.0, a, T)
    ib = character(c, 800, FLOOR, 1.95, b, T)
    if labels:
        y = ia['head'][1] - 190
        if left is MOM: who(c, 280, y, 'DARONNE', (200, 60, 90))
        if left is DAD: who(c, 280, y, 'DARON', (40, 90, 170))
    return ia, ib


def phone(c, x, y, k, name, sub, col, bad=True, ok=False, T=0):
    w, h = 420 * k, 640 * k
    c.rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, fill=(16, 20, 30), r=50 * k, outline=(70, 80, 96), w=6)
    c.ell(x, y - h * 0.25, 70 * k, fill=col); c.text(x, y - h * 0.25, name[0], 70 * k, WHITE)
    c.text(x, y - h * 0.05, name, 50 * k, WHITE); c.text(x, y + h * 0.05, sub, 30 * k, (170, 180, 190), black=False)
    if bad:
        bx, by = x - (80 * k if ok else 0), y + h * 0.3
        c.ell(bx, by, 46 * k, fill=RED)
        c.line([(bx - 18 * k, by - 18 * k), (bx + 18 * k, by + 18 * k)], WHITE, 9 * k); c.line([(bx - 18 * k, by + 18 * k), (bx + 18 * k, by - 18 * k)], WHITE, 9 * k)
    if ok:
        g = 1 + 0.08 * math.sin(T * 10)
        c.ell(x + 80 * k, y + h * 0.3, 46 * k * g, fill=(60, 190, 100)); c.text(x + 80 * k, y + h * 0.3, '✓', 50 * k, WHITE)


def trash(c, x, y, k=1.0):
    c.ell(x, y, 70 * k, 80 * k, fill=(40, 90, 60))
    c.poly([(x - 30 * k, y - 70 * k), (x, y - 120 * k), (x + 30 * k, y - 70 * k)], (40, 90, 60))
    c.ell(x - 20 * k, y - 20 * k, 14 * k, 22 * k, fill=(70, 130, 90))


def chat(c, msgs, T):
    c.rect(200, 300, 880, 1250, fill=(232, 236, 240), r=50)
    c.rect(220, 320, 860, 1230, fill=(246, 248, 250), r=40)
    c.rect(470, 340, 610, 352, fill=(60, 60, 70), r=6)
    c.text(540, 420, 'Daronne ❤'.replace(' ❤', ''), 44, (40, 44, 52))
    y = 520
    for t0, txt, mine in msgs:
        p = back((T - t0) / 0.25)
        if p <= 0.02: continue
        f = font(40 * S); tw = c.d.textlength(txt, font=f) / S
        if mine:
            c.rect(840 - tw - 50, y - 40, 840, y + 40, fill=(70, 120, 230), r=36); c.text(840 - tw / 2 - 25, y, txt, 40 * min(1, p), WHITE)
        else:
            c.rect(250, y - 40, 250 + tw + 50, y + 40, fill=(220, 224, 230), r=36); c.text(250 + tw / 2 + 25, y, txt, 40 * min(1, p), (40, 44, 52))
        y += 120


def rain(c, T):
    c.ell(400, 520, 140, 90, fill=(90, 100, 120)); c.ell(560, 480, 170, 120, fill=(100, 110, 130)); c.ell(720, 530, 130, 85, fill=(90, 100, 120))
    for k in range(18):
        r = random.Random(k); x = r.uniform(320, 780); y = 620 + ((T * 900 + r.uniform(0, 400)) % 400)
        c.line([(x, y), (x - 6, y + 34)], (140, 190, 255), 5)


def heart_icon(c, x, y, r, b=1.0): E.heart(c, x, y, r, b)


# ------------------------------------------------------------ plans (début, fonction)
def p01(c, T, t):  # VS
    c.text(W / 2, 260, 'POURQUOI', 120 * min(1.05, back(t / 0.3)), WHITE, stroke=9)
    c.text(W / 2, 400, 'TU PARLES MAL ?', 96 * min(1.05, back((t - 0.15) / 0.3)), YEL, stroke=9)
    two(c, T, MOM, DAD, 'happy2', 'happy', labels=False)
    who(c, 280, 720, 'DARONNE', (200, 60, 90)); who(c, 800, 720, 'DARON', (40, 90, 170))
    c.ell(540, 1000, 70, fill=WHITE); c.text(540, 1000, 'VS', 60, (30, 30, 40))


def p02(c, T, t):
    two(c, T, MOM, SON, 'neutral', 'neutral')
    bubble(c, 'Ouais ouais…', 790, 560, back(t / 0.3), 46, tail=-1)


def p03(c, T, t):
    two(c, T, DAD, SON, 'neutral', 'scared' if T > 6.3 else 'worry', rkw=dict(tremble=3 if T > 6.3 else 0))
    bubble(c, '…', 790, 560, back(t / 0.3), 60, tail=-1)
    if T > 8.0: big(c, 'JAMAIS.', 300, T - 8.0, RED)


def p04(c, T, t):
    two(c, T, MOM, SON, 'neutral', 'neutral', lkw=dict(arms=('point', 'down')))
    bubble(c, 'Range ta chambre !', 330, 560, back((T - 9.7) / 0.3), 46, tail=1)


def p05(c, T, t):
    closeup(c, T, SON, 'neutral')
    big(c, "T'ES EN MODE :", 300, t, YEL, 96)
    bubble(c, 'Ouais ouais, tqt… plus tard.', 540, 560, back((T - 11.8) / 0.3), 46, tail=1)


def p06(c, T, t):
    c.glow(540, 1000, 600, 600, RED, 0.35)
    closeup(c, T, MOM, 'angry', arms=('hip', 'hip'))
    bubble(c, 'RANGE TA CHAMBRE !!', 540, 520, back(t / 0.25), 54, tail=1)


def p07(c, T, t):
    info = closeup(c, T, SON, 'worry')
    big(c, '*SOUPIR*', 300, t, WHITE)
    for k in range(3):
        u = (T * 0.8 + k * 0.33) % 1; c.ell(640 + u * 160, 820 - u * 200, 18 + 30 * u, fill=mix((200, 210, 220), (60, 50, 90), u))
    if T > 15.6: E.tag(c, "T'AS LE SEUM", 540, 1520, back((T - 15.68) / 0.3), 60, RED)


def p08(c, T, t):
    rain(c, T)
    closeup(c, T, SON, 'worry')
    c.text(W / 2, 300, 'MA VIE EST', 90 * min(1.05, back(t / 0.3)), WHITE, stroke=8)
    c.text(W / 2, 400, 'GÂCHÉE', 110 * min(1.05, back((t - 0.15) / 0.3)), YEL, stroke=9)


def p09(c, T, t):
    who(c, 540, 260, 'DARON', (40, 90, 170))
    closeup(c, T, DAD, 'neutral')
    if T > 19.3: bubble(c, 'Viens deux secondes.', 540, 560, back((T - 19.4) / 0.3), 48, tail=1)


def p10(c, T, t):
    E.speedlines(c, T, 18, (220, 190, 120), 300, 1800)
    character(c, 540, 1900, 2.2, dict(SON, legs='run', phase=T * 22, arms=('run_f', 'run_b'), mood='happy2', rot=0.25), T)
    big(c, 'EN SPRINT', 300, t, YEL)


def p11(c, T, t):
    two(c, T, DAD, SON, 'neutral', 'happy2', rkw=dict(arms=('down', 'wave')))
    bubble(c, 'Oui papa ! Y a quoi ?', 760, 560, back(t / 0.25), 46, tail=-1)


def p12(c, T, t):
    p = back(t / 0.35)
    c.glow(540, 900, 500, 300, RED, 0.5)
    c.rect(540 - 380 * min(1, p), 820, 540 + 380 * min(1, p), 980, fill=(225, 40, 40), r=80)
    if p > 0.6: c.text(540, 900, 'ABONNE-TOI', 84, WHITE)
    c.ell(540, 680, 60, fill=(250, 210, 70)); c.rect(500, 680, 580, 720, fill=(250, 210, 70)); c.ell(540, 745, 16, fill=(250, 210, 70))
    cx = lerp(900, 700, ease(t / 0.8)); cy = lerp(1200, 940, ease(t / 0.8))
    c.poly([(cx, cy), (cx + 70, cy + 110), (cx + 30, cy + 100), (cx + 50, cy + 160), (cx + 30, cy + 168), (cx + 12, cy + 108), (cx - 20, cy + 130)], WHITE)
    if T > 25.0: big(c, 'LA SUITE VA PIQUER', 1100, T - 25.0, YEL, 76)


def p13(c, T, t):
    if T < 28.4:
        n = min(15, 1 + int((T - 26.56) * 9))
        phone(c, 540, 860, 1.25, 'DARONNE', f'{n} appels manqués', (200, 60, 90))
        c.ell(760, 520, 50, fill=RED); c.text(760, 520, str(n), 50, WHITE)
    else:
        closeup(c, T, SON, 'calm', arms=('hold', 'down'))
        big(c, 'VU ✓✓'.replace('✓✓', ''), 300, T - 28.6, CYAN) if False else None
        E.tag(c, 'VU, PAS RÉPONDU', 540, 330, back((T - 29.0) / 0.3), 66, CYAN)


def p14(c, T, t):
    if T < 31.6:
        phone(c, 540, 860, 1.25, 'DARON', '1 appel entrant', (40, 90, 170), bad=False, ok=True, T=T)
    else:
        info = closeup(c, T, SON, 'happy2', arms=('down', 'cover'))
        big(c, 'DIRECT !', 300, T - 31.7, YEL, 130)


def p15(c, T, t):
    if T < 35.4:
        ia, ib = two(c, T, MOM, SON, 'neutral', 'worry', lkw=dict(arms=('point', 'down')))
        trash(c, 540, 1660, 1.0)
        bubble(c, 'Descends les poubelles.', 330, 560, back(t / 0.3), 44, tail=1)
    else:
        closeup(c, T, SON, 'determined', arms=('point', 'down'))
        big(c, "L'AVOCAT", 280, T - 35.6, YEL, 120)
        bubble(c, 'Objection !', 540, 560, back((T - 36.3) / 0.25), 52, tail=1)
        if T > 37.3: E.tag(c, "C'EST ABUSÉ", 540, 1540, back((T - 37.6) / 0.3), 62, RED)


def p16(c, T, t):
    if T < 39.8:
        two(c, T, DAD, SON, 'neutral', 'shock')
        bubble(c, 'Les poubelles.', 330, 560, back(t / 0.3), 46, tail=1)
    else:
        info = closeup(c, T, SON, 'happy2', arms=('hold', 'down'))
        trash(c, info['hands'][0][0] - 40, info['hands'][0][1] + 80, 1.4)
        big(c, 'DÉJÀ EN', 260, T - 39.9, WHITE, 96); big(c, 'CLAQUETTES', 380, T - 40.1, YEL, 110)


def p17(c, T, t):
    if T < 42.25:
        c.glow(540, 1000, 600, 600, RED, 0.4)
        closeup(c, T, MOM, 'angry', arms=('hip', 'hip'), tremble=2)
        bubble(c, '!!!', 540, 540, back(t / 0.2), 70, tail=1)
    else:
        closeup(c, T, SON, 'angry', arms=('up', 'up'), tremble=3)
        bubble(c, 'NON !!', 540, 520, back((T - 42.3) / 0.2), 70, tail=1)
        if T > 43.4: E.tag(c, 'TU FAIS LE CHAUD', 540, 1540, back((T - 43.5) / 0.3), 62, RED)


def p18(c, T, t):
    if T < 45.4:
        two(c, T, DAD, SON, 'angry', 'scared', rkw=dict(tremble=3))
        bubble(c, 'Hé.', 330, 560, back((T - 44.5) / 0.25), 56, tail=1)
    else:
        closeup(c, T, SON, 'calm', arms=('down', 'down'))
        big(c, 'TOUT SAGE', 300, T - 46.2, YEL, 110)
        if T > 47.7: E.tag(c, 'ZÉRO BRUIT', 540, 1540, back((T - 47.76) / 0.3), 62, CYAN)


def p19(c, T, t):
    closeup(c, T, SON, 'worry', look=(0, -4))
    c.ell(820, 520, 100, 80, fill=(232, 234, 236)); c.ell(720, 640, 22, fill=(232, 234, 236)); c.ell(680, 700, 12, fill=(232, 234, 236))
    c.text(820, 520, '?', 90, (60, 60, 70))
    big(c, 'POURQUOI ?', 300, T - 49.8, YEL, 110)


def p20(c, T, t):
    two(c, T, MOM, SON, 'happy', 'worry')
    for k in range(4):
        u = (T * 0.6 + k * 0.25) % 1; E.heart(c, 220 + k * 50, 900 - u * 300, 26 * (1 - u * 0.5))
    E.tag(c, 'ELLE PARDONNE TOUJOURS', 540, 330, back((T - 52.2) / 0.3), 58, YEL)


def p21(c, T, t):
    c.ell(880, 200, 70, fill=(250, 230, 160)); c.ell(910, 180, 62, fill=PAL['navy'][0])
    chat(c, [(53.6, 'Tu sais quoi, laisse-moi.', True), (55.5, "T'as mangé ?", False), (56.0, 'Tout va bien ? ❤'.replace(' ❤', ''), False)], T)
    E.heart(c, 800, 1150, 40, 1 + 0.08 * math.sin(T * 6))


def p22(c, T, t):
    fade = ease((T - 59.0) / 1.5)
    phone(c, 540, 820, 1.2, 'DARONNE', '0 appel' if T > 59.0 else '15 appels', mix((200, 60, 90), (70, 70, 80), fade), bad=False)
    character(c, 540, 1900, 1.4, dict(SON, mood='worry', look=(0, -4)), T)
    big(c, "UN JOUR…", 260, t, WHITE, 100)
    if T > 59.0: E.tag(c, 'ÇA SONNERA PLUS', 540, 1150, back((T - 59.4) / 0.3), 60, RED)


def p23(c, T, t):
    a = 0.35 + 0.1 * math.sin(T * 2)
    gc = C(Image.new('RGB', (W * S, H * S), (0, 0, 0)))
    character(gc, 300, 1560, 1.5, dict(MOM, mood='happy', arms=('point', 'down'), shadow=False), T)
    ghost = gc.im
    gl = ghost.convert('L').point(lambda v: int(255 * a) if v > 0 else 0)
    c.im.paste(ghost, (0, 0), gl); c.d = ImageDraw.Draw(c.im)
    bubble(c, 'Range ta chambre…', 330, 640, back((T - 62.6) / 0.4), 42, tail=1)
    closeup(c, T, SON, 'worry', look=(-6, 0))
    if T > 61.0:
        for k in range(2):
            u = ((T - 61.0) * 0.7 + k * 0.5) % 1; c.ell(540 + 60 + k * 0, 1020 + u * 160, 12, 18, fill=(140, 200, 255))


def p24(c, T, t):
    ok = T > 66.0
    phone(c, 540, 820, 1.3, 'DARONNE', 'appel entrant…' if not ok else 'en ligne', (200, 60, 90), bad=not ok, ok=True, T=T)
    if not ok:
        r = 1 + 0.15 * ((T * 2) % 1); c.ell(540, 820 - 0.25 * 640 * 1.3, 70 * 1.3 * r * 1.3, outline=mix((200, 60, 90), (30, 30, 40), (T * 2) % 1), w=6)
    if T > 66.0:
        big(c, 'DÉCROCHE.', 1580, T - 66.0, YEL, 130)


PLANS = [(0, p01, 'teal', False), (2.7, p02, 'rose', True), (5.2, p03, 'teal', True), (8.6, p04, 'rose', True),
         (10.7, p05, 'purple', False), (13.45, p06, 'red', False), (14.3, p07, 'purple', False), (16.15, p08, 'navy', False),
         (17.84, p09, 'teal', False), (20.42, p10, 'amber', False), (22.7, p11, 'teal', True), (24.1, p12, 'red', False),
         (26.55, p13, 'rose', False), (30.22, p14, 'teal', False), (33.62, p15, 'rose', True), (38.3, p16, 'green', True),
         (41.3, p17, 'red', False), (44.02, p18, 'teal', True), (48.66, p19, 'navy', False), (50.97, p20, 'purple', True),
         (53.3, p21, 'navy', False), (56.45, p22, 'navy', False), (60.62, p23, 'navy', False), (64.26, p24, 'rose', False)]
BURST = {p06, p17, p12}
NOFLOORCLOSE = True


def plan_at(T):
    i = max(k for k, p in enumerate(PLANS) if p[0] <= T + 1e-6)
    t0, fn, col, fl = PLANS[i]
    t1 = PLANS[i + 1][0] if i + 1 < len(PLANS) else DUR
    return t0, t1, fn, col, fl


# ------------------------------------------------------------ légendes
HL = {'MÈRE', 'PÈRE', 'DARON', 'DARONNE', 'JAMAIS', 'CHAMBRE', 'SEUM', 'VIE', 'SPRINT', 'ABONNE-TOI', 'PIQUER', 'QUINZE',
      'GHOSTES', 'RÉPONDU', 'UNE', 'DÉCROCHES', "L'AVOCAT", 'ABUSÉ', 'CLAQUETTES', 'CHAUD', 'SAGE', 'CALME', 'ZÉRO',
      'PARDONNER', 'MANGÉ', 'JOUR', 'TOUT', 'DÉCROCHE', 'FRÈRE', 'FRÉROT'}


def captions():
    toks = []
    for line in open(os.path.join(HERE, 'words.txt'), encoding='utf-8'):
        w, t0 = line.rsplit(' ', 1); toks.append((w, float(t0)))
    words = []
    for w, t0 in toks:
        if w in (':', '«', '»') and words: continue
        if w in ('?', '!') and words: words[-1][0] += ' ?'; words[-1][3] = True; continue
        up = w.upper(); brk = up.endswith(('.', ',', '…', '?', '!'))
        disp = up.rstrip('.,') if not up.endswith('…') else up
        words.append([disp, t0, disp.strip('…?! ') in HL, brk])
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        if w[3] or len(cur) >= 3 or sum(len(x[0]) for x in cur) > 14:
            chunks.append(cur); cur = []
    if cur: chunks.append(cur)
    out = []
    for i, ch in enumerate(chunks):
        st = ch[0][1] - 0.05
        en = chunks[i + 1][0][1] - 0.05 if i + 1 < len(chunks) else ch[-1][1] + 1.2
        out.append((st, min(en, ch[-1][1] + 1.4), [(a, b, c) for a, b, c, _ in ch]))
    return out


CAPS = captions()


def frame(f):
    T = f / FPS
    t0, t1, fn, col, fl = plan_at(T)
    c = C(vbg(col, floor=fl, burst=fn in BURST))
    fn(c, T, T - t0)
    edge = min(T - t0, t1 - T)
    dark = max(0.0, 1 - edge / 0.07) * 0.6
    zoom = 1.0 + 0.04 * ((T - t0) / max(0.1, t1 - t0))
    im = E.finish(c.im, zoom, dark)
    if T > DUR - 0.6: im = Image.blend(im, Image.new('RGB', im.size, (0, 0, 0)), (T - (DUR - 0.6)) / 0.6)
    d = ImageDraw.Draw(im)
    for st, en, ch in CAPS:
        if st <= T < en: E.caption(d, ch, T, y=1330, size=78); break
    return im


def render(args):
    a, b, path = args
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-tune', 'animation', path], stdin=subprocess.PIPE)
    for f in range(a, b): p.stdin.write(frame(f).tobytes())
    p.stdin.close(); p.wait(); return path


if __name__ == '__main__':
    out = os.path.join(HERE, 'out'); os.makedirs(out, exist_ok=True)
    if sys.argv[1] == 'sheet':
        fs = [int(float(v) * FPS) for v in sys.argv[2].split(',')]
        ims = [frame(f).resize((270, 480)) for f in fs]
        cols = 6; rows = (len(ims) + cols - 1) // cols
        sh = Image.new('RGB', (270 * cols, 480 * rows))
        for i, im in enumerate(ims): sh.paste(im, ((i % cols) * 270, (i // cols) * 480))
        sh.save(sys.argv[3])
    else:
        n = 4; step = math.ceil(N / n)
        jobs = [(i * step, min(N, (i + 1) * step), os.path.join(out, f'p{i}.mp4')) for i in range(n)]
        with Pool(n) as pool: parts = pool.map(render, jobs)
        with open(os.path.join(out, 'list.txt'), 'w') as fh:
            for p in parts: fh.write(f"file '{p}'\n")
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', os.path.join(out, 'list.txt'),
                        '-c', 'copy', os.path.join(out, 'short_daronne_muet.mp4')], check=True)
        print('ok')
