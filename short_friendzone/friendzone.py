"""Short « Friendzone à l'école » — réutilise le modèle short_daronne/short.py."""
import sys, os, math, random, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'short_daronne'))
import short as SH
from short import E, C, character, bubble, back, ease, lerp, mix, font, YEL, RED, CYAN, WHITE, BLK, HOOD, W, H, FPS, FLOOR
from PIL import Image, ImageDraw
from multiprocessing import Pool

SON = SH.SON
CRUSH = dict(col=(150, 92, 205), outfit='dress', longhair=True, hair=(222, 176, 86))
POTE1 = dict(col=(60, 150, 90), hair=(30, 30, 30))
POTE2 = dict(col=(232, 160, 48), hair=(90, 52, 30))
BEAU = dict(col=(40, 40, 52), hair=(230, 230, 240), flathair=True)


def tag(c, txt, y, t, col=YEL, size=60):
    E.tag(c, txt, W / 2, y, back(t / 0.3), size, col)


def pair(c, T, a, b, am='happy', bm='happy', akw=None, bkw=None, la=None, lb=None):
    A = dict(a); A.update(mood=am, look=(5, 2), blink=(T % 3.3) < 0.08); A.update(akw or {})
    B = dict(b); B.update(mood=bm, look=(-5, 2), blink=(T % 2.8) < 0.08); B.update(bkw or {})
    ia = character(c, 280, FLOOR, 1.95, A, T); ib = character(c, 800, FLOOR, 1.95, B, T)
    if la: SH.who(c, 280, ia['head'][1] - 190, la, (40, 90, 170))
    if lb: SH.who(c, 800, ib['head'][1] - 190, lb, (150, 80, 190))
    return ia, ib


def hearts(c, x, y, T, n=4, spread=120, size=30, seed=1):
    for k in range(n):
        r = random.Random(seed * 10 + k); u = (T * 0.5 + r.random()) % 1
        E.heart(c, x + r.uniform(-spread, spread), y - u * 260, size * (1 - 0.5 * u))


def broken(c, x, y, r, gap):
    col = (230, 60, 70)
    E.heart(c, x, y, r)
    zig = [(x, y - r * 0.35), (x - r * 0.15, y - r * 0.05), (x + r * 0.12, y + r * 0.25), (x - r * 0.1, y + r * 0.55), (x, y + r * 1.05)]
    c.line(zig, (30, 20, 40), 14 + gap * 30, cap=False)


def card(c, x, y, w, h, txt, sub=None, col=(255, 255, 255), rot=0):
    c.rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, fill=col, r=14)
    E.heart(c, x, y - 20, 40)
    c.text(x, y + h / 2 - 34, txt, 30, (60, 60, 70))


def thought(c, x, y, w, h, tail=(0, 0)):
    c.ell(x, y, w, h, fill=(232, 234, 236))
    tx, ty = tail
    if tx: c.ell(tx, ty, 26, fill=(232, 234, 236)); c.ell((tx + x) / 2 + 20, (ty + y + h) / 2, 16, fill=(232, 234, 236))


def chat(c, msgs, T):
    c.rect(200, 300, 880, 1250, fill=(232, 236, 240), r=50)
    c.rect(220, 320, 860, 1230, fill=(246, 248, 250), r=40)
    c.rect(470, 340, 610, 352, fill=(60, 60, 70), r=6)
    c.ell(300, 430, 40, fill=CRUSH['col']); c.text(300, 430, 'L', 44, WHITE)
    c.text(420, 430, 'Lina', 44, (40, 44, 52)); c.text(760, 430, '23:58', 34, (130, 130, 140), black=False)
    y = 560
    for t0, txt, mine in msgs:
        p = back((T - t0) / 0.25)
        if p <= 0.02: continue
        f = font(40 * E.S); tw = c.d.textlength(txt, font=f) / E.S
        if mine:
            c.rect(840 - tw - 50, y - 40, 840, y + 40, fill=(70, 120, 230), r=36); c.text(840 - tw / 2 - 25, y, txt, 40 * min(1, p), WHITE)
        else:
            c.rect(250, y - 40, 250 + tw + 50, y + 40, fill=(220, 224, 230), r=36); c.text(250 + tw / 2 + 25, y, txt, 40 * min(1, p), (40, 44, 52))
        y += 120


# ------------------------------------------------------------ plans
def q01(c, T, t):
    c.text(W / 2, 260, 'FRIENDZONE', 130 * min(1.05, back(t / 0.3)), YEL, stroke=10)
    c.text(W / 2, 410, "À L'ÉCOLE ?", 110 * min(1.05, back((t - 0.15) / 0.3)), WHITE, stroke=9)
    SH.closeup(c, T, SON, 'worry')


