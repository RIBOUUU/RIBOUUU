"""Scènes de la vidéo « Ces 5 super-pouvoirs te tueraient en quelques secondes » (style vectoriel sombre)."""
import math, random, sys, os
from engine import *

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from narration import SECTIONS

NF = [2028, 2686, 3002, 2659, 2791, 2909, 2698]
OFF = [0]
for n in NF: OFF.append(OFF[-1] + n)
TOTAL = OFF[-1]

# ------------------------------------------------------------------ légendes
HL = {'GÉANT', 'MOURIR', 'SECONDES', 'PHYSIQUE', 'FACTURE', 'FRAGILITÉ', 'MINUSCULE', 'S\'EFFONDRE', 'CINQ', 'BRUTAL',
      'PIÈGE', 'SPECTACULAIRE', 'MILLE', 'CENT', 'DIX', 'OS', 'CARRÉ-CUBE', 'GALILÉE', 'ÉLÉPHANT', 'BALEINE', 'FÉMURS',
      'ÉCRASÉ', 'CUIT', 'VOLER', 'EVEREST', 'MASQUE', 'ARMSTRONG', 'BOUT', 'INCONSCIENT', 'VITE', 'SUPER-VITESSE',
      'ACCÉLÉRATION', 'POIDS', 'STAPP', 'SON', 'CHAUFFE', 'TEE-SHIRT', 'CŒUR', 'L\'ÉLECTRICITÉ', 'ÉCLAIRS', 'VOLTS',
      'ÉLECTRIQUE', 'SINUSAL', 'FIBRILLATION', 'VENTRICULAIRE', 'DÉFIBRILLATEUR', 'SAUVER', 'TÉLÉPORTATION', 'CLAC',
      'NOBEL', 'ASPECT', 'FICTION', 'TOURNE', 'NEWTON', 'OPPOSÉE', 'KILOMÈTRES-HEURE', 'TGV', 'RETOURNEMENT',
      'SOLEIL', 'CHANGEMENT', 'COMMENTAIRE', 'ABONNE-TOI', 'DANGEREUX', 'VIE', 'QUANTIQUE', 'LYON', 'PARIS',
      'NOUVELLE-ZÉLANDE', 'ANTIPODES', 'KILOMÈTRES', 'MÈTRES', 'DEGRÉS', 'TRENTE-SEPT', 'APOLLO', 'ANGUILLE'}
NUMS = {'DEUX', 'TROIS', 'QUATRE', 'CINQ', 'SIX', 'SEPT', 'HUIT', 'NEUF', 'DIX', 'ONZE', 'CENT', 'CENTS', 'MILLE',
        'DIX-SEPT', 'DIX-NEUF', 'TRENTE', 'TRENTE-HUIT', 'TRENTE-SEPT', 'TRENTE-QUATRE', 'QUARANTE-CINQ', 'QUARANTE-SIX',
        'CINQUANTE-HUIT', 'CINQUANTE-QUATRE', 'SOIXANTE', 'SOIXANTE-DIX', 'SOIXANTE-DIX-HUIT', 'QUATRE-VINGTS',
        'VINGT-DEUX', 'QUINZE'}


def build_captions():
    chunks = []  # (t_start_global, t_end_global, [(WORD, t_global, yellow)])
    for s, txt in enumerate(SECTIONS.values()):
        toks = txt.split(); ts = [float(v) for v in open(os.path.join(HERE, f't{s}.txt')).read().split()]
        assert len(toks) == len(ts), (s, len(toks), len(ts))
        base = OFF[s] / FPS
        words = []
        for w, t0 in zip(toks, ts):
            if w in (':', '«', '»') and words:
                continue
            if w in ('?', '!') and words:
                words[-1][0] += ' ' + w; words[-1][3] = True; continue
            clean = w.strip('«»').upper()
            brk = clean.endswith(('.', ',', '…', '?', '!', ':', ';'))
            disp = clean.rstrip('.,;:') if not clean.endswith('…') else clean
            key = disp.strip('…?! ').strip()
            words.append([disp, base + t0, key in HL or key in NUMS, brk])
        cur = []
        for w in words:
            cur.append(w)
            if w[3] or len(cur) >= 3 or sum(len(x[0]) for x in cur) > 16:
                chunks.append(cur); cur = []
        if cur: chunks.append(cur)
    out = []
    for i, ch in enumerate(chunks):
        st = ch[0][1] - 0.05
        en = chunks[i + 1][0][1] - 0.05 if i + 1 < len(chunks) else ch[-1][1] + 1.2
        en = min(en, ch[-1][1] + 1.6)
        out.append((st, en, [(w[0], w[1], w[2]) for w in ch]))
    return out


CAPS = build_captions()

# ------------------------------------------------------------------ helpers de scène
def me(c, x, T, s=1.0, gy=GY, **kw):
    kw.setdefault('blink', (T % 3.7) < 0.09)
    return character(c, x, gy, s, kw, T)


def at(T, t0, d=0.35): return back((T - t0) / d)


def card(c, x, y, w, h, label, kind, T, hi=0.0):
    col = mix((26, 52, 66), (70, 40, 46), hi)
    c.glow(x, y, w * 0.8, h * 0.8, RED if hi > 0.5 else CYAN, 0.25 + 0.3 * hi)
    c.rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, fill=col, r=26, outline=mix((70, 120, 140), RED, hi), w=5)
    icon(c, kind, x, y - 20, 0.9, T)
    c.text(x, y + h / 2 - 40, label, 40, YEL)


def icon(c, kind, x, y, k, T):
    if kind == 'giant':
        for bx in (-90, 50):
            c.rect(x + bx * k, y + 30 * k, x + (bx + 40) * k, y + 90 * k, fill=(44, 88, 110), r=4)
        character(c, x, y + 92 * k, 0.4 * k, dict(mood='happy', arms=('up', 'up'), shadow=False), T)
    elif kind == 'fly':
        character(c, x, y + 70 * k, 0.36 * k, dict(legs='fly', arms=('fly', 'fly'), mood='happy', shadow=False), T)
        c.ell(x - 70 * k, y + 80 * k, 40 * k, 16 * k, fill=(220, 230, 236)); c.ell(x + 70 * k, y + 70 * k, 50 * k, 18 * k, fill=(220, 230, 236))
    elif kind == 'speed':
        for i in range(4): c.line([(x - 120 * k, y - 40 * k + i * 28 * k), (x - 50 * k, y - 40 * k + i * 28 * k)], CYAN, 6 * k)
        character(c, x + 20 * k, y + 90 * k, 0.38 * k, dict(legs='run', phase=T * 14, arms=('run_f', 'run_b'), mood='determined', shadow=False), T)
    elif kind == 'elec':
        bolt(c, x - 20 * k, y - 90 * k, x + 20 * k, y + 80 * k, int(T * 12), w=7 * k, amp=30 * k)
    elif kind == 'portal':
        c.glow(x, y, 130 * k, 130 * k, (170, 110, 255), 0.6)
        c.ell(x, y, 85 * k, 100 * k, outline=(190, 150, 255), w=10 * k)
        c.ell(x, y, 60 * k, 74 * k, fill=(60, 30, 110))
        for i in range(6):
            a = T * 3 + i; c.ell(x + math.cos(a) * 70 * k, y + math.sin(a) * 84 * k, 6 * k, fill=(220, 200, 255))


def iso(c, ox, oy, a, b, h, u, col=(110, 200, 220)):
    """Boîte isométrique a x b x h (unités u) posée en (ox, oy)."""
    cx, cy = math.cos(math.radians(30)) * u, math.sin(math.radians(30)) * u
    p0 = (ox, oy); pa = (ox + a * cx, oy - a * cy); pb = (ox - b * cx, oy - b * cy); pab = (pa[0] - b * cx, pa[1] - b * cy)
    up = lambda p: (p[0], p[1] - h * u)
    c.poly([pb, p0, up(p0), up(pb)], mix(col, BLK, 0.45))
    c.poly([p0, pa, up(pa), up(p0)], mix(col, BLK, 0.25))
    c.poly([up(p0), up(pa), up(pab), up(pb)], col)
    for p, q in ((p0, up(p0)), (up(p0), up(pa)), (up(p0), up(pb))):
        c.line([p, q], mix(col, WHITE, 0.4), 2, cap=False)


def elephant(c, x, gy, k=1.0, step=0.0):
    g = (120, 132, 142); dg = (96, 106, 116)
    for i, lx in enumerate((-110, -55, 55, 110)):
        sh = 8 * math.sin(step + i * 1.6) * k
        c.rect(x + (lx - 26) * k, gy - 170 * k + sh, x + (lx + 26) * k, gy, fill=dg if i % 2 else g, r=10 * k)
    c.ell(x, gy - 220 * k, 190 * k, 110 * k, fill=g)
    c.ell(x + 190 * k, gy - 260 * k, 85 * k, 80 * k, fill=g)
    c.ell(x + 150 * k, gy - 260 * k, 60 * k, 75 * k, fill=dg)
    c.line([(x + 255 * k, gy - 240 * k), (x + 290 * k, gy - 160 * k), (x + 270 * k, gy - 90 * k)], g, 34 * k)
    c.ell(x + 215 * k, gy - 280 * k, 9 * k, fill=BLK)


