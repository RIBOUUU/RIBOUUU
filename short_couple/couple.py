"""Short « Pourquoi t'es nul en couple ? » — réutilise le modèle short_daronne/short.py."""
import sys, os, math, random, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'short_daronne'))
import short as SH
from short import E, C, character, bubble, back, ease, lerp, mix, font, YEL, RED, CYAN, WHITE, BLK, W, H, FPS, FLOOR
from PIL import Image
from multiprocessing import Pool

HIM = SH.SON
HER = dict(col=(64, 156, 160), outfit='dress', longhair=True, earrings=True, hair=(140, 62, 40))
WOOD = (92, 70, 64)
SHEET = (214, 206, 220)
DUVET = (70, 78, 120)


def tag(c, txt, x, y, T, t0, col=YEL, size=56):
    E.tag(c, txt, x, y, back((T - t0) / 0.3), size, col)


# ------------------------------------------------------------ décor
def bed_back(c, cx=540, top=1320, w=860):
    c.rect(cx - w / 2, top - 520, cx + w / 2, top + 40, fill=WOOD, r=40)
    c.rect(cx - w / 2 + 30, top - 490, cx + w / 2 - 30, top - 60, fill=tuple(v + 14 for v in WOOD), r=28)
    for sx in (-1, 1):
        c.ell(cx + sx * w * 0.24, top - 130, w * 0.19, 60, fill=SHEET)


def bed_front(c, cx=540, top=1320, w=860, col=DUVET):
    c.rect(cx - w / 2 - 20, top, cx + w / 2 + 20, top + 330, fill=col, r=36)
    c.rect(cx - w / 2 - 20, top, cx + w / 2 + 20, top + 50, fill=tuple(min(255, v + 30) for v in col), r=24)
    c.rect(cx - w / 2 - 10, top + 330, cx + w / 2 + 10, top + 400, fill=WOOD, r=12)


def in_bed(c, T, a=None, b=None, gap=0, top=1320, w=860, col=DUVET, s=1.55):
    """Couple assis dans le lit (vue de face)."""
    bed_back(c, 540, top, w)
    gy = top + 230
    out = []
    for P, x in ((a, 540 - w * 0.24 - gap), (b, 540 + w * 0.24 + gap)):
        if P is None: out.append(None); continue
        out.append(character(c, x, gy, s, dict(P, shadow=False), T))
    bed_front(c, 540, top, w, col)
    return out


def lying(c, T, a=None, b=None, top=1150, moods=('neutral', 'neutral'), looks=((0, -6), (0, -6)), sep=230):
    """Têtes sur l'oreiller, couette jusqu'au menton (vue plongée)."""
    c.rect(60, top - 250, 1020, top + 900, fill=(150, 146, 170), r=40)
    for k, (P, x) in enumerate(((a, 540 - sep), (b, 540 + sep))):
        c.ell(x, top - 40, 200, 90, fill=SHEET)
        if P is None: continue
        r = 110
        if P.get('longhair'): c.ell(x, top - 40, r * 1.25, r * 1.05, fill=P['hair'])
        c.ell(x, top - 30, r, fill=BLK)
        if not P.get('longhair'):
            c.d.chord([(x - r * 0.95) * E.S, (top - 30 - r * 1.08) * E.S, (x + r * 0.95) * E.S, (top - 30 - r * 0.2) * E.S], 190, 350, fill=P.get('hair', (120, 40, 36)))
        else:
            c.d.chord([(x - r * 1.05) * E.S, (top - 30 - r * 1.15) * E.S, (x + r * 1.05) * E.S, (top - 30 + r * 0.1) * E.S], 180, 360, fill=P['hair'])
        E.face(c, x, top - 20, r / 62, moods[k], blink=(T % 3.0) < 0.08 and moods[k] not in ('sleep',), look=looks[k])
    c.rect(40, top + 70, 1040, top + 1000, fill=DUVET, r=60)
    c.rect(40, top + 70, 1040, top + 130, fill=tuple(v + 30 for v in DUVET), r=30)