def q02(c, T, t):
    pair(c, T, SON, CRUSH, 'happy', 'happy2', bkw=dict(arms=('down', 'wave')))
    hearts(c, 800, 900, T, 5)
    SH.big(c, 'ELLE TE FAIT', 250, t, WHITE, 96); SH.big(c, 'CROIRE…', 370, t - 0.15, RED, 110)


def q03(c, T, t):
    pair(c, T, SON, CRUSH, 'neutral', 'happy', bkw=dict(look=(-7, 0)))
    SH.big(c, 'ELLE TE CALCULE', 300, t, YEL, 96)


def q04(c, T, t):
    c.glow(540, 1000, 500, 500, (255, 120, 180), 0.35)
    SH.closeup(c, T, CRUSH, 'happy2', arms=('down', 'wave'))
    hearts(c, 540, 800, T, 6, 300, 36, 3)
    SH.big(c, 'ELLE SOURIT', 300, t, WHITE, 110)


def q05(c, T, t):
    pair(c, T, SON, CRUSH, 'happy', 'happy2', bkw=dict(arms=('down', 'wave')))
    bubble(c, 'Hey !', 800, 560, back(t / 0.25), 56, tail=-1)
    if T > 10.8: SH.big(c, 'JUSTE POUR TOI ?', 300, T - 10.84, YEL, 96)


def q06(c, T, t):
    c.ell(880, 200, 70, fill=(250, 230, 160)); c.ell(910, 180, 62, fill=SH.PAL['navy'][0])
    chat(c, [(12.4, "t'es là ?", False), (13.0, 'trop drôle mdrr', False), (13.5, 'grave ahah', True), (14.0, 'bonne nuit', False)], T)
    E.tag(c, '00:00', 540, 1180, back((T - 14.3) / 0.3), 70, (180, 140, 255))


def q07(c, T, t):
    SH.closeup(c, T, SON, 'happy2', arms=('up', 'up'))
    hearts(c, 540, 780, T, 6, 320, 34, 5)
    SH.big(c, "T'ES EN MODE :", 280, t, YEL, 96)
    if T > 16.4: bubble(c, "C'est bon, c'est ma go.", 540, 540, back((T - 16.45) / 0.3), 50, tail=1)


def q08(c, T, t):
    p = back(t / 0.35)
    c.glow(540, 900, 500, 300, RED, 0.5)
    c.rect(540 - 380 * min(1, p), 820, 540 + 380 * min(1, p), 980, fill=(225, 40, 40), r=80)
    if p > 0.6: c.text(540, 900, 'ABONNE-TOI', 84, WHITE)
    c.ell(540, 680, 60, fill=(250, 210, 70)); c.rect(500, 680, 580, 720, fill=(250, 210, 70)); c.ell(540, 745, 16, fill=(250, 210, 70))
    cx = lerp(900, 700, ease(t / 0.8)); cy = lerp(1200, 940, ease(t / 0.8))
    c.poly([(cx, cy), (cx + 70, cy + 110), (cx + 30, cy + 100), (cx + 50, cy + 160), (cx + 30, cy + 168), (cx + 12, cy + 108), (cx - 20, cy + 130)], WHITE)
    if T > 19.0: SH.big(c, 'LA SUITE VA FAIRE MAL', 1100, T - 19.0, YEL, 70)


def q09(c, T, t):
    character(c, 180, FLOOR, 1.5, dict(POTE1, mood='shock', look=(6, 0)), T)
    character(c, 900, FLOOR, 1.5, dict(POTE2, mood='shock', look=(-6, 0)), T)
    character(c, 540, FLOOR, 1.95, dict(SON, mood='happy2', arms=('wave', 'down')), T)
    bubble(c, 'Sérieux ??', 230, 820, back((T - 21.4) / 0.25), 46, tail=1)
    SH.big(c, 'À TES POTES', 300, t, WHITE, 110)


def q10(c, T, t):
    SH.closeup(c, T, SON, 'happy2', look=(4, -6))
    thought(c, 600, 640, 230, 140, (440, 860))
    E.heart(c, 520, 640, 50); c.text(600, 640, '+', 70, (60, 60, 70)); E.heart(c, 690, 640, 50)
    SH.big(c, 'TU TE FAIS', 220, t, WHITE, 96); SH.big(c, 'DES FILMS', 330, t - 0.15, YEL, 110)