def whale(c, x, y, k=1.0, T=0):
    b = (40, 70, 110); bl = (130, 160, 190)
    sw = math.sin(T * 1.5) * 20 * k
    c.poly([(x - 330 * k, y), (x - 470 * k, y - 80 * k + sw), (x - 450 * k, y + sw * 0.2), (x - 470 * k, y + 80 * k + sw)], b)
    c.ell(x, y, 360 * k, 120 * k, fill=b)
    c.ell(x + 40 * k, y + 50 * k, 300 * k, 50 * k, fill=bl)
    c.ell(x + 250 * k, y - 20 * k, 10 * k, fill=BLK)
    c.poly([(x + 40 * k, y + 70 * k), (x - 40 * k, y + 170 * k), (x + 80 * k, y + 90 * k)], b)


def eel(c, x, y, T, k=1.0, glow=0.0):
    pts = [(x - 520 * k + i * 26 * k, y + math.sin(T * 3 + i * 0.35) * 40 * k) for i in range(36)]
    if glow > 0:
        c.glow(x - 60 * k, y, 560 * k, 140 * k, (120, 220, 255), glow)
    c.line(pts, (48, 66, 52), 56 * k)
    c.line([(px, py + 14 * k) for px, py in pts[2:]], (150, 140, 90), 16 * k)
    hx, hy = pts[-1]; c.ell(hx + 10 * k, hy, 42 * k, 30 * k, fill=(48, 66, 52)); c.ell(hx + 26 * k, hy - 8 * k, 7 * k, fill=YEL)


def car(c, x, y, k=1.0, col=(200, 70, 70)):
    c.rect(x - 120 * k, y - 60 * k, x + 120 * k, y, fill=col, r=18 * k)
    c.rect(x - 70 * k, y - 105 * k, x + 60 * k, y - 50 * k, fill=col, r=16 * k)
    c.rect(x - 58 * k, y - 95 * k, x + 48 * k, y - 60 * k, fill=(150, 210, 235), r=8 * k)
    for wx in (-70, 70): c.ell(x + wx * k, y, 30 * k, fill=BLK); c.ell(x + wx * k, y, 12 * k, fill=GREY)


def plane(c, x, y, k=1.0, col=(225, 230, 236)):
    c.poly([(x - 40 * k, y), (x + 80 * k, y), (x - 60 * k, y + 120 * k), (x - 110 * k, y + 120 * k)], (190, 198, 206))
    c.ell(x, y, 260 * k, 42 * k, fill=col)
    c.poly([(x - 220 * k, y - 10 * k), (x - 270 * k, y - 110 * k), (x - 220 * k, y - 110 * k), (x - 150 * k, y - 20 * k)], (190, 198, 206))
    for i in range(8): c.ell(x - 120 * k + i * 36 * k, y - 8 * k, 8 * k, fill=(60, 90, 120))


def brain(c, x, y, k=1.0, on=1.0):
    col = mix((60, 60, 70), (240, 160, 180), on)
    c.glow(x, y, 160 * k, 130 * k, (255, 170, 200), 0.4 * on)
    for dx, dy, r in [(-50, -20, 70), (20, -40, 72), (70, 10, 60), (-30, 40, 60), (40, 45, 55)]:
        c.ell(x + dx * k, y + dy * k, r * k, fill=col)
    for i in range(5):
        c.arc(x - 60 * k + i * 30 * k, y - 10 * k, 30 * k, 200, 340, mix(col, BLK, 0.3), 5 * k)


def aed(c, x, y, k=1.0):
    c.rect(x - 110 * k, y - 140 * k, x + 110 * k, y + 140 * k, fill=(40, 170, 90), r=18 * k)
    c.rect(x - 90 * k, y - 120 * k, x + 90 * k, y + 120 * k, outline=(220, 255, 230), w=4 * k, r=12 * k)
    heart(c, x, y - 10 * k, 60 * k, col=(250, 250, 250))
    c.poly([(x + 10 * k, y - 60 * k), (x - 20 * k, y), (x + 4 * k, y), (x - 12 * k, y + 50 * k), (x + 26 * k, y - 14 * k), (x + 2 * k, y - 14 * k)], (40, 170, 90))


def ecg(c, x, y, w, h, T, chaos=0.0):
    c.rect(x - w / 2 - 20, y - h / 2 - 20, x + w / 2 + 20, y + h / 2 + 20, fill=(40, 48, 56), r=20)
    c.rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, fill=(8, 20, 16), r=10)
    pts = []
    rr = random.Random(int(T * 20))
    for i in range(120):
        u = i / 119; px = x - w / 2 + u * w; ph = (u * 3 + T * 0.9) % 1
        v = 0
        if 0.3 < ph < 0.34: v = -0.9
        elif 0.34 < ph < 0.37: v = 0.5
        elif 0.5 < ph < 0.6: v = -0.15
        v = v * (1 - chaos) + chaos * (math.sin(u * 60 + T * 25) * 0.4 + rr.uniform(-0.25, 0.25))
        pts.append((px, y + v * h * 0.45))
    col = mix((80, 255, 140), RED, chaos)
    c.glow(x, y, w * 0.5, h * 0.5, col, 0.25)
    c.line(pts, col, 5, cap=False)


def france(c, x, y, k=1.0):
    pts = [(-0.05, -0.62), (0.32, -0.42), (0.55, -0.2), (0.5, 0.1), (0.58, 0.42), (0.3, 0.6), (0.05, 0.55), (-0.25, 0.62),
           (-0.42, 0.35), (-0.38, -0.02), (-0.7, -0.22), (-0.62, -0.36), (-0.3, -0.38)]
    c.glow(x, y, 520 * k, 480 * k, CYAN, 0.25)
    c.poly([(x + px * 420 * k, y + py * 420 * k) for px, py in pts], (44, 92, 112), outline=(110, 190, 210), w=5)


def galileo(c, x, T, s=1.0):
    info = me(c, x, T, s, col=(112, 70, 46), hair=(200, 200, 205), arms=('hold', 'down'), mood='calm')
    hx, hy, r = info['head']
    c.poly([(hx - r * 0.7, hy + r * 0.35), (hx + r * 0.7, hy + r * 0.35), (hx, hy + r * 1.35)], (200, 200, 205))
    face(c, hx, hy - 6 * s, s, 'calm')
    hd = info['hands'][0]
    c.rect(hd[0] - 70 * s, hd[1] - 20 * s, hd[0] + 10 * s, hd[1] + 70 * s, fill=(230, 214, 170), r=8)
    return info


def sled(c, x, gy, T, flame=1.0, riders=True):
    if flame > 0:
        c.glow(x - 260, gy - 110, 200 * flame, 90 * flame, (255, 150, 60), 0.8)
        c.poly([(x - 170, gy - 150), (x - 170 - 260 * flame * (0.8 + 0.2 * math.sin(T * 40)), gy - 110), (x - 170, gy - 70)], (255, 190, 90))
    c.rect(x - 180, gy - 170, x + 220, gy - 50, fill=(150, 160, 170), r=14)
    c.rect(x - 180, gy - 120, x + 220, gy - 100, fill=RED)
    for wx in (-120, 140): c.rect(x + wx - 30, gy - 50, x + wx + 30, gy - 20, fill=(60, 60, 70), r=6)
    if riders:
        info = character(c, x + 40, gy - 160, 0.55, dict(legs='sit', arms=('hold', 'hold'), col=(110, 120, 70), hair=(210, 210, 210),
                                                          mood='determined', shadow=False), T)
        return info


def capsule(c, x, y, T, heat=1.0):
    # se déplace vers le bas-gauche : bouclier en bas à gauche, traînée vers le haut à droite
    for i in range(9):
        r = random.Random(i); L = r.uniform(300, 700) * heat; off = r.uniform(-70, 70)
        c.line([(x + 40 + off * 0.7, y - 40 + off * 0.7), (x + 40 + off * 0.7 + L, y - 40 + off * 0.7 - L)],
               mix((255, 110, 40), (255, 220, 140), r.random()), 12, cap=True)
    c.glow(x - 20, y + 20, 230 * heat, 230 * heat, (255, 120, 40), 0.95)
    nx, ny = 0.7071, -0.7071  # axe (vers l'arrière)
    px, py = 0.7071, 0.7071   # perpendiculaire
    base = [(x + px * 120, y + py * 120), (x - px * 120, y - py * 120)]
    apex = [(x + nx * 190 + px * 45, y + ny * 190 + py * 45), (x + nx * 190 - px * 45, y + ny * 190 - py * 45)]
    c.poly([base[0], apex[0], apex[1], base[1]], (200, 205, 212))
    c.line([(x + px * 125, y + py * 125), (x - px * 125, y - py * 125)], (255, 150, 60), 30)
    c.ell(x + nx * 110, y + ny * 110, 18, fill=(60, 90, 120))


def sun(c, x, y, r, T):
    c.glow(x, y, r * 2.4, r * 2.4, (255, 190, 80), 0.9)
    c.ell(x, y, r, fill=(255, 210, 90))
    for i in range(12):
        a = i * math.pi / 6 + T * 0.2
        c.line([(x + math.cos(a) * r * 1.15, y + math.sin(a) * r * 1.15), (x + math.cos(a) * r * 1.4, y + math.sin(a) * r * 1.4)], (255, 210, 90), 10)