def clock(c, x, y, r, hh, mm):
    c.ell(x, y, r + 10, fill=(40, 40, 48)); c.ell(x, y, r, fill=(236, 236, 240))
    for k in range(12):
        a = k * math.pi / 6; c.line([(x + math.sin(a) * r * 0.82, y - math.cos(a) * r * 0.82), (x + math.sin(a) * r * 0.92, y - math.cos(a) * r * 0.92)], (60, 60, 70), 4)
    ah = (hh % 12 + mm / 60) * math.pi / 6; am = mm * math.pi / 30
    c.line([(x, y), (x + math.sin(ah) * r * 0.5, y - math.cos(ah) * r * 0.5)], BLK, 10)
    c.line([(x, y), (x + math.sin(am) * r * 0.78, y - math.cos(am) * r * 0.78)], BLK, 6)
    c.ell(x, y, 9, fill=RED)


def couch(c, x, gy, w=440):
    c.rect(x - w / 2, gy - 330, x + w / 2, gy - 120, fill=(52, 60, 96), r=40)
    c.rect(x - w / 2 - 40, gy - 210, x - w / 2 + 40, gy - 40, fill=(44, 52, 86), r=30)
    c.rect(x + w / 2 - 40, gy - 210, x + w / 2 + 40, gy - 40, fill=(44, 52, 86), r=30)
    c.rect(x - w / 2, gy - 140, x + w / 2, gy - 50, fill=(62, 72, 112), r=24)


def lamp(c, x, y, on=1.0, k=1.0):
    if on > 0: c.glow(x, y + 120 * k, 420 * k, 360 * k, (255, 220, 150), 0.55 * on)
    c.line([(x, y - 400), (x, y - 70 * k)], (40, 40, 46), 6)
    c.poly([(x - 120 * k, y + 60 * k), (x + 120 * k, y + 60 * k), (x + 50 * k, y - 70 * k), (x - 50 * k, y - 70 * k)], mix((90, 90, 96), (255, 236, 190), on))


def book(c, x, y, k=1.0):
    c.poly([(x - 70 * k, y - 50 * k), (x, y - 40 * k), (x, y + 50 * k), (x - 70 * k, y + 40 * k)], (170, 40, 50))
    c.poly([(x + 70 * k, y - 50 * k), (x, y - 40 * k), (x, y + 50 * k), (x + 70 * k, y + 40 * k)], (190, 50, 60))
    c.line([(x, y - 40 * k), (x, y + 50 * k)], (120, 20, 30), 4)


def tv(c, x, y, T):
    c.glow(x, y, 360, 260, (90, 160, 255), 0.5 + 0.1 * math.sin(T * 9))
    c.rect(x - 230, y - 140, x + 230, y + 140, fill=(20, 22, 30), r=16)
    c.rect(x - 210, y - 120, x + 210, y + 120, fill=mix((40, 90, 200), (120, 200, 255), 0.5 + 0.5 * math.sin(T * 5)), r=8)
    c.text(x, y, 'GAME', 60, WHITE)


def phone_small(c, x, y, k=1.0, glow=True):
    if glow: c.glow(x, y, 160 * k, 160 * k, (120, 190, 255), 0.5)
    c.rect(x - 34 * k, y - 60 * k, x + 34 * k, y + 60 * k, fill=(20, 22, 30), r=12 * k)
    c.rect(x - 28 * k, y - 52 * k, x + 28 * k, y + 52 * k, fill=(110, 170, 250), r=8 * k)


def zz(c, x, y, T):
    for k in range(3):
        u = (T * 0.7 + k / 3) % 1
        c.text(x + 40 * u + k * 10, y - 140 * u, 'Z', 40 + 30 * u, (220, 220, 240))


def brain(c, x, y, k=1.0, T=0):
    c.glow(x, y, 300 * k, 200 * k, (255, 140, 200), 0.4)
    for dx, dy, r in [(-110, 0, 90), (-40, -50, 95), (50, -50, 95), (120, 0, 90), (60, 50, 90), (-50, 50, 90), (0, 0, 100)]:
        c.ell(x + dx * k, y + dy * k, r * k, r * 0.85 * k, fill=(240, 160, 200))
    for dx, dy in [(-60, -10), (40, 10), (-10, 40)]:
        c.arc(x + dx * k, y + dy * k, 40 * k, 200, 340, (210, 120, 170), 6)


def weight(c, x, y, k=1.0):
    c.poly([(x - 120 * k, y + 110 * k), (x + 120 * k, y + 110 * k), (x + 80 * k, y - 80 * k), (x - 80 * k, y - 80 * k)], (60, 64, 74))
    c.arc(x, y - 100 * k, 40 * k, 180, 360, (60, 64, 74), 18 * k)
    c.text(x, y + 20 * k, '100 KG', 50 * k, WHITE)


