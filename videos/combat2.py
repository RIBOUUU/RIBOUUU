"""Combat de bonhommes très dynamique, chorégraphié sur les kicks du beat (intro ~12 s)."""
import sys, subprocess, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

AUDIO, OUT = sys.argv[1], sys.argv[2]
W, H, FPS = 540, 960, 30
START, DUR = 28.0, 12.4          # extrait de la musique : la batterie entre à ~32.08 s
random.seed(4)

# ---------- poses (face à droite, hanche = origine, y vers le bas) ----------
J = ["neck", "head", "fel", "fha", "bel", "bha", "fkn", "ffo", "bkn", "bfo"]
P = {
 "stance": [(4,-58),(6,-80),(20,-44),(32,-62),(-6,-42),(14,-58),(16,24),(24,54),(-14,26),(-26,54)],
 "run_a":  [(14,-56),(20,-77),(-6,-40),(4,-26),(22,-44),(36,-52),(22,14),(18,40),(-10,26),(-30,44)],
 "run_b":  [(14,-56),(20,-77),(22,-44),(36,-52),(-6,-40),(4,-26),(-10,26),(-30,44),(22,14),(18,40)],
 "dash":   [(30,-46),(44,-62),(16,-30),(0,-16),(10,-34),(-8,-22),(26,14),(20,40),(-20,22),(-46,36)],
 "land":   [(18,-44),(26,-62),(28,-20),(30,30),(0,-34),(-24,-52),(28,4),(26,30),(-10,18),(-30,30)],
 "punch":  [(12,-56),(16,-77),(38,-56),(66,-60),(-10,-40),(6,-56),(18,24),(30,54),(-16,24),(-32,54)],
 "kick":   [(-12,-56),(-18,-77),(8,-48),(22,-62),(-26,-44),(-40,-28),(32,-10),(68,-32),(-4,26),(-8,54)],
 "upper":  [(10,-60),(14,-82),(30,-60),(36,-96),(-8,-42),(8,-56),(16,24),(24,54),(-18,24),(-30,54)],
 "hit":    [(-16,-54),(-30,-70),(-4,-48),(12,-34),(-26,-46),(-40,-58),(8,24),(16,54),(-14,24),(-26,54)],
 "block":  [(-2,-56),(0,-78),(18,-56),(20,-78),(12,-50),(16,-70),(16,24),(26,54),(-16,24),(-30,54)],
 "duck":   [(16,-32),(26,-48),(22,-22),(36,-34),(4,-20),(20,-30),(26,6),(22,32),(-16,16),(-30,32)],
 "tuck":   [(4,-40),(10,-58),(20,-26),(24,-6),(10,-24),(14,-4),(24,-14),(20,10),(18,-8),(10,14)],
 "airkick":[(-30,-40),(-48,-50),(-14,-30),(-2,-18),(-34,-24),(-50,-14),(30,-6),(64,-8),(10,20),(-8,30)],
 "flail":  [(-6,-56),(-10,-78),(-24,-70),(-36,-92),(16,-70),(30,-90),(18,18),(10,46),(-10,26),(-24,46)],
 "lie":    [(-56,0),(-78,-2),(-40,-8),(-24,-2),(-46,8),(-30,6),(26,-4),(54,0),(26,4),(54,6)],
}
P = {k: np.array(v, float) for k, v in P.items()}
BONES = [(-1,0),(0,2),(2,3),(0,4),(4,5),(-1,6),(6,7),(-1,8),(8,9)]  # -1 = hanche

# ---------- chorégraphie : (t, x, hauteur, rotation°, pose, easing) ----------
A = [(0,-80,950,0,"tuck","lin"),(1.7,-80,0,0,"land","in"),(2.6,-80,0,0,"land","io"),(3.3,-80,0,0,"stance","io"),
     (4.08,-90,0,0,"duck","io"),(4.3,-20,0,0,"dash","out"),(4.48,0,0,0,"punch","out"),(4.7,-25,0,0,"stance","out"),
     (4.94,-20,0,0,"duck","out"),(5.25,-5,0,0,"duck","io"),(5.45,20,10,0,"upper","out"),(5.8,30,0,0,"stance","io"),
     (6.0,40,30,0,"tuck","out"),(6.6,130,300,360,"tuck","out"),(6.84,150,330,360,"airkick","out"),
     (7.3,170,120,360,"tuck","in"),(7.71,175,0,360,"land","in"),(8.1,180,0,360,"stance","io"),
     (8.4,225,0,360,"punch","out"),(8.55,215,0,360,"stance","io"),(8.64,212,0,360,"block","out"),
     (8.87,240,0,360,"kick","out"),(9.0,232,0,360,"stance","io"),(9.16,205,0,360,"hit","out"),
     (9.6,40,0,360,"hit","out"),(10.0,40,0,360,"stance","io"),(10.6,30,0,360,"duck","io"),
     (11.1,150,0,360,"dash","in"),(11.42,205,0,360,"punch","out"),(12.4,195,0,360,"punch","io")]