def coffee(c, x, y, k=1.0, T=0):
    c.rect(x - 34 * k, y - 50 * k, x + 34 * k, y + 20 * k, fill=(240, 240, 236), r=10 * k)
    c.arc(x + 40 * k, y - 18 * k, 20 * k, -90, 90, (240, 240, 236), 8 * k)
    c.rect(x - 28 * k, y - 46 * k, x + 28 * k, y - 36 * k, fill=(110, 70, 40), r=4 * k)
    for i in range(2):
        pts = [(x - 10 * k + i * 20 * k + math.sin(T * 3 + j + i) * 6 * k, y - 60 * k - j * 14 * k) for j in range(5)]
        c.line(pts, (200, 210, 220), 4 * k)


def xmark(c, x, y, r, p=1.0):
    if p <= 0: return
    r *= min(1.0, p)
    c.line([(x - r, y - r), (x + r, y + r)], RED, 18); c.line([(x - r, y + r), (x + r, y - r)], RED, 18)


def check(c, x, y, r, col=(90, 220, 130)):
    c.line([(x - r, y), (x - r * 0.3, y + r * 0.7), (x + r, y - r * 0.8)], col, 18)


def ruler(c, x, y0, y1, label, p=1.0):
    if p <= 0: return
    yt = lerp(y0, y1, min(1, p))
    c.line([(x, y0), (x, yt)], YEL, 6); c.line([(x - 20, y0), (x + 20, y0)], YEL, 6); c.line([(x - 20, yt), (x + 20, yt)], YEL, 6)
    tag(c, label, x + 120, (y0 + yt) / 2, p, 40)


# ------------------------------------------------------------------ scènes
def s_room(c, T, t):
    if T > 8.56:
        g = ease((T - 8.56) / 1.0)
        c.glow(1000, 560, 330 * g, 330 * g, (90, 200, 255), 0.7)
        particles(c, 1000, 700, 18, T, 1, spread=260, rise=420, size=7)
    me(c, 1000, T, 1.0, mood='sleep' if T > 5.52 else 'happy', arms=('hold', 'hold') if T > 8.56 else ('down', 'down'),
       glowchest=(90, 200, 255) if T > 8.56 else None)


def s_countdown(c, T, t):
    left = max(0, 10 - (T - 10.0) * 1.3)
    stopwatch(c, 1300, 420, 200, left / 10, RED, str(int(math.ceil(left))))
    me(c, 560, T, 1.0, mood='scared' if T > 11.3 else 'worry', arms=('cover', 'cover') if T > 12.4 else ('down', 'down'), tremble=4 if T > 11.4 else 0)


def s_physics(c, T, t):
    if T < 19.76:
        c.glow(1320, 420, 260, 260, (150, 60, 200), 0.5)
        c.poly([(1180, 700), (1240, 380), (1320, 330), (1400, 380), (1460, 700)], (30, 20, 40))
        c.ell(1320, 300, 70, fill=(30, 20, 40)); c.poly([(1270, 260), (1280, 200), (1300, 250)], (30, 20, 40)); c.poly([(1370, 260), (1360, 200), (1340, 250)], (30, 20, 40))
        c.ell(1295, 300, 10, fill=RED); c.ell(1345, 300, 10, fill=RED)
        xmark(c, 1320, 470, 170, at(T, 17.0))
        me(c, 620, T, 1.0, mood='calm', arms=('shrug', 'shrug'))
    else:
        p = at(T, 19.76, 0.5); c.glow(1300, 420, 300 * p, 300 * p, CYAN, 0.6)
        for k in range(3):
            a = math.radians(60 * k + T * 40)
            c.d.ellipse([(1300 - 210 * p) * S, (420 - 70 * p) * S, (1300 + 210 * p) * S, (420 + 70 * p) * S], outline=CYAN, width=int(6 * S)) if k == 0 else None
            pts = [(1300 + math.cos(u) * 210 * p * math.cos(a) - math.sin(u) * 70 * p * math.sin(a),
                    420 + math.cos(u) * 210 * p * math.sin(a) + math.sin(u) * 70 * p * math.cos(a)) for u in [i * 0.2 for i in range(33)]]
            c.line(pts, CYAN, 6, cap=False)
            u = T * 4 + k * 2
            c.ell(1300 + math.cos(u) * 210 * p * math.cos(a) - math.sin(u) * 70 * p * math.sin(a),
                  420 + math.cos(u) * 210 * p * math.sin(a) + math.sin(u) * 70 * p * math.cos(a), 14, fill=WHITE)
        c.ell(1300, 420, 38 * p, fill=YEL)
        me(c, 620, T, 1.0, mood='happy', arms=('point', 'down'))


def s_cinema(c, T, t):
    c.rect(360, 140, 1560, 700, fill=(20, 26, 34), r=18, outline=(90, 110, 120), w=8)
    c.rect(390, 170, 1530, 670, fill=(40, 96, 140), r=8)
    for cx in (600, 1200): c.ell(cx, 300, 120, 40, fill=(200, 220, 230))
    character(c, 700 + (T - 22.16) * 220, 520, 0.55, dict(legs='fly', arms=('fly', 'fly'), mood='happy', shadow=False, rot=-1.2), T)
    if T > 24.48:
        p = ease((T - 24.48) / 0.5); y = lerp(-400, 160, p)
        c.rect(1180, y, 1520, y + 470, fill=(236, 236, 230), r=8)
        c.text(1350, y + 70, 'FACTURE', 54, (40, 40, 40))
        for i in range(5): c.rect(1220, y + 140 + i * 48, 1480 - (i % 2) * 60, y + 158 + i * 48, fill=(190, 190, 186), r=4)
        c.text(1350, y + 420, 'TOTAL : ???', 40, RED)


def s_gauges(c, T, t):
    bad = ease((T - 39.6) / 0.8)
    G = [(330, 330, 'PRESSION', 32.96), (720, 190, 'GRAVITÉ', 34.48), (1200, 190, 'VITESSE', 35.84), (1590, 330, 'ÉLECTRICITÉ', 37.2)]
    c.glow(960, 470, 300, 260, mix(CYAN, RED, bad), 0.25)
    for i, (x, y, lab, t0) in enumerate(G):
        p = at(T, t0)
        if p <= 0.02: continue
        v = 0.45 + 0.05 * math.sin(T * 2 + i) + bad * (0.5 if i % 2 else -0.4)
        gauge(c, x, y, 100 * min(1, p), max(0, min(1, v)), lab, ok=bad < 0.5)
    if T < 30.0:
        c.rect(700, 210, 1220, 560, outline=CYAN, w=6, r=20)
    fall = ease((T - 42.4) / 0.6)
    me(c, 960, T, 0.95, mood='ko' if T > 42.4 else ('scared' if bad > 0.3 else 'calm'), tremble=6 * bad * (1 - fall),
       rot=-1.35 * fall, arms=('flail', 'flail') if bad > 0.3 else ('down', 'down'))
    if fall > 0: dust(c, 960, GY, fall)


def s_lineup(c, T, t):
    kinds = [('giant', 'N°5'), ('fly', 'N°4'), ('speed', 'N°3'), ('elec', 'N°2'), ('portal', 'N°1')]
    for i, (k, lab) in enumerate(kinds):
        p = at(T, 45.08 + i * 0.35)
        if p <= 0.02: continue
        hi = ease((T - 56.4) / 0.6) if i == 4 else 0.0
        x = 240 + i * 360; y = 420 - 40 * hi
        if i == 4 and T > 60.56: x += 8 * math.sin(T * 60) * max(0, 1 - (T - 60.56))
        dim = 0.55 if (T > 56.4 and i != 4) else 1.0
        card(c, x, y, 300 * min(1, p) * (1 + 0.15 * hi), 420 * min(1, p) * (1 + 0.15 * hi), lab, k, T, hi)
        if dim < 1: c.rect(x - 150, y - 210, x + 150, y + 210, fill=None)
    if T > 59.0:
        tag(c, '?', 1680, 120, at(T, 59.0), 90, RED)
    if T > 60.56:
        tag(c, 'LE PIÈGE', 1680, 700, at(T, 61.16), 50, RED)


# --- section 1 : géant
def s_title(num, txt):
    def f(c, T, t): title_card(c, num, txt, t)
    return f


def s_grow(c, T, t):
    g = back((T - 7.12) / 1.6); s = 0.55 + 1.0 * max(0, g)
    if T < 7.12 and T > 3.28:
        c.glow(960, 640, 240, 240, (90, 200, 255), 0.6); particles(c, 960, 760, 12, T, 2, spread=180, rise=300)
    info = me(c, 960, T, s, mood='happy', arms=('up', 'up') if T > 7.1 else ('down', 'down'))
    tag(c, '× 10', 1420, 300, at(T, 9.04), 70)
    if T > 10.48:
        ruler(c, 1240, GY, info['head'][1] - 60 * s, '≈ 17 M', ease((T - 10.48) / 0.8))
    if T > 13.68: tag(c, '5 ÉTAGES', 1420, 520, at(T, 13.68), 40, CYAN)


def s_view(c, T, t):
    eiffel(c, 1560, GY, 360, (30, 52, 66))
    me(c, 760, T, 1.55, mood='worry' if T > 18.3 else 'happy', look=(7, 1), tremble=3 if T > 19.3 else 0)
    if T > 19.3: bubble(c, '?', 470, 160, at(T, 19.3), 70, tail=1)