# ------------------------------------------------------------ plans
def q01(c, T, t):
    SH.closeup(c, T, HIM, 'shock')
    SH.big(c, "POURQUOI T'ES NUL", 250, t, WHITE, 96); SH.big(c, 'EN COUPLE ?', 380, t - 0.15, YEL, 130)


def q02(c, T, t):
    in_bed(c, T, dict(HIM, mood='angry', look=(-6, 0), arms=('cross', 'cross')), dict(HER, mood='angry', look=(6, 0), arms=('cross', 'cross')), gap=60)
    SH.big(c, 'ZÉRO INTIMITÉ', 300, t, RED, 110)


def q03(c, T, t):
    clock(c, 820, 420, 110, 23, int(10 + t * 20))
    bed_back(c, 360, 1360, 560)
    character(c, 280, 1590, 1.45, dict(HER, mood='sleep', shadow=False), T)
    bed_front(c, 360, 1360, 560)
    couch(c, 860, 1760, 360)
    character(c, 860, 1700, 1.4, dict(HIM, legs='sit', mood='neutral', look=(0, 4), arms=('hold', 'hold')), T)
    phone_small(c, 860, 1330, 0.8)
    SH.big(c, 'PLUS EN MÊME TEMPS', 220, t, YEL, 82)


def q04(c, T, t):
    SH.closeup(c, T, HIM, 'determined', arms=('down', 'point'))
    SH.big(c, 'ET NON…', 230, t, WHITE, 100)
    if T > 5.4:
        SH.big(c, 'PAS LA FATIGUE', 360, T - 5.5, RED, 110)


def q05(c, T, t):
    character(c, 330, FLOOR, 2.0, dict(HER, mood='neutral', flip=-1, look=(-7, 0)), T)
    character(c, 760, FLOOR, 2.0, dict(HIM, mood='neutral', look=(7, 0)), T)
    SH.big(c, 'LES PSYS', 230, t, WHITE, 90)
    if T > 7.5: SH.big(c, "L'ÉVITEMENT", 360, T - 7.6, YEL, 130)


def q06(c, T, t):
    in_bed(c, T, dict(HIM, mood='worry', look=(4, 0)), dict(HER, mood='worry', look=(-4, 0)), gap=90)
    c.rect(510, 1350, 570, 1650, fill=(235, 235, 245), r=10)
    SH.big(c, 'VOUS VOUS', 220, t, WHITE, 96); SH.big(c, 'TOUCHEZ PLUS', 340, t - 0.15, YEL, 110)
    if T > 10.9: tag(c, 'LE MANQUE', 540, 520, T, 10.96, RED, 60)


def q07(c, T, t):
    lying(c, T, HIM, HER, moods=('neutral', 'neutral'), looks=((0, -6), (0, -6)))
    SH.big(c, 'DEUX CORPS', 260, t, WHITE, 110); SH.big(c, 'CÔTE À CÔTE', 390, t - 0.15, YEL, 110)


def q08(c, T, t):
    lying(c, T, HIM, HER, moods=('worry', 'worry'), looks=((5, -2), (-5, -2)))
    lamp(c, 540, 380, 1 - ease((T - 15.7) / 0.6), 0.9)
    SH.big(c, 'SILENCE GÊNANT', 640, t, WHITE, 96)
    bubble(c, '…', 300, 860, back((T - 14.6) / 0.3), 60, tail=1)


def q09(c, T, t):
    character(c, 280, FLOOR, 1.95, dict(HER, mood='neutral', arms=('down', 'shrug'), look=(-6, 0)), T)
    character(c, 800, FLOOR, 1.95, dict(HIM, mood='neutral', arms=('shrug', 'down'), look=(6, 0)), T)
    SH.big(c, 'CHACUN', 240, t, WHITE, 110); SH.big(c, 'SON EXCUSE', 370, t - 0.15, YEL, 120)


def q10(c, T, t):
    lamp(c, 260, 520, 1.0, 0.8)
    SH.closeup(c, T, HER, 'calm', arms=('hold', 'hold'))
    book(c, 540, 1540, 1.6)
    clock(c, 840, 560, 100, 21, 0)
    SH.big(c, '21 H :', 220, t, WHITE, 100); SH.big(c, 'SON LIVRE', 340, t - 0.15, YEL, 110)