def q11(c, T, t):
    c.ell(870, 900, 150, 230, fill=(200, 170, 90)); c.ell(870, 900, 125, 205, fill=(150, 200, 230))
    c.ell(830, 820, 20, 60, fill=(220, 240, 250))
    SH.closeup(c, T, SON, 'determined', arms=('down', 'think'))
    for k in range(5):
        r = random.Random(k); u = (T * 1.5 + r.random()) % 1
        x, y, s = 300 + r.uniform(0, 500), 600 + r.uniform(0, 400), 14 * math.sin(u * math.pi) + 2
        c.poly([(x, y - s * 2), (x + s * 0.5, y - s * 0.5), (x + s * 2, y), (x + s * 0.5, y + s * 0.5), (x, y + s * 2), (x - s * 0.5, y + s * 0.5), (x - s * 2, y), (x - s * 0.5, y - s * 0.5)], (255, 240, 180))
    SH.big(c, 'TU TE METS FRAIS', 300, t, YEL, 92)
    if T > 24.9: tag(c, 'PARFUM · COIFFURE · TOUT', 1560, T - 24.96, CYAN, 46)


def q12(c, T, t):
    pair(c, T, SON, CRUSH, 'worry', 'neutral', akw=dict(tremble=2))
    if T > 28.3: SH.big(c, 'COURAGE !', 300, T - 28.32, RED, 120)
    if T > 29.0: bubble(c, "Je t'aime bien…", 300, 560, back((T - 29.0) / 0.3), 48, tail=1)


def q13(c, T, t):
    SH.closeup(c, T, CRUSH, 'neutral')
    SH.big(c, 'ET LÀ…', 300, t, WHITE, 130)


def q14(c, T, t):
    pair(c, T, SON, CRUSH, 'shock', 'happy', bkw=dict(arms=('down', 'wave')))
    bubble(c, "Mais t'es comme un frère pour moi.", 600, 560, back(t / 0.3), 40, tail=1)


def q15(c, T, t):
    c.glow(540, 1000, 600, 600, RED, 0.45)
    SH.closeup(c, T, SON, 'ko', tremble=3)
    broken(c, 540, 640, 120, ease((T - 35.6) / 0.4))
    SH.big(c, 'FRÈRE.', 280, t, RED, 150)
    if T > 36.4: tag(c, 'LE MOT QUI TUE', 1560, T - 36.48, RED, 62)


def q16(c, T, t):
    for i, (x, txt, t0) in enumerate([(270, 'REGARDS', 37.7), (540, 'SOURIRES', 38.6), (810, 'MESSAGES', 39.7)]):
        p = back((T - t0) / 0.3)
        if p > 0.02:
            fade = 1 - 0.6 * ease((T - 40.3) / 1.0)
            card(c, x, 520, 220 * min(1, p), 260 * min(1, p), txt, col=mix((40, 40, 60), (245, 245, 245), fade))
    character(c, 540, 1900, 1.5, dict(SON, mood='worry', look=(0, -5)), T)
    SH.big(c, 'LES SOUVENIRS…', 250, t, WHITE, 96)
    if T > 40.2: tag(c, 'TOUT DANS TA TÊTE ?', 900, T - 40.22, YEL, 62)


def q17(c, T, t):
    c.rect(170, 220, 910, 520, fill=(30, 84, 60), r=18, outline=(140, 100, 60), w=14)
    c.text(540, 320, 'LENDEMAIN', 60, (250, 230, 120)); c.text(540, 420, 'COURS DE MATHS', 64, WHITE)
    pair(c, T, SON, CRUSH, 'neutral', 'happy2')
    c.rect(60, 1500, 1020, 1560, fill=(120, 84, 56), r=10)


def q18(c, T, t):
    pair(c, T, SON, CRUSH, 'worry', 'happy2', bkw=dict(look=(4, -6)))
    thought(c, 760, 600, 210, 170, (790, 880))
    character(c, 740, 720, 0.45, dict(BEAU, mood='happy', shadow=False), T); E.heart(c, 860, 540, 34)
    SH.big(c, 'UN AUTRE GARS', 280, t, RED, 96)


def q19(c, T, t):
    SH.closeup(c, T, SON, 'happy', tremble=1.5)
    c.ell(760, 920, 18, 28, fill=(140, 200, 255))
    SH.big(c, 'FAUX SOURIRE', 300, t, YEL, 110)
    if T > 50.0:
        broken(c, 540, 640, 110, ease((T - 50.2) / 0.5)); tag(c, 'LE CŒUR EN MIETTES', 1560, T - 50.24, RED, 60)