def s_cube(c, T, t):
    me(c, 230, T, 0.6, mood='shock' if T > 31.6 else 'calm', look=(6, 0))
    iso(c, 560, 560, 1, 1, 1, 30)
    tag(c, '×1', 560, 640, 1, 36, CYAN)
    a = 1 + 9 * ease((T - 23.6) / 1.2); h = 1 + 9 * ease((T - 27.0) / 1.0); b = 1 + 9 * ease((T - 28.3) / 1.0)
    iso(c, 1230, 760, a, b, h, 30, (230, 160, 70))
    tag(c, 'TAILLE ×10', 1650, 320, at(T, 23.6), 40, CYAN)
    if T > 31.12: tag(c, 'VOLUME ×1 000', 1250, 140, at(T, 31.68), 64, YEL)


def s_bone(c, T, t):
    # balance
    tilt = 0.32 * ease((T - 38.5) / 1.0)
    c.rect(950, 380, 970, 760, fill=GREY, r=6); c.poly([(900, 780), (1020, 780), (960, 740)], GREY)
    L = 520; ax, ay = 960, 380
    lx, ly = ax - L * math.cos(tilt), ay + L * math.sin(tilt); rx, ry = ax + L * math.cos(tilt), ay - L * math.sin(tilt)
    c.line([(lx, ly), (rx, ry)], GREY, 14)
    for px, py, lab, col, ww in ((lx, ly, 'POIDS ×1 000', RED, 150), (rx, ry, 'SOLIDITÉ ×100', CYAN, 90)):
        c.line([(px, py), (px - 110, py + 160)], GREY, 4); c.line([(px, py), (px + 110, py + 160)], GREY, 4)
        c.rect(px - 140, py + 160, px + 140, py + 180, fill=GREY, r=6)
        c.rect(px - ww / 2, py + 160 - ww * 0.8, px + ww / 2, py + 160, fill=col, r=10)
        tag(c, lab, px, py + 240, at(T, 35.0 if col == RED else 38.56), 36, col)
    # os
    p = at(T, 34.4)
    if p > 0:
        c.ell(960, 210, 90 * min(1, p), fill=(236, 230, 214)); c.ell(960, 210, 50 * min(1, p), fill=(196, 160, 120))
        tag(c, 'SECTION DE L\'OS', 960, 70, p, 34, WHITE)
    if T > 40.36: tag(c, '×10 DE CHARGE', 1580, 120, at(T, 40.36), 50, RED)


def s_galileo(c, T, t):
    galileo(c, 620, T, 1.0)
    tag(c, 'GALILÉE · 1638', 1280, 220, at(T, 46.3), 56, YEL)
    if T > 45.2: tag(c, 'LOI DU CARRÉ-CUBE', 1280, 360, at(T, 45.2), 46, CYAN)
    if T > 49.5:
        p = ease((T - 49.5) / 1.5)
        for i in range(3):
            k = 0.4 + i * 0.35 * p
            c.rect(1120 + i * 150 - 10 * k, 700 - 160 * k, 1120 + i * 150 + 10 * k, 700, fill=(236, 230, 214), r=4)
            c.ell(1120 + i * 150, 700 - 160 * k, 16 * k + 6, fill=(236, 230, 214))


def s_elephant(c, T, t):
    elephant(c, 820, GY, 1.4, T * 2)
    for lx in (-110, 110):
        c.line([(820 + lx * 1.4 - 70, 560), (820 + lx * 1.4 - 70, 760)], YEL, 6)
    tag(c, 'PATTES = COLONNES', 1420, 220, at(T, 54.3), 48)


def s_whale(c, T, t):
    whale(c, 960, 520, 1.25, T)
    if T > 60.4:
        p = ease((T - 60.4) / 0.6)
        for i in range(5):
            x = 620 + i * 170; c.line([(x, 860), (x, 860 - 140 * p)], CYAN, 10); c.poly([(x - 26, 860 - 140 * p), (x + 26, 860 - 140 * p), (x, 820 - 140 * p)], CYAN)
        tag(c, 'L\'EAU PORTE SON POIDS', 960, 140, p, 54)
    tag(c, 'BALEINE BLEUE', 400, 140, at(T, 58.6), 42, CYAN)


def s_air(c, T, t):
    me(c, 960, T, 1.45, mood='worry')
    for i in range(4):
        x = 560 + i * 270; y = 200 + 20 * math.sin(T * 6 + i)
        c.line([(x, y), (x, y + 120)], RED, 10); c.poly([(x - 26, y + 120), (x + 26, y + 120), (x, y + 160)], RED)
    tag(c, 'DANS L\'AIR', 1600, 150, at(T, 63.4), 46, RED)


def s_collapse(c, T, t):
    kn = ease((T - 66.0) / 0.5); fall = ease((T - 67.36) / 1.2)
    info = me(c, 900, T, 1.45, mood='hurt' if T > 64.3 else 'worry', knee=kn * 0.8, rot=-1.35 * fall,
              arms=('flail', 'flail') if fall > 0 else ('down', 'down'), tremble=4 if T < 67.3 else 0)
    if T > 64.3 and fall < 0.3:
        for kx, ky in info['knees']:
            c.glow(kx, ky, 60, 60, RED, 0.9)
            c.line([(kx - 20, ky - 30), (kx + 10, ky - 6), (kx - 14, ky + 8), (kx + 18, ky + 30)], (255, 200, 170), 4)
    if fall > 0.95: dust(c, 900, GY, ease((T - 68.5) / 1.0))
    if T > 68.6: tag(c, 'CHUTE DE 17 M', 1520, 180, at(T, 68.8), 50, RED)


def s_heart(c, T, t):
    if T < 74.52:
        beat = 1 + 0.08 * max(0, math.sin(T * 8))
        heart(c, 700, 460, 150, beat)
        p = ease((T - 73.36) / 0.6)
        c.line([(1100, 720), (1100, 720 - 560 * p)], RED, 14)
        c.poly([(1060, 720 - 560 * p), (1140, 720 - 560 * p), (1100, 660 - 560 * p)], RED)
        tag(c, '×10 PLUS HAUT', 1440, 360, at(T, 73.4), 50, RED)
    else:
        h = ease((T - 76.0) / 2.5)
        c.glow(800, 500, 300, 360, mix(HOOD, RED, h), 0.4 + 0.5 * h)
        me(c, 800, T, 1.1, mood='worry' if h < 0.6 else 'shock', col=mix(HOOD, (220, 50, 40), h), glowchest=RED if h > 0.3 else None)
        thermometer(c, 1400, 700, 440, h, 'CHALEUR' if T > 77.28 else None)
        particles(c, 800, 400, 10, T, 4, col=(255, 140, 80), spread=150, rise=260)


def s_end1(c, T, t):
    if T < 83.6:
        c.glow(960, 700, 500, 140, RED if T > 81.7 else (60, 80, 90), 0.5)
        me(c, 760, T, 1.45, mood='ko', rot=-1.45, shadow=False)
        particles(c, 960, 640, 14, T, 6, col=(220, 220, 220), spread=420, rise=300, size=10)
        tag(c, 'ÉCRASÉ…', 640, 200, at(T, 80.64), 50, RED)
        if T > 81.72: tag(c, '…OU CUIT', 1260, 200, at(T, 81.72), 50, RED)
    else:
        sh = 1.45 - 0.55 * ease((T - 83.6) / 0.8)
        me(c, 960, T, sh, mood='happy' if T < 85.5 else 'calm', look=(0, -6) if T > 85.56 else (3, 2), arms=('down', 'down'))
        if T > 87.6: bubble(c, 'Et si je volais ?', 1350, 260, at(T, 87.84), 46)


# --- section 2 : voler
def s_takeoff(c, T, t):
    p = ease((T - 4.88) / 7.0)
    c.d.rectangle([0, 0, W * S, H * S], fill=None)
    eh = 640 * (1 - 0.7 * p); eb = GY + 700 * p
    eiffel(c, 960 + 300, eb, eh, (28, 46, 60))
    for i in range(4):
        x = (i * 520 + T * 60) % (W + 400) - 200; y = 900 - p * 900 + i * 140
        c.ell(x, y, 160, 46, fill=(200, 220, 232))
    me(c, 760, T, 0.9, gy=GY - 520 * p, legs='fly' if T > 5.0 else 'stand', arms=('fly', 'fly') if T > 5.0 else ('down', 'down'), mood='happy2', shadow=T < 5.2)


def s_alti(c, T, t):
    km = 1 + 7 * ease((T - 12.6) / 5.8)
    me(c, 860, T, 0.9, gy=760 + 20 * math.sin(T * 2), legs='fly', arms=('fly', 'fly'), mood='happy' if km < 4 else 'cold', tremble=2 if km > 5 else 0, shadow=False)
    c.rect(1450, 160, 1650, 700, fill=(16, 26, 36), r=20, outline=GREY, w=4)
    c.rect(1520, 690 - 520 * (km / 10), 1580, 690, fill=CYAN, r=8)
    c.text(1550, 120, f'{km:.1f} KM'.replace('.', ','), 50, WHITE)
    thermometer(c, 300, 700, 440, max(0, 0.7 - (km - 1) * 0.1), f'{15 - 6.5 * (km - 1):.0f} °C')
    if T > 14.8: tag(c, '−6,5 °C PAR KM', 960, 160, at(T, 14.8), 50)