def q11(c, T, t):
    tv(c, 540, 560, T)
    couch(c, 540, 1760, 560)
    character(c, 540, 1700, 1.8, dict(HIM, legs='sit', mood='happy2', arms=('hold', 'hold')), T)
    c.rect(480, 1290, 600, 1340, fill=(30, 30, 36), r=20)
    SH.big(c, 'UNE GAME', 230, t, YEL, 110)
    for x, y, txt, t0 in [(220, 860, 'UN MATCH', 23.16), (820, 860, 'UN ÉPISODE', 24.0)]:
        if T > t0: tag(c, txt, x, y, T, t0, CYAN, 50)


def q12(c, T, t):
    lying(c, T, None, HER, moods=('neutral', 'sleep'), looks=((0, 0), (0, 0)))
    zz(c, 800, 900, T)
    x = lerp(1200, 300, ease(t / 1.2))
    character(c, x, 1900, 1.3, dict(HIM, legs='run', phase=T * 6, mood='worry', arms=('run_f', 'run_b')), T)
    SH.big(c, 'ELLE DORT DÉJÀ', 300, t, WHITE, 100)
    if T > 26.68: tag(c, 'ZÉRO BRUIT', 540, 470, T, 26.68, YEL, 60)


def q13(c, T, t):
    p = back(t / 0.35)
    c.glow(540, 900, 500, 300, RED, 0.5)
    c.rect(540 - 380 * min(1, p), 820, 540 + 380 * min(1, p), 980, fill=(225, 40, 40), r=80)
    if p > 0.6: c.text(540, 900, 'ABONNE-TOI', 84, WHITE)
    c.ell(540, 680, 60, fill=(250, 210, 70)); c.rect(500, 680, 580, 720, fill=(250, 210, 70)); c.ell(540, 745, 16, fill=(250, 210, 70))
    cx = lerp(900, 700, ease(t / 0.8)); cy = lerp(1200, 940, ease(t / 0.8))
    c.poly([(cx, cy), (cx + 70, cy + 110), (cx + 30, cy + 100), (cx + 50, cy + 160), (cx + 30, cy + 168), (cx + 12, cy + 108), (cx - 20, cy + 130)], WHITE)
    if T > 28.6: SH.big(c, 'LA SUITE VA PIQUER', 1100, T - 28.64, YEL, 76)


def q14(c, T, t):
    lying(c, T, HIM, HER, moods=('worry', 'worry'), looks=((-6, 0), (6, 0)), sep=250)
    SH.big(c, 'DANS LE NOIR…', 300, t, WHITE, 110)
    if T > 31.4: tag(c, 'CHACUN GAMBERGE', 540, 450, T, 31.48, YEL, 58)


def q15(c, T, t):
    SH.closeup(c, T, HIM, 'worry', arms=('down', 'think'))
    bubble(c, "Elle m'en veut ?", 540, 330, back((T - 32.86) / 0.3), 60, tail=1)
    bubble(c, 'Je lui plais plus ?', 540, 520, back((T - 33.73) / 0.3), 60, tail=1)


def q16(c, T, t):
    SH.closeup(c, T, HER, 'worry', look=(6, 0))
    bubble(c, 'Il préfère son tel', 540, 330, back((T - 35.42) / 0.3), 58, tail=-1)
    bubble(c, 'à moi ?', 540, 480, back((T - 36.3) / 0.3), 58, tail=-1)
    phone_small(c, 880, 700, 1.3)


def q17(c, T, t):
    character(c, 360, FLOOR, 2.0, dict(HER, mood='calm', arms=('down', 'point')), T)
    character(c, 720, FLOOR, 2.0, dict(HIM, mood='calm', arms=('point', 'down')), T)
    E.heart(c, 540, 1080, 50)
    SH.big(c, "PERSONNE NE FUIT", 230, t, WHITE, 90); SH.big(c, "L'AUTRE", 340, t - 0.15, YEL, 110)
    if T > 38.88: tag(c, 'VOUS FUYEZ CE MOMENT', 540, 520, T, 38.88, RED, 54)


def q18(c, T, t):
    d = ease(t / 1.6)
    character(c, lerp(380, 180, d), FLOOR, 2.0, dict(HER, mood='worry', flip=-1, look=(-6, 0)), T)
    character(c, lerp(700, 900, d), FLOOR, 2.0, dict(HIM, mood='worry', look=(6, 0)), T)
    SH.big(c, 'LE DÉTACHEMENT', 300, t, RED, 100)
    if T > 41.8: SH.big(c, 'COMMENCE', 420, T - 41.84, WHITE, 90)