B = [(0,700,0,0,"stance","lin"),(2.3,700,0,0,"run","lin"),(3.5,150,0,0,"run","lin"),(3.75,105,0,0,"duck","out"),
     (4.08,110,0,0,"stance","io"),(4.3,100,0,0,"stance","io"),(4.48,92,0,0,"block","out"),(4.7,110,0,0,"stance","out"),
     (4.94,85,0,0,"kick","out"),(5.25,78,0,0,"stance","io"),(5.45,88,30,0,"flail","out"),
     (6.84,215,330,-540,"flail","out"),(7.71,270,0,-720,"lie","in"),(7.91,290,45,-720,"tuck","out"),
     (8.2,310,0,-1080,"stance","in"),(8.4,315,0,-1080,"hit","out"),(8.55,318,0,-1080,"stance","io"),
     (8.64,298,0,-1080,"punch","out"),(8.87,330,0,-1080,"hit","out"),(9.0,322,0,-1080,"stance","io"),
     (9.16,290,0,-1080,"kick","out"),(9.5,330,0,-1080,"tuck","out"),(9.75,375,90,-1260,"tuck","out"),
     (10.1,420,0,-1440,"stance","in"),(10.6,425,0,-1440,"duck","io"),(11.1,330,0,-1440,"dash","in"),
     (11.42,295,0,-1440,"punch","out"),(12.4,305,0,-1440,"punch","io")]
# impacts : (t, x, hauteur, force, type)
FX = [(1.7,-80,0,3,"land"),(3.6,130,0,0.6,"dust"),(4.48,55,75,1.5,"hit"),(4.94,60,70,0.4,"whoosh"),
      (5.45,70,90,1.8,"hit"),(6.84,205,350,2.2,"hit"),(7.71,265,0,2.6,"land"),(7.91,285,10,0.8,"dust"),
      (8.4,280,65,1.1,"hit"),(8.64,262,65,0.8,"hit"),(8.87,300,45,1.2,"hit"),(9.16,250,45,1.6,"hit"),
      (9.3,150,0,0.6,"dust"),(11.42,252,70,4,"clash"),(11.88,252,70,2.2,"clash")]

EASE = {"lin": lambda p: p, "in": lambda p: p*p, "out": lambda p: 1-(1-p)**2, "io": lambda p: p*p*(3-2*p)}

def pose_of(name, t):
    if name == "run":
        s = 0.5 + 0.5*math.sin(t*2*math.pi*4)
        return P["run_a"]*s + P["run_b"]*(1-s)
    return P[name]

def sample(keys, t):
    if t <= keys[0][0]: k = keys[0]; return k[1], k[2], k[3], pose_of(k[4], t)
    for a, b in zip(keys, keys[1:]):
        if t <= b[0]:
            p = (t - a[0]) / max(1e-6, b[0] - a[0])
            e = EASE[b[5]](p)
            q = min(1, p / 0.35); q = q*q*(3-2*q)            # la pose arrive vite = coups secs
            pose = pose_of(a[4], t)*(1-q) + pose_of(b[4], t)*q
            return a[1]+(b[1]-a[1])*e, a[2]+(b[2]-a[2])*e, a[3]+(b[3]-a[3])*e, pose
    k = keys[-1]; return k[1], k[2], k[3], pose_of(k[4], t)

def skeleton(x, h, rot, pose, facing):
    pts = np.vstack([[0, 0], pose])
    r = math.radians(rot); c, s = math.cos(r), math.sin(r)
    pts = np.stack([pts[:,0]*c - pts[:,1]*s, pts[:,0]*s + pts[:,1]*c], 1)
    hip_h = h + pts[:,1].max()                     # le point le plus bas touche « h »
    return np.stack([x + facing*pts[:,0], hip_h - pts[:,1]], 1)   # coordonnées monde (y vers le haut)