def s_everest(c, T, t):
    if T < 27.08:
        me(c, 1300, T, 0.9, gy=420, legs='fly', arms=('cross', 'cross'), mood='cold', tremble=4, shadow=False)
        tag(c, '8 KM', 560, 160, at(T, 18.6), 60, WHITE)
        if T > 21.6: tag(c, '−30 °C', 560, 300, at(T, 21.6), 56, CYAN)
        if T > 23.68: tag(c, 'PRESSION ÷ 3', 1460, 120, at(T, 23.8), 50, YEL)
    else:
        for i, colr in enumerate(((60, 110, 220), (70, 160, 90))):
            character(c, 880 + i * 160, 300, 0.55, dict(col=colr, hair=(240, 240, 240), arms=('up', 'hip') if i == 0 else ('hip', 'up'), mood='happy2', shadow=False), T)
        c.line([(1110, 300), (1110, 120)], GREY, 6); c.poly([(1110, 120), (1210, 150), (1110, 180)], RED)
        tag(c, '1978', 520, 200, at(T, 28.08), 80, YEL)
        tag(c, 'SANS OXYGÈNE', 520, 340, at(T, 34.5), 44, CYAN)
        if T > 36.2: tag(c, 'DES SEMAINES', 1500, 520, at(T, 37.9), 46, WHITE)
        if T > 38.88:
            p = ease((T - 38.88) / 1.5)
            character(c, lerp(-200, 1500, p), 640 - 300 * p, 0.6, dict(legs='fly', arms=('fly', 'fly'), mood='happy', shadow=False, rot=-0.9), T)
            tag(c, 'TOI : QUELQUES MINUTES', 960, 960 - 100, at(T, 40.5), 46, RED) if False else None


def s_plane(c, T, t):
    if T < 45.32:
        plane(c, lerp(2200, -300, (T - 42.0) / 3.3), 420, 1.2)
        tag(c, '11 KM', 960, 160, at(T, 42.1), 70)
    else:
        c.rect(300, 120, 1620, 760, fill=(40, 50, 60), r=30)
        c.rect(340, 160, 1580, 720, fill=(26, 34, 44), r=20)
        for i in range(4):
            x = 520 + i * 300; d = ease((T - 46.12 - i * 0.12) / 0.5)
            if d > 0:
                y = 160 + 240 * d + 10 * math.sin(T * 5 + i)
                c.line([(x, 160), (x, y)], GREY, 3, cap=False)
                c.ell(x, y + 30, 46, 36, fill=(250, 210, 60))
        if T > 48.6: stopwatch(c, 1420, 560, 110, max(0, 1 - (T - 48.6) / 6), RED, None)
        if T > 48.6: tag(c, 'QUELQUES DIZAINES DE SECONDES', 760, 820 - 60, at(T, 48.9), 40, RED)
        if T > 52.0: tag(c, 'TEMPS DE CONSCIENCE UTILE', 960, 90, at(T, 52.2), 44, YEL)


def s_blur(c, T, t):
    me(c, 960, T, 1.0, gy=760, legs='fly', arms=('fly', 'down'), mood='worry' if T < 58.0 else 'sleep', shadow=False)
    xmark(c, 1400, 300, 90, at(T, 55.6))
    c.rect(1310, 270, 1490, 330, fill=None)
    c.ell(1400, 300, 70, 50, fill=(250, 210, 60))


def s_armstrong(c, T, t):
    y = 430
    for x in range(0, W, 60): c.line([(x, y), (x + 34, y)], RED, 6, cap=False)
    tag(c, 'LIMITE D\'ARMSTRONG · 19 KM', 1450, y - 60, at(T, 62.3), 44, RED)
    rise = ease((T - 62.1) / 3.0)
    info = me(c, 960, T, 0.85, gy=900 - 380 * rise, legs='fly', arms=('fly', 'fly') if T < 73 else ('cover', 'cover'), mood='worry' if T < 72.8 else 'scared', shadow=False)
    if T > 72.88:
        hx, hy, r = info['head']
        particles(c, hx, hy + 40, 24, T, 8, col=(200, 240, 255), spread=110, rise=200, size=9)
        thermometer(c, 300, 820, 300, 0.45, '37 °C')
        tag(c, 'L\'EAU BOUT', 1560, 640, at(T, 73.36), 50, CYAN)


def s_blood(c, T, t):
    c.rect(200, 380, 1720, 560, fill=(120, 20, 30), r=90)
    c.rect(220, 400, 1700, 540, fill=(200, 40, 50), r=70)
    for i in range(14):
        x = (200 + i * 120 + T * 160) % 1500 + 220
        c.ell(x, 470 + 30 * math.sin(i), 30, 20, fill=(240, 90, 90))
    for x in (500, 960, 1420):
        c.line([(x, 280), (x, 370)], YEL, 8); c.poly([(x - 20, 370), (x + 20, 370), (x, 395)], YEL)
        c.line([(x, 660), (x, 575)], YEL, 8); c.poly([(x - 20, 575), (x + 20, 575), (x, 550)], YEL)
    tag(c, 'LE SANG RESTE LIQUIDE', 960, 170, at(T, 80.9), 54)
    xmark(c, 960, 470, 220, at(T, 85.2))


def s_drift(c, T, t):
    p = ease((T - 86.56) / 7.0)
    me(c, 960 + 60 * math.sin(T * 0.6), T, 0.8 - 0.3 * p, gy=760 - 340 * p, legs='fly', arms=('down', 'fly'), mood='sleep', rot=0.25 * math.sin(T * 0.5), shadow=False)
    brain(c, 1500, 260, 0.9, 1 - ease((T - 88.5) / 1.0))
    if T > 91.8: tag(c, 'INCONSCIENT', 520, 200, at(T, 91.8), 52, RED)


def s_ground(c, T, t):
    k = ease((T - 96.2) / 0.5)
    if T > 97.44: speedlines(c, T, 10)
    me(c, 960, T, 1.0, mood='determined', knee=0.35 * k, arms=('run_f', 'run_b') if k > 0.5 else ('down', 'down'), rot=0.25 * k)


# --- section 3 : vitesse
def s_bolt(c, T, t):
    if T < 13.6:
        speedlines(c, T, 12)
        character(c, 960, GY, 1.0, dict(legs='run', phase=T * 16, arms=('run_f', 'run_b'), col=(60, 110, 220), hair=(30, 30, 30), mood='determined', rot=0.18), T)
        tag(c, '9,58 S', 400, 220, at(T, 6.4), 80)
        if T > 8.08: tag(c, 'BERLIN · 2009', 400, 360, at(T, 8.08), 44, CYAN)
        if T > 11.68: tag(c, '≈ 45 KM/H', 1520, 220, at(T, 11.68), 64, YEL)
    else:
        character(c, 1300, GY, 0.85, dict(col=(60, 110, 220), hair=(30, 30, 30), mood='shock', look=(-6, 1)), T)
        me(c, 620, T, 1.0, mood='determined', knee=0.3, arms=('run_f', 'run_b'), rot=0.25)
        tag(c, 'BEAUCOUP MIEUX', 620, 140, at(T, 15.68), 50)


def s_accel(c, T, t):
    speedlines(c, T, 24)
    sq = ease((T - 26.3) / 0.6)
    me(c, 760, T, 1.0, legs='run', phase=T * 22, arms=('run_f', 'run_b'), mood='scared' if sq > 0 else 'determined', rot=0.3)
    tag(c, 'ACCÉLÉRATION', 760, 120, at(T, 20.48), 56, YEL)
    if T > 26.27: tag(c, '34 G', 1450, 240, at(T, 26.3), 110, RED)
    if T > 28.56:
        p = ease((T - 28.56) / 0.4); r = 170
        c.ell(1450, 600, r + 20, fill=(16, 24, 32), outline=GREY, w=5)
        sqz = 1 - 0.35 * ease((T - 29.36) / 1.0)
        for i in range(5):
            c.arc(1450, 600 - 80 + i * 36, 110 * sqz, 200, 340, (230, 226, 214), 10)
        c.rect(1444, 470, 1456, 730, fill=(230, 226, 214))
        tag(c, 'CÔTES COMPRIMÉES', 1450, 840 - 20, p, 36, RED)


def s_stapp(c, T, t):
    if T < 38.96:
        sled(c, 900, GY, T, 0.0)
        tag(c, '1954', 400, 180, at(T, 32.9), 80)
        if T > 36.24: tag(c, 'JOHN PAUL STAPP', 1400, 180, at(T, 36.3), 50, CYAN)
    elif T < 41.41:
        p = (T - 38.96) / 2.45
        speedlines(c, T, 16)
        sled(c, lerp(200, 1500, p), GY, T, 1.0)
    else:
        p = ease((T - 41.41) / 0.4)
        x = lerp(1500, 1600, p)
        info = sled(c, 1060, GY, T, 0.0)
        dust(c, 1260, GY, ease((T - 41.4) / 1.2), col=(170, 134, 96))
        tag(c, '46 G', 520, 200, at(T, 43.64), 110, RED)
        if T > 46.96:
            hx, hy, r = info['head']
            c.glow(hx, hy, 70, 50, RED, 0.6)
            tag(c, 'VAISSEAUX ÉCLATÉS', 520, 380, at(T, 47.1), 40, RED)
        if T > 51.36: tag(c, 'UNE FRACTION DE SECONDE', 1300, 140, at(T, 52.3), 40, YEL)