def q19(c, T, t):
    in_bed(c, T, dict(HIM, mood='happy', look=(6, 0)), dict(HER, mood='happy2', look=(-6, 0)), gap=-40, col=(150, 90, 70))
    lamp(c, 900, 600, 1.0, 0.6)
    SH.big(c, 'VOTRE DERNIER', 220, t, WHITE, 96); SH.big(c, 'RENDEZ-VOUS', 340, t - 0.15, YEL, 116)


def q20(c, T, t):
    laugh = T > 48.6
    in_bed(c, T, dict(HIM, mood='happy2' if laugh else 'happy', look=(6, 0), arms=('down', 'wave') if laugh else ('down', 'down')),
           dict(HER, mood='happy2' if laugh else 'calm', look=(-6, 0)), gap=-40, col=(150, 90, 70))
    for y, txt, t0, col in [(260, 'LES CONFIDENCES', 45.87, YEL), (400, 'LES PIEDS GELÉS', 47.44, CYAN), (540, 'LES FOUS RIRES', 48.56, (255, 150, 200))]:
        if T > t0: tag(c, txt, 540, y, T, t0, col, 60)


def q21(c, T, t):
    character(c, 220, FLOOR, 1.9, dict(HER, mood='worry', flip=-1, look=(-6, 0)), T)
    character(c, 860, FLOOR, 1.9, dict(HIM, mood='worry', look=(6, 0)), T)
    k = 1 - ease((T - 50.4) / 1.2) * 0.85
    E.heart(c, 540, 1000, 80 * k, col=mix((80, 80, 90), (230, 60, 70), k))
    SH.big(c, 'LA TENDRESSE', 240, t, WHITE, 110); SH.big(c, 'SE BARRE', 370, t - 0.15, RED, 120)


def q22(c, T, t):
    bed_back(c, 540, 1420, 620); bed_front(c, 540, 1420, 620, (90, 92, 110))
    character(c, 140, FLOOR, 1.6, dict(HER, mood='worry', look=(6, 0)), T)
    character(c, 940, FLOOR, 1.6, dict(HIM, mood='worry', look=(-6, 0)), T)
    weight(c, 540, lerp(300, 900, ease((T - 53.7) / 0.5)) if T > 53.7 else -400, 1.3)
    SH.big(c, 'PLUS TU ESQUIVES…', 240, t, WHITE, 90)
    if T > 54.0: SH.big(c, 'PLUS C\'EST LOURD', 380, T - 54.0, RED, 100)


def q23(c, T, t):
    brain(c, 540, 520, 1.3)
    bed_back(c, 540, 1460, 820); bed_front(c, 540, 1460, 820, (90, 92, 110))
    for x, t0 in [(340, 56.28), (740, 57.64)]:
        if T > t0: tag(c, 'À ÉVITER', x, 1040, T, t0, RED, 60)
    SH.big(c, 'TON CERVEAU', 220, t, WHITE, 100)


def q24(c, T, t):
    clock(c, 540, 380, 120, 0, int(40 + t * 30))
    bed_back(c, 330, 1380, 560)
    character(c, 250, 1610, 1.4, dict(HER, mood='sleep', shadow=False), T)
    bed_front(c, 330, 1380, 560)
    couch(c, 860, 1760, 340)
    character(c, 860, 1700, 1.3, dict(HIM, legs='sit', mood='worry', arms=('hold', 'hold')), T)
    phone_small(c, 860, 1370, 0.7)
    SH.big(c, 'PAS SÉPARÉS…', 620, t, WHITE, 90)
    if T > 60.6: SH.big(c, 'HEURES DÉCALÉES', 760, T - 60.68, YEL, 96)


def q25(c, T, t):
    lamp(c, 540, 400, 1.0, 1.1)
    in_bed(c, T, dict(HIM, mood='worry', look=(4, -6)), dict(HER, mood='worry', look=(-4, -6)), gap=40)
    if T < 63.0: SH.big(c, "VOUS VOUS AIMEZ", 640, t, WHITE, 80)
    else:
        SH.big(c, 'PERSONNE', 600, T - 63.0, WHITE, 100); SH.big(c, "N'ÉTEINT", 720, T - 63.15, YEL, 110)