# ---------- décor ----------
ruins = [(random.uniform(-1500, 1500), random.uniform(20, 70), random.uniform(30, 160)) for _ in range(70)]
yy, xx = np.mgrid[0:H, 0:W]
vign = (1 - 0.65*(((xx-W/2)/(W*0.75))**2 + ((yy-H/2)/(H*0.7))**2)).clip(0.25, 1)[..., None]
ash = [[random.uniform(0, W), random.uniform(0, H), random.uniform(0.3, 1.2)] for _ in range(70)]

ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                       "-r", str(FPS), "-i", "-", "-ss", str(START), "-t", str(DUR), "-i", AUDIO,
                       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-c:a", "aac", "-shortest", OUT],
                      stdin=subprocess.PIPE)

COL = [(110, 235, 255), (255, 55, 75)]
cam = np.array([-80.0, 750.0]); zoom = 1.0
shake = flash = 0.0; sparks = []; rings = []; lines_t = -9; trails = [[], []]; prev = [None, None]
fired = set()

for f in range(int(DUR*FPS)):
    t = f / FPS
    st = [sample(A, t), sample(B, t)]
    sk = [skeleton(*st[0], 1), skeleton(*st[1], -1)]

    # caméra : suit l'orbe pendant la chute, puis le milieu des combattants
    if t < 1.7:
        tgt = np.array([-80, st[0][1] - 40]); zt = 1.25
    else:
        xs = [st[0][0], min(st[1][0], st[0][0] + (60 if t < 2.6 else 520))]
        tgt = np.array([sum(xs)/2, max(st[0][1], st[1][1])*0.55 + 60])
        zt = float(np.clip(330/(abs(xs[1]-xs[0]) + 170), 0.5, 1.45))
    cam += (tgt - cam) * (0.35 if t < 1.7 else 0.16)
    zoom += (zt - zoom) * 0.12

    # déclenchement des effets
    for i, (ft, fx, fh, fs, kind) in enumerate(FX):
        if i not in fired and t >= ft:
            fired.add(i)
            shake = max(shake, fs*7); flash = max(flash, min(1, fs/3)) if kind != "dust" else flash
            n = int(10 + fs*14)
            for _ in range(n):
                a = random.uniform(0, 2*math.pi) if kind != "land" and kind != "dust" else random.uniform(0.1, math.pi-0.1)
                v = random.uniform(3, 6 + fs*4)
                col = (255, 225, 140) if kind in ("hit", "clash") else (150, 120, 90)
                sparks.append([fx, fh, math.cos(a)*v*(1.6 if kind in ("land","dust") else 1), math.sin(a)*v, 1.0, col])
            if kind in ("land", "clash", "hit") and fs >= 1:
                rings.append([fx, fh, 0.0, fs, kind == "land"])
            if kind == "clash" or fs >= 2.5: lines_t = f

    # poussière quand un combattant glisse au sol
    for i in range(2):
        if prev[i] is not None and st[i][1] < 2:
            vx = st[i][0] - prev[i]
            if abs(vx) > 6:
                for _ in range(2):
                    sparks.append([st[i][0], 0, -vx*0.3 + random.uniform(-2, 2), random.uniform(1, 4), 0.8, (140, 110, 80)])
        prev[i] = st[i][0]

    shake *= 0.82; flash *= 0.78
    sc = 1.9 * zoom
    ox, oy = random.uniform(-shake, shake), random.uniform(-shake, shake)
    def S(wx, wh): return (W/2 + (wx - cam[0])*sc + ox, H*0.62 - (wh - cam[1])*sc + oy)

    # ciel + sol
    hy = S(0, 0)[1]
    rows = (np.arange(H) - hy)[:, None]
    sky = np.where(rows < 0, 1, 0)
    k = np.clip(-rows/900, 0, 1)
    skyc = np.concatenate([18 + 30*(1-k), 15 + 22*(1-k), 24 + 26*(1-k)], 1)
    g = np.clip(rows/500, 0, 1)
    grc = np.concatenate([88 - 50*g, 66 - 40*g, 50 - 32*g], 1)
    col = np.where(sky == 1, skyc, grc)
    img = Image.fromarray(np.repeat(col[:, None, :], W, 1).astype(np.uint8))
    d = ImageDraw.Draw(img)
    for rx, rw, rh in ruins:  # ruines lointaines (parallaxe)
        px = W/2 + (rx - cam[0]*0.35)*sc*0.5 + ox
        if -100 < px < W + 100:
            d.rectangle([px, hy - rh*sc*0.4, px + rw*sc*0.5, hy], fill=(22, 18, 24))
    d.rectangle([0, hy, W, hy + 3], fill=(40, 32, 30))

    glow = Image.new("RGB", (W, H)); gd = ImageDraw.Draw(glow)

    # orbe lumineux pendant la chute
    if t < 1.7:
        px, py = S(-80, st[0][1] + 40)
        for r, c in ((60, (90, 140, 160)), (30, (200, 240, 255))):
            gd.ellipse([px-r, py-r, px+r, py+r], fill=c)
        gd.line([px, py, px, py - 400], fill=(120, 200, 230), width=18)
        d.ellipse([px-14, py-14, px+14, py+14], fill=(255, 255, 255))

    # traînées de mouvement + bonhommes
    for i in range(2):
        if t < 1.7 and i == 0: continue
        scr = [S(*p) for p in sk[i]]
        trails[i] = (trails[i] + [scr])[-5:]
        wdt = max(3, int(4.5*sc))
        for j, tr in enumerate(trails[i][:-1]):
            a = (j + 1) / len(trails[i]) * 0.45
            c = tuple(int(v*a) for v in COL[i])
            for b0, b1 in BONES:
                gd.line([tr[b0+1], tr[b1+1]], fill=c, width=wdt)
        for dr, w_, c in ((gd, wdt*2, COL[i]), (d, wdt, tuple(min(255, v+60) for v in COL[i]))):
            for b0, b1 in BONES:
                dr.line([scr[b0+1], scr[b1+1]], fill=c, width=w_)
            for p in scr: dr.ellipse([p[0]-w_/2, p[1]-w_/2, p[0]+w_/2, p[1]+w_/2], fill=c)
            hx, hy2 = scr[2]; r = 11*sc
            dr.ellipse([hx-r, hy2-r, hx+r, hy2+r], fill=c)
        # ombre au sol
        gx, gy = S(st[i][0], 0); sw = 40*sc/(1 + st[i][1]/150)
        d.ellipse([gx-sw, gy-5, gx+sw, gy+5], fill=(30, 24, 22))

    # particules
    for s in sparks:
        s[0] += s[2]; s[1] += s[3]; s[3] -= 0.7; s[4] -= 0.045
        if s[1] < 0: s[1] = 0; s[3] *= -0.3; s[2] *= 0.7
        if s[4] > 0:
            p0 = S(s[0], s[1]); p1 = S(s[0]-s[2]*1.5, s[1]-s[3]*1.5)
            c = tuple(int(v*s[4]) for v in s[5])
            gd.line([p0, p1], fill=c, width=5); d.line([p0, p1], fill=c, width=2)
    sparks = [s for s in sparks if s[4] > 0]

    # ondes de choc
    for r in rings:
        r[2] += 1
        rad = r[2] * (14 + r[3]*6) * sc / 1.9
        cx_, cy_ = S(r[0], r[1]); a = max(0, 1 - r[2]/14)
        ry = rad*0.25 if r[4] else rad
        gd.ellipse([cx_-rad, cy_-ry, cx_+rad, cy_+ry], outline=tuple(int(255*a) for _ in range(3)), width=max(1, int(6*a)))
    rings = [r for r in rings if r[2] < 14]

    # lignes de vitesse radiales sur les gros impacts
    if f - lines_t < 8:
        a = 1 - (f - lines_t)/8
        for _ in range(40):
            ang = random.uniform(0, 2*math.pi); r0 = random.uniform(180, 300)
            gd.line([W/2 + math.cos(ang)*r0, H/2 + math.sin(ang)*r0, W/2 + math.cos(ang)*900, H/2 + math.sin(ang)*900],
                    fill=tuple(int(200*a) for _ in range(3)), width=2)

    # cendres qui volent
    for s in ash:
        s[0] = (s[0] - 1.5*s[2] - (cam[0]*0.0)) % W; s[1] = (s[1] + 0.6*s[2]) % H
        d.point((s[0], s[1]), fill=(170, 150, 130))

    arr = np.asarray(img, np.float32) + np.asarray(glow.filter(ImageFilter.GaussianBlur(10)), np.float32)*0.9 \
          + np.asarray(glow, np.float32)*0.25
    arr = arr * vign + flash*160
    if f - lines_t == 0: arr = 255 - np.clip(arr, 0, 255)     # image négative sur l'impact principal
    ff.stdin.write(np.clip(arr, 0, 255).astype(np.uint8).tobytes())

ff.stdin.close(); ff.wait()