def s_mach(c, T, t):
    v = min(1.0, (T - 54.16) / 5.5)
    speedlines(c, T * (1 + v), int(14 + 20 * v))
    if T > 64.0:
        h = ease((T - 64.0) / 5.0)
        c.glow(1260, 560, 160 + 160 * h, 300, mix((255, 160, 60), RED, h), 0.4 + 0.5 * h)
        for i in range(6):
            yy = 330 + i * 70; c.arc(1180 - 40 * h, yy + 60, 140, -50, 50, mix((255, 200, 120), RED, h), 6)
    me(c, 900, T, 1.0, legs='run', phase=T * 26, arms=('run_f', 'run_b'), mood='determined' if T < 64 else 'scared', rot=0.35)
    gauge(c, 260, 200, 110, min(1, (T - 54.16) / 5.5), f'{int(1200 * min(1, (T - 54.16) / 5.5))} KM/H', ok=True)
    if 59.84 < T < 63.9:
        p = (T - 59.84) / 1.2
        c.ell(1000, 520, 300 + 900 * min(p, 1.5), 260 + 700 * min(p, 1.5), outline=mix(WHITE, (40, 60, 70), min(1, p)), w=10)
        tag(c, 'BANG !', 1500, 200, at(T, 60.8), 90, YEL)
        for k in range(20):
            r = random.Random(k); a = r.uniform(0, 6.28); dd = (T - 60.8) * r.uniform(300, 700)
            if dd > 0: c.poly([(1000 + math.cos(a) * dd, 500 + math.sin(a) * dd), (1020 + math.cos(a) * dd, 520 + math.sin(a) * dd), (990 + math.cos(a) * dd, 530 + math.sin(a) * dd)], (180, 230, 255))
    if T > 67.6: tag(c, 'L\'AIR SE COMPRIME', 1460, 160, at(T, 67.6), 46, YEL)
    if T > 70.08: tag(c, 'IL CHAUFFE', 1460, 280, at(T, 70.08), 46, RED)


def s_capsule(c, T, t):
    capsule(c, 1060 + 30 * math.sin(T), 460, T, 0.8 + 0.2 * math.sin(T * 9))
    tag(c, 'APOLLO', 380, 180, at(T, 75.5), 60)
    if T > 77.8: tag(c, '+2 500 °C', 380, 330, at(T, 77.8), 80, RED)


def s_tshirt(c, T, t):
    c.glow(960, 520, 360, 380, (255, 120, 40), 0.55)
    me(c, 960, T, 1.1, mood='shock', col=(250, 130, 60), glowchest=(255, 160, 80), tremble=3)
    tag(c, 'TON BOUCLIER : UN TEE-SHIRT', 960, 120, at(T, 80.0), 52, RED)


def s_heart_tease(c, T, t):
    b = 1 + 0.1 * max(0, math.sin(T * 6)) ** 8
    c.glow(960, 450, 400, 400, RED, 0.45)
    heart(c, 960, 450, 180, b)


# --- section 4 : électricité
def s_zap(c, T, t):
    info = me(c, 620, T, 1.0, mood='determined', arms=('point', 'point'))
    for i, h in enumerate(info['hands']):
        bolt(c, h[0], h[1], 1700, 200 + i * 400, int(T * 15) + i, amp=45)


def s_eel(c, T, t):
    eel(c, 1060, 560, T, 1.2, 0.3 + 0.4 * (T > 17.0))
    if T > 9.64:
        p = at(T, 9.64)
        for i in range(6):
            c.rect(220, 640 - i * 70, 380, 690 - i * 70, fill=(60, 70, 80), r=8)
            c.rect(220, 640 - i * 70, 380 * 0 + 220 + 160 * min(1, p), 690 - i * 70, fill=(90, 210, 120), r=8)
        tag(c, 'COMME DES PILES', 300, 240, p, 36, CYAN)
    if T > 13.76: tag(c, '2019', 1600, 180, at(T, 13.8), 60)
    if T > 18.48:
        tag(c, '860 V', 960, 180, at(T, 18.5), 110, YEL)
        bolt(c, 900, 600, 1300, 300, int(T * 12), amp=30)


def s_shield(c, T, t):
    c.rect(140, 300, 860, 760, fill=(10, 50, 80), r=20, outline=GREY, w=5)
    eel(c, 640, 520, T, 0.6, 0.4)
    c.ell(500, 530, 330, 150, outline=(140, 230, 255), w=4)
    me(c, 1380, T, 1.0, mood='worry' if T < 25.5 else 'shock', look=(-6, 0))
    if T > 25.56: tag(c, '?', 1600, 220, at(T, 25.9), 110, YEL)
    if T > 23.28: tag(c, 'CORPS ADAPTÉ', 500, 240, at(T, 23.6), 40, CYAN)


def s_body(c, T, t):
    if T < 39.24:
        info = me(c, 960, T, 1.15, mood='calm', arms=('shrug', 'shrug'))
        hx, hy, r = info['head']
        for i, tgt in enumerate(info['hands'] + [info['knees'][0], info['knees'][1]]):
            u = (T * 1.2 + i * 0.25) % 1
            c.line([(hx, hy), tgt], (80, 180, 220), 3, cap=False)
            c.glow(lerp(hx, tgt[0], u), lerp(hy, tgt[1], u), 30, 30, (150, 240, 255), 0.9)
        tag(c, 'TON CORPS EST ÉLECTRIQUE', 960, 100, at(T, 32.6), 50)
    else:
        b = 1 + 0.1 * max(0, math.sin(T * 7)) ** 6
        heart(c, 900, 470, 210, b)
        nx, ny = 1010, 330
        c.glow(nx, ny, 70, 70, YEL, 0.6 + 0.4 * math.sin(T * 7)); c.ell(nx, ny, 16, fill=YEL)
        pr = (T * 0.9) % 1
        c.ell(nx, ny, 40 + 260 * pr, outline=mix(YEL, (40, 50, 60), pr), w=5)
        tag(c, 'NŒUD SINUSAL', 1460, 240, at(T, 42.1), 56, YEL)


def s_current(c, T, t):
    chaos = ease((T - 63.6) / 1.5)
    clench = T > 52.6
    info = me(c, 700, T, 1.1, mood='determined' if T < 52 else ('shock' if T < 66 else 'hurt'), arms=('tense', 'tense') if clench else ('point', 'point'), tremble=5 if clench else 0)
    if T > 47.84:
        for i, h in enumerate(info['hands']):
            bolt(c, h[0], h[1], info['chest'][0], info['chest'][1], int(T * 14) + i, amp=20, seg=5)
    if T > 51.08: c.glow(info['chest'][0], info['chest'][1], 160, 160, (150, 220, 255), 0.6 + 0.3 * math.sin(T * 20))
    if T > 53.36: tag(c, 'MUSCLES BLOQUÉS', 700, 110, at(T, 53.4), 46, CYAN)
    if T > 58.88:
        ecg(c, 1420, 470, 600, 300, T, chaos)
        if T > 68.56: tag(c, 'FIBRILLATION', 1420, 720, at(T, 68.6), 54, RED)


def s_faint(c, T, t):
    f = ease((T - 71.0) / 1.2)
    me(c, 760, T, 1.1, mood='sleep' if f > 0.3 else 'worry', rot=-1.35 * f)
    if f > 0.9: dust(c, 760, GY, ease((T - 72.2) / 1.0))
    brain(c, 1400, 360, 1.0, 1 - ease((T - 71.4) / 1.4))
    if T > 73.36: tag(c, '≈ 10 SECONDES', 1400, 640, at(T, 73.4), 56, RED)


def s_defib(c, T, t):
    aed(c, 1300, 420, 1.2)
    me(c, 620, T, 1.0, mood='happy' if T > 79 else 'calm', arms=('point', 'down'))
    if 78.08 < T < 79.8: bolt(c, 1300, 420, 760, 520, int(T * 20), amp=40)
    if T > 80.32: tag(c, 'DÉFIBRILLATEUR', 1300, 120, at(T, 80.4), 56, (90, 220, 130))
    if T > 82.6: tag(c, 'GARES · MAIRIES · SALLES DE SPORT', 1050, 760 + 60, at(T, 82.9), 36, WHITE)


def s_saves(c, T, t):
    bolt(c, 960, 160, 960, 760, int(T * 10), amp=50)
    tag(c, 'TE TUE', 520, 460, at(T, 86.4), 80, RED)
    tag(c, 'TE SAUVE', 1400, 460, at(T, 88.4), 80, (90, 220, 130))


def s_tease1(c, T, t):
    icon(c, 'portal', 960, 430, 2.0, T)
    tag(c, 'N°1', 960, 760, at(T, 89.4), 70, YEL)


# --- section 5 : téléportation
def s_popular(c, T, t):
    for i in range(7):
        character(c, 240 + i * 240, GY - (i % 2) * 20, 0.55, dict(col=[(60, 110, 220), HOOD, (70, 160, 90), (170, 90, 200), (220, 70, 70), (230, 180, 50), (60, 170, 170)][i],
                                                               arms=('up', 'up') if (T * 2 + i) % 2 > 1 else ('up', 'down'), mood='happy2'), T)
    tag(c, 'LE PLUS CHOISI', 960, 170, at(T, 3.6), 64)


def s_nomore(c, T, t):
    items = [(420, 'car', 6.0), (960, 'ticket', 7.2), (1500, 'plane', 8.4)]
    for x, k, t0 in items:
        p = at(T, t0)
        if p <= 0.02: continue
        if k == 'car': car(c, x, 520, 1.2 * min(1, p))
        elif k == 'ticket':
            c.rect(x - 160 * min(1, p), 380, x + 160 * min(1, p), 560, fill=(236, 230, 210), r=12)
            c.text(x, 470, 'TGV', 60 * min(1, p), (60, 60, 60))
        else: plane(c, x, 470, 0.6 * min(1, p))
        xmark(c, x, 470, 130, at(T, t0 + 0.4))