def q20(c, T, t):
    character(c, 200, FLOOR, 1.7, dict(POTE1, mood='happy2', look=(6, 0)), T)
    character(c, 880, FLOOR, 1.7, dict(POTE2, mood='happy2', look=(-6, 0)), T)
    character(c, 540, FLOOR, 1.95, dict(SON, mood='worry' if T > 54 else 'neutral'), T)
    if T < 54.8: bubble(c, "Alors, c'est ta go ?", 300, 760, back((T - 51.6) / 0.25), 46, tail=1)
    else:
        bubble(c, "Nan… c'est juste une pote.", 600, 600, back((T - 54.9) / 0.3), 44, tail=1)
        SH.big(c, 'JUSTE UNE POTE', 300, T - 55.6, YEL, 100)


def q21(c, T, t):
    c.poly([(540, 0), (180, 1900), (900, 1900)], (90, 80, 60))
    c.glow(540, 1100, 400, 700, (255, 230, 150), 0.4)
    SH.closeup(c, T, SON, 'happy2', arms=('up', 'up'))
    SH.big(c, 'PERSONNAGE', 230, t, YEL, 110); SH.big(c, 'PRINCIPAL ?', 360, t - 0.15, WHITE, 110)


def q22(c, T, t):
    c.glow(640, 1100, 420, 600, (255, 230, 150), 0.35)
    character(c, 640, FLOOR, 1.95, dict(CRUSH, mood='happy2', arms=('down', 'wave')), T)
    character(c, 860, FLOOR, 1.6, dict(BEAU, mood='happy'), T)
    character(c, 150, FLOOR, 0.9, dict(SON, mood='worry'), T)
    SH.who(c, 150, 1250, 'FIGURANT', (60, 60, 70))
    c.rect(780, 560, 980, 700, fill=(30, 30, 36), r=10)
    for k in range(4): c.poly([(790 + k * 48, 560), (812 + k * 48, 560), (800 + k * 48, 520), (778 + k * 48, 520)], WHITE if k % 2 else (30, 30, 36))
    c.text(880, 630, 'SCÈNE 1', 34, WHITE)
    SH.big(c, 'JUSTE LE', 240, t, WHITE, 96); SH.big(c, 'FIGURANT', 350, t - 0.15, RED, 120)


def q23(c, T, t):
    SH.closeup(c, T, SON, 'determined', arms=('down', 'cover'))
    c.ell(540, 640, 120, fill=(70, 110, 170)); c.ell(540, 640, 100, fill=(40, 70, 120)); E.heart(c, 540, 630, 55)
    if T > 64.3: SH.big(c, 'PROTÈGE', 220, T - 64.32, WHITE, 120); SH.big(c, 'TON CŒUR', 350, T - 64.5, YEL, 130)


SH.PLANS = [(0, q01, 'teal', False), (3.0, q02, 'rose', True), (6.35, q03, 'amber', True), (7.86, q04, 'rose', False),
            (9.54, q05, 'amber', True), (12.18, q06, 'navy', False), (14.94, q07, 'purple', False), (18.0, q08, 'red', False),
            (20.6, q09, 'amber', True), (22.34, q10, 'purple', False), (23.54, q11, 'teal', False), (26.58, q12, 'rose', True),
            (30.34, q13, 'navy', False), (33.18, q14, 'rose', True), (35.26, q15, 'red', False), (37.62, q16, 'navy', False),
            (41.86, q17, 'green', True), (44.9, q18, 'amber', True), (47.3, q19, 'purple', False), (51.42, q20, 'teal', True),
            (56.72, q21, 'amber', False), (59.58, q22, 'amber', True), (61.78, q23, 'navy', False)]
SH.BURST = {q08, q15}
SH.DUR = 65.8
SH.N = int(SH.DUR * FPS)
SH.HL = {'FRIENDZONE', "L'ÉCOLE", 'ATROCE', 'PIRE', 'CALCULE', 'SOURIT', 'MINUIT', 'FRÉROT', 'GO', 'ABONNE-TOI', 'MAL',
         'POTES', 'FILMS', 'FRAIS', 'COURAGE', 'FRÈRE', 'TUE', 'INVENTÉ', 'TÊTE', 'MATHS', 'AUTRE', 'BEAU', 'SEMBLANT',
         'ZÉRO', 'MIETTES', 'POTE', 'PRINCIPAL', 'FIGURANT', 'CŒUR', 'PROTÈGE'}
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
    else:
        n = 4; step = math.ceil(SH.N / n)
        jobs = [(i * step, min(SH.N, (i + 1) * step), os.path.join(out, f'p{i}.mp4')) for i in range(n)]
        with Pool(n) as pool: parts = pool.map(render, jobs)
        with open(os.path.join(out, 'list.txt'), 'w') as fh:
            for p in parts: fh.write(f"file '{p}'\n")
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', os.path.join(out, 'list.txt'),
                        '-c', 'copy', os.path.join(out, 'friendzone_muet.mp4')], check=True)
        print('ok')