def q26(c, T, t):
    SH.closeup(c, T, HIM, 'determined', arms=('down', 'hold'))
    phone_small(c, 760, lerp(1450, 1700, ease((T - 67.7) / 0.5)), 1.4, glow=False)
    SH.big(c, 'CE SOIR, FRÈRE…', 240, t, WHITE, 96)
    if T > 67.7: SH.big(c, 'POSE TON TEL', 380, T - 67.72, YEL, 116)


def q27(c, T, t):
    in_bed(c, T, dict(HIM, mood='happy2', look=(6, 0)), dict(HER, mood='happy2', look=(-6, 0)), gap=-60, col=(150, 90, 70))
    lamp(c, 900, 600, 1 - ease((T - 69.6) / 0.4), 0.6)
    E.heart(c, 540, 820, 50 * (1 + 0.08 * math.sin(T * 8)))
    SH.big(c, 'VA TE COUCHER', 220, t, WHITE, 100); SH.big(c, 'AVEC ELLE', 340, t - 0.15, YEL, 116)


SH.PLANS = [(0, q01, 'teal', False), (1.5, q02, 'purple', False), (4.0, q03, 'navy', True), (5.0, q04, 'teal', False),
            (6.26, q05, 'purple', True), (8.5, q06, 'purple', False), (12.3, q07, 'navy', False), (14.14, q08, 'navy', False),
            (16.5, q09, 'amber', True), (18.42, q10, 'rose', False), (20.7, q11, 'navy', True), (24.74, q12, 'navy', False),
            (27.58, q13, 'red', False), (30.14, q14, 'navy', False), (32.22, q15, 'purple', False), (34.83, q16, 'rose', False),
            (37.0, q17, 'teal', True), (40.46, q18, 'red', True), (42.5, q19, 'amber', False), (45.74, q20, 'amber', False),
            (49.42, q21, 'navy', True), (52.3, q22, 'purple', True), (54.86, q23, 'purple', False), (58.14, q24, 'navy', True),
            (61.63, q25, 'amber', False), (66.14, q26, 'teal', False), (68.66, q27, 'rose', False)]
SH.BURST = {q13, q18}
SH.DUR = 70.8
SH.N = int(SH.DUR * FPS)
SH.HL = {'NUL', 'COUPLE', 'INTIMES', 'FATIGUE', "L'ÉVITEMENT", 'TOUCHEZ', 'MANQUE', 'SILENCE', 'GÊNANT', 'EXCUSE', 'LIVRE',
         'GAME', 'DÉJÀ', 'ZÉRO', 'ABONNE-TOI', 'PIQUER', 'NOIR', 'GAMBERGE', 'TEL', 'FUIT', 'FUYEZ', 'DÉTACHEMENT',
         'RENDEZ-VOUS', 'CONFIDENCES', 'GELÉS', 'RIRES', 'TENDRESSE', 'BARRE', 'LOURD', 'CERVEAU', 'ÉVITER', 'DÉCALÉES',
         'LUMIÈRE', 'PREMIER', 'FRÈRE', 'POSE', 'ELLE'}
SH.HERE = HERE
SH.CAPS = SH.captions()


def render(args):
    a, b, path = args
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-tune', 'animation', path], stdin=subprocess.PIPE)
    for f in range(a, b): p.stdin.write(SH.frame(f).tobytes())
    p.stdin.close(); p.wait(); return path


if __name__ == '__main__':
    out = os.path.join(HERE, 'out'); os.makedirs(out, exist_ok=True)
    if sys.argv[1] == 'sheet':
        fs = [int(float(v) * FPS) for v in sys.argv[2].split(',')]
        ims = [SH.frame(f).resize((270, 480)) for f in fs]
        sh = Image.new('RGB', (270 * 6, 480 * ((len(ims) + 5) // 6)))
        for i, im in enumerate(ims): sh.paste(im, ((i % 6) * 270, (i // 6) * 480))
        sh.save(sys.argv[3])
    elif sys.argv[1] == 'full':
        n = 4; step = math.ceil(SH.N / n)
        jobs = [(i * step, min(SH.N, (i + 1) * step), os.path.join(out, f'p{i}.mp4')) for i in range(n)]
        with Pool(n) as pool: parts = pool.map(render, jobs)
        with open(os.path.join(out, 'list.txt'), 'w') as fh:
            for p in parts: fh.write(f"file '{p}'\n")
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', os.path.join(out, 'list.txt'),
                        '-c', 'copy', os.path.join(out, 'couple_muet.mp4')], check=True)
        print('ok')