def s_map(c, T, t):
    globe(c, 960, 460, 330, 0.4)
    c.ell(840, 300, 14, fill=RED); c.text(840, 260, 'PARIS', 36, WHITE)
    c.d.arc([(560) * S, (180) * S, (1500) * S, (900) * S], 200, 330, fill=YEL, width=6 * S)
    c.text(1380, 800, 'NOUVELLE-ZÉLANDE', 36, WHITE)
    me(c, 260, T, 0.7, mood='sleep' if T > 12.4 else 'happy')
    if T > 13.76:
        p = (T - 13.76) / 0.5
        if p < 0.4: c.rect(0, 0, W, H, fill=mix((255, 255, 255), (60, 90, 110), p / 0.4))
        tag(c, 'CLAC !', 960, 160, at(T, 13.8), 100, YEL)


def s_quantum(c, T, t):
    for k in range(4):
        y = 560 - k * 4
        c.line([(260, y + k * 10), (1660, y - k * 6)], mix((255, 60, 60), (60, 255, 120), k / 3), 4, cap=False)
    a = (560, 420); b = (1360, 420)
    c.line([a, b], (190, 160, 255), 3, cap=False)
    for (x, y), ph in ((a, 0), (b, 1)):
        g = 0.7 + 0.3 * math.sin(T * 5 + ph * math.pi)
        c.glow(x, y, 120, 120, (190, 150, 255), g); c.ell(x, y, 26, fill=WHITE)
    if T > 21.88: tag(c, 'ÉTAT QUANTIQUE', 960, 200, at(T, 22.9), 50, CYAN)
    if T > 24.84: tag(c, 'INFORMATION ≠ MATIÈRE', 960, 760, at(T, 25.0), 50, YEL)


def s_nobel(c, T, t):
    c.glow(960, 340, 260, 260, YEL, 0.5)
    c.poly([(880, 80), (930, 80), (980, 240), (930, 240)], (60, 100, 200)); c.poly([(1040, 80), (990, 80), (940, 240), (990, 240)], (200, 50, 60))
    c.ell(960, 330, 150, fill=(230, 180, 60)); c.ell(960, 330, 118, fill=(250, 210, 90))
    c.text(960, 310, 'NOBEL', 50, (120, 80, 20)); c.text(960, 370, '2022', 44, (120, 80, 20))
    for i, colr in enumerate(((60, 110, 220), (150, 150, 160), (70, 160, 90))):
        character(c, 560 + i * 400, GY, 0.6, dict(col=colr, hair=(200, 200, 205), mood='happy', shadow=True), T)
    if T > 33.36: tag(c, 'ALAIN ASPECT', 560, 860, at(T, 33.4), 38, YEL)
    if T > 35.2: tag(c, 'ANTON ZEILINGER', 1360, 860, at(T, 35.3), 38, CYAN)


def s_fiction(c, T, t):
    me(c, 960, T, 1.1, mood='calm', arms=('shrug', 'shrug'))
    if T > 42.4:
        p = back((T - 42.5) / 0.25)
        c.rect(1180, 200, 1180 + 520 * min(1.1, p), 340, outline=RED, w=12, r=14)
        c.text(1180 + 260 * min(1.1, p), 270, 'FICTION', 90 * min(1.1, p), RED)


def s_spin(c, T, t):
    globe(c, 960, 570, 300, T * 0.5)
    for i in range(3):
        a = math.radians(200 + i * 30 + T * 30)
        c.arc(960, 570, 370, 200 + i * 40 + T * 20 % 360, 230 + i * 40 + T * 20 % 360, YEL, 8)
    if T > 49.92:
        c.line([(660, 570), (1260, 570)], (255, 255, 255), 3, cap=False)
        tag(c, 'ÉQUATEUR : 1 670 KM/H', 400, 200, at(T, 50.0), 50)
    if T > 54.6:
        c.ell(900, 330, 14, fill=RED)
        tag(c, 'PARIS : 1 100 KM/H', 1520, 300, at(T, 54.7), 46, YEL)
    if T > 58.48:
        info = character(c, 960, 272, 0.45, dict(mood='calm', arms=('hold', 'down'), shadow=False), T)
        h = info['hands'][0]; coffee(c, h[0] - 10, h[1] + 6, 0.5, T)


def s_antipode(c, T, t):
    globe(c, 960, 500, 320, 0.3 + T * 0.05)
    p1 = (820, 300); p2 = (1100, 700)
    c.ell(*p1, 14, fill=RED); c.ell(*p2, 14, fill=YEL)
    c.text(p1[0], p1[1] - 40, 'PARIS', 34, WHITE); c.text(p2[0] + 180, p2[1] + 40, 'ANTIPODES', 34, WHITE)
    if T > 70.0:
        p = ease((T - 70.0) / 0.8)
        c.line([(p1[0], p1[1] - 70), (p1[0] + 240 * p, p1[1] - 70)], RED, 12); c.poly([(p1[0] + 240 * p, p1[1] - 90), (p1[0] + 240 * p, p1[1] - 50), (p1[0] + 280 * p, p1[1] - 70)], RED)
        c.line([(p2[0], p2[1] + 80), (p2[0] - 240 * p, p2[1] + 80)], YEL, 12); c.poly([(p2[0] - 240 * p, p2[1] + 60), (p2[0] - 240 * p, p2[1] + 100), (p2[0] - 280 * p, p2[1] + 80)], YEL)
        tag(c, 'SENS OPPOSÉ', 1560, 180, at(T, 74.6), 50, YEL)
    if T > 75.6:
        c.ell(360, 360, 70, fill=(210, 50, 50)); c.line([(360, 300), (372, 260)], (110, 70, 40), 8); c.ell(395, 275, 22, 12, fill=(90, 170, 80))
        tag(c, '1ʳᵉ LOI DE NEWTON'.replace('ʳᵉ', 'RE'), 360, 520, at(T, 78.5), 40, CYAN)


def s_impact(c, T, t):
    c.d.rectangle([0, (GY - 20) * S, W * S, H * S], fill=(70, 140, 80))
    for i in range(4):
        c.ell(200 + i * 520, GY - 10, 360, 110, fill=(80, 156, 90))
    c.d.rectangle([0, GY * S, W * S, H * S], fill=(64, 128, 74))
    x = (T - 82.21) * 1400 % (W + 600) - 300
    speedlines(c, T, 18, (220, 240, 255), 500, 760)
    character(c, x, GY - 60, 0.8, dict(legs='fly', arms=('fly', 'fly'), mood='scared', rot=-1.45, shadow=False), T)
    for k in range(14):
        r = random.Random(k); dx = r.uniform(40, 700)
        c.ell(x - dx, GY - r.uniform(0, 80), r.uniform(20, 50) * (1 - dx / 800), fill=(130, 100, 70))
    tag(c, '+2 000 KM/H', 520, 180, at(T, 83.5), 90, RED)
    if T > 86.16: tag(c, '≈ 2 × LA VITESSE DU SON', 1340, 180, at(T, 86.3), 46, YEL)


def s_stayfr(c, T, t):
    me(c, 760, T, 1.05, mood='calm', arms=('think', 'hip'))
    bubble(c, 'Je resterai en France.', 1300, 260, at(T, 94.2), 46, tail=-1)


# --- section 6 : retournement
def s_pl(c, T, t):
    france(c, 960, 540, 1.0)
    P = (960, 400); Ly = (1060, 610)
    for (x, y), nm in ((P, 'PARIS'), (Ly, 'LYON')):
        c.glow(x, y, 50, 50, YEL, 0.8); c.ell(x, y, 14, fill=YEL); c.text(x - 110, y - 10, nm, 36, WHITE)
    p = ease((T - 3.64) / 1.2)
    c.line([P, (lerp(P[0], Ly[0], p), lerp(P[1], Ly[1], p))], WHITE, 5)
    tag(c, '≈ 400 KM', 400, 200, at(T, 1.7), 56)
    if T > 3.64: tag(c, '2 H DE TGV', 400, 330, at(T, 4.2), 46, CYAN)
    if T > 7.68:
        q = ease((T - 7.8) / 0.6)
        c.line([(P[0] + 40, P[1]), (P[0] + 40 + 180 * q, P[1])], RED, 10)
        c.line([(Ly[0] + 40, Ly[1]), (Ly[0] + 40 + 200 * q, Ly[1] + 12 * q)], YEL, 10)
    if T > 13.4: tag(c, '≈ 80 KM/H D\'ÉCART', 1500, 860, at(T, 15.8), 56, RED)


def s_crash(c, T, t):
    p = ease((T - 17.44) / 1.0)
    c.rect(1500, 200, 1640, GY, fill=(90, 80, 76), r=6)
    for i in range(8): c.line([(1500, 220 + i * 70), (1640, 220 + i * 70)], (60, 52, 50), 4, cap=False)
    x = lerp(300, 1380, min(1, p))
    hit = T > 18.44
    me(c, x, T, 1.0, mood='ko' if hit else 'shock', rot=0.4 * (1 - min(1, p)) if not hit else -0.1, arms=('flail', 'flail'))
    if hit:
        for k in range(3):
            a = T * 5 + k * 2.1; c.ell(x + math.cos(a) * 80, 380 + math.sin(a) * 20, 12, fill=YEL)
        tag(c, 'BOUM !', 1100, 160, at(T, 18.5), 90, RED)


def s_orbit(c, T, t):
    sun(c, 480, 500, 150, T)
    c.ell(480, 500, 700, 300, outline=(120, 150, 170), w=3)
    a = 0.3 + (T - 21.52) * 0.12
    ex, ey = 480 + math.cos(a) * 700, 500 + math.sin(a) * 300
    globe(c, ex, ey, 90, T)
    character(c, ex, ey - 86, 0.2, dict(mood='calm', shadow=False), T)
    km = int(15000 * ease((T - 23.52) / 4.0))
    if T > 23.52: tag(c, f'{km:,} KM'.replace(',', ' '), 1560, 180, at(T, 23.6), 60, YEL)
    if T > 29.92: tag(c, '107 000 KM/H', 1560, 330, at(T, 30.0), 56, RED)
    if T > 36.16: tag(c, 'ET TU N\'AS RIEN SENTI', 960, 900 - 60, at(T, 36.3), 46, WHITE)


def s_change(c, T, t):
    if T < 42.48:
        tag(c, 'VITESSE', 600, 300, at(T, 40.0), 80, (90, 220, 130)); check(c, 600, 470, 70)
        if T > 41.12: tag(c, 'CHANGEMENT', 1320, 300, at(T, 41.6), 80, RED); xmark(c, 1320, 470, 70, at(T, 41.8))
        me(c, 960, T, 0.7, mood='calm')
    else:
        items = [(42.48, 'speed'), (44.4, 'press'), (46.08, 'weight'), (47.8, 'elec')]
        for i, (t0, k) in enumerate(items):
            p = at(T, t0)
            if p <= 0.02: continue
            x = 300 + i * 440; y = 430
            c.ell(x, y, 150 * min(1, p), fill=(24, 40, 52), outline=RED, w=6)
            if k == 'speed': gauge(c, x, y - 10, 90 * min(1, p), 0.95, '')
            elif k == 'press': thermometer(c, x, y + 70, 160 * min(1, p), 0.1)
            elif k == 'weight':
                c.rect(x - 70, y - 30, x + 70, y + 80, fill=(70, 74, 80), r=20); c.arc(x, y - 30, 40, 180, 360, (70, 74, 80), 16)
                c.text(x, y + 30, '×1000', 34, WHITE)
            else: bolt(c, x - 30, y - 100, x + 30, y + 100, int(T * 12), amp=30)


def s_flaw(c, T, t):
    kinds = [('giant', 'N°5'), ('fly', 'N°4'), ('speed', 'N°3'), ('elec', 'N°2'), ('portal', 'N°1')]
    for i, (k, lab) in enumerate(kinds):
        card(c, 240 + i * 360, 420, 300, 420, lab, k, T, 0.6 + 0.4 * math.sin(T * 4 + i))
    tag(c, 'TOUT CHANGE EN UN INSTANT', 960, 820 - 20, at(T, 52.8), 56, RED)


def s_calm(c, T, t):
    globe(c, 960, 860, 420, T * 0.15)
    info = character(c, 960, 450, 0.9, dict(legs='sit', mood='calm', arms=('hold', 'down'), shadow=False), T)
    h = info['hands'][0]; coffee(c, h[0] - 20, h[1] + 10, 0.9, T)
    if T > 60.0: tag(c, '+100 000 KM/H', 400, 200, at(T, 60.9), 56, YEL)
    if T > 64.52:
        heart(c, 1560, 200, 60, 1 + 0.1 * max(0, math.sin(T * 7)) ** 6); thermometer(c, 1720, 300, 180, 0.45)
        tag(c, 'RÉGLÉ POUR LA VIE', 1500, 420, at(T, 65.0), 40, CYAN)


def s_cta(c, T, t):
    me(c, 520, T, 1.0, mood='happy', arms=('point', 'down'))
    c.rect(880, 160, 1760, 560, fill=(232, 234, 236), r=40)
    c.poly([(940, 540), (1020, 540), (900, 640)], (232, 234, 236))
    c.text(1320, 260, 'QUEL POUVOIR', 64, (40, 44, 50)); c.text(1320, 340, 'PRENDRAIS-TU ?', 64, (40, 44, 50))
    for i, k in enumerate(['giant', 'fly', 'speed', 'elec', 'portal']):
        icon(c, k, 1000 + i * 160, 470, 0.45, T)
    if T > 75.36: tag(c, 'ÉCRIS-LE EN COMMENTAIRE', 1320, 720, at(T, 75.4), 46, YEL)


def s_sub(c, T, t):
    p = at(T, 82.5, 0.4)
    me(c, 520, T, 1.0, mood='happy2', arms=('point', 'wave'))
    c.rect(1000, 330, 1000 + 640 * min(1, p), 510, fill=(220, 40, 40), r=40)
    if p > 0.6: c.text(1320, 420, 'ABONNE-TOI', 74, WHITE)
    c.ell(1720, 420, 60, fill=(240, 240, 240))
    c.text(1320, 640, 'invisibilité · arrêt du temps…', 40, CYAN, black=False)


def s_end(c, T, t):
    c.glow(960, 440, 420, 420, (170, 110, 255), 0.5)
    tag(c, '?', 960, 440, at(T, 85.5), 220, (200, 160, 255))


SCENES = [
    [(0, s_room), (10.0, s_countdown), (16.4, s_physics), (22.16, s_cinema), (25.84, s_gauges), (43.68, s_lineup)],
    [(0, s_title('N°5', 'DEVENIR GÉANT')), (3.12, s_grow), (15.6, s_view), (21.44, s_cube), (34.2, s_bone), (44.5, s_galileo),
     (53.0, s_elephant), (55.76, s_whale), (62.4, s_air), (64.08, s_collapse), (70.52, s_heart), (79.56, s_end1)],
    [(0, s_title('N°4', 'VOLER')), (4.64, s_takeoff), (12.6, s_alti), (18.44, s_everest), (42.0, s_plane), (55.28, s_blur),
     (62.08, s_armstrong), (80.72, s_blood), (86.56, s_drift), (94.32, s_ground)],
    [(0, s_title('N°3', 'LA SUPER-VITESSE')), (3.04, s_bolt), (16.8, s_accel), (32.72, s_stapp), (54.16, s_mach),
     (71.0, s_capsule), (79.6, s_tshirt), (83.16, s_heart_tease)],
    [(0, s_title('N°2', "CONTRÔLER L'ÉLECTRICITÉ")), (3.12, s_zap), (5.28, s_eel), (20.4, s_shield), (30.96, s_body),
     (46.08, s_current), (70.32, s_faint), (75.04, s_defib), (85.48, s_saves), (89.24, s_tease1)],
    [(0, s_title('N°1', 'LA TÉLÉPORTATION')), (2.88, s_popular), (5.76, s_nomore), (9.52, s_map), (15.12, s_quantum),
     (27.24, s_nobel), (39.04, s_fiction), (43.52, s_spin), (63.92, s_antipode), (82.21, s_impact), (92.88, s_stayfr)],
    [(0, s_pl), (17.44, s_crash), (21.52, s_orbit), (37.76, s_change), (49.44, s_flaw), (55.0, s_calm), (70.16, s_cta),
     (80.0, s_sub), (85.36, s_end)],
]
BGS = {
    s_room: 'room', s_countdown: 'plain', s_physics: 'plain', s_cinema: 'plain', s_gauges: 'plain', s_lineup: 'plain',
    s_grow: 'citywide', s_view: 'citywide', s_cube: 'plain', s_bone: 'plain', s_galileo: 'plain', s_elephant: 'plain',
    s_whale: 'ocean', s_air: 'citywide', s_collapse: 'citywide', s_heart: 'plain', s_end1: 'citywide',
    s_takeoff: 'sky', s_alti: 'sky', s_everest: 'mountain', s_plane: 'highsky', s_blur: 'highsky', s_armstrong: 'highsky',
    s_blood: 'plain', s_drift: 'space', s_ground: 'plain',
    s_bolt: 'track', s_accel: 'track', s_stapp: 'desert', s_mach: 'city', s_capsule: 'highsky', s_tshirt: 'plain',
    s_heart_tease: 'plain', s_zap: 'plain', s_eel: 'ocean', s_shield: 'plain', s_body: 'plain', s_current: 'hospital',
    s_faint: 'hospital', s_defib: 'station', s_saves: 'plain', s_tease1: 'plain',
    s_popular: 'city', s_nomore: 'plain', s_map: 'space', s_quantum: 'lab', s_nobel: 'plain', s_fiction: 'plain',
    s_spin: 'space', s_antipode: 'space', s_impact: 'sky', s_stayfr: 'plain',
    s_pl: 'map', s_crash: 'plain', s_orbit: 'space', s_change: 'plain', s_flaw: 'plain', s_calm: 'space', s_cta: 'plain',
    s_sub: 'plain', s_end: 'space',
}
BLUR = {s_blur: lambda T: max(0, (T - 56.6) / 3.0) * 6}


def scene_at(frame):
    sec = max(i for i in range(7) if OFF[i] <= frame)
    T = (frame - OFF[sec]) / FPS
    lst = SCENES[sec]
    idx = max(i for i, (t0, _) in enumerate(lst) if t0 <= T + 1e-6)
    t0, fn = lst[idx]
    t1 = lst[idx + 1][0] if idx + 1 < len(lst) else NF[sec] / FPS
    return sec, T, fn, t0, t1
