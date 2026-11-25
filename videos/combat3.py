"""Combat de bonhommes 3D/2D, chorégraphié sur les kicks du beat (intro ~12 s)."""
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
BONES = [(0,1),(1,2),(2,3),(2,4),(4,5),(2,6),(6,7),(0,8),(8,9),(0,10),(10,11)]

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
    if t <= keys[0][0]: k = keys[0]; return k[1], k[2], k[3], pose_of(k[4], t), k[4]
    for a, b in zip(keys, keys[1:]):
        if t <= b[0]:
            p = (t - a[0]) / max(1e-6, b[0] - a[0])
            e = EASE[b[5]](p)
            q = min(1, p / 0.35); q = q*q*(3-2*q)            # la pose arrive vite = coups secs
            pose = pose_of(a[4], t)*(1-q) + pose_of(b[4], t)*q
            return a[1]+(b[1]-a[1])*e, a[2]+(b[2]-a[2])*e, a[3]+(b[3]-a[3])*e, pose, (b[4] if q > 0.5 else a[4])
    k = keys[-1]; return k[1], k[2], k[3], pose_of(k[4], t), k[4]

def skeleton(x, h, rot, pose, facing):
    pts = np.vstack([[0, 0], pose])
    r = math.radians(rot); c, s = math.cos(r), math.sin(r)
    pts = np.stack([pts[:,0]*c - pts[:,1]*s, pts[:,0]*s + pts[:,1]*c], 1)
    hip_h = h + pts[:,1].max()                     # le point le plus bas touche « h »
    return np.stack([x + facing*pts[:,0], hip_h - pts[:,1]], 1)   # coordonnées monde (y vers le haut)


# ---------- squelette articulé (angles + ressorts) ----------
# os : (point parent, point enfant, os parent) ; points : 0 hanche,1 buste,2 cou,3 tête,4-5 bras avant,6-7 bras arrière,8-9 jambe avant,10-11 jambe arrière
BD = [(0,1,-1),(1,2,0),(2,3,1),(2,4,1),(4,5,3),(2,6,1),(6,7,5),(0,8,-1),(8,9,7),(0,10,-1),(10,11,9)]
#           buste cou  tête brasA avbA brasB avbB cuisA tibA cuisB tibB
OMEGA = np.array([34, 24, 15, 30, 22, 30, 22, 32, 26, 32, 26], float)   # raideur (plus bas = plus souple)
ZETA = 0.5                                                                 # amortissement (<1 = rebond)
def pts12(pose):
    p = np.vstack([[0, 0], pose]); hip, neck = p[0], p[1]
    chest = (hip + neck)/2
    return np.array([hip, chest, neck, p[2], p[3], p[4], p[5], p[6], p[7], p[8], p[9], p[10]])
def rel_angles(pose):
    q = pts12(pose); ab = []; out = []
    for i, (a, b, par) in enumerate(BD):
        ang = math.atan2(q[b][1]-q[a][1], q[b][0]-q[a][0]); ab.append(ang)
        r = ang - (ab[par] if par >= 0 else 0)
        out.append((r + math.pi) % (2*math.pi) - math.pi)
    return np.array(out)
_q = pts12(P["stance"]); LEN = np.array([np.hypot(*(_q[b]-_q[a])) for a, b, _ in BD])
def fk(rel):
    q = np.zeros((12, 2)); ab = np.zeros(11)
    for i, (a, b, par) in enumerate(BD):
        ab[i] = rel[i] + (ab[par] if par >= 0 else 0)
        q[b] = q[a] + LEN[i]*np.array([math.cos(ab[i]), math.sin(ab[i])])
    return q
class Body:
    def __init__(self, pose): self.a = rel_angles(pose); self.v = np.zeros(11)
    def step(self, target, dt):
        for _ in range(4):
            d = (target - self.a + math.pi) % (2*math.pi) - math.pi
            self.v += (OMEGA**2*d - 2*ZETA*OMEGA*self.v)*dt/4
            self.a += self.v*dt/4
def skeleton2(x, h, rot, rel, facing):
    pts = fk(rel)
    r = math.radians(rot); c, s = math.cos(r), math.sin(r)
    pts = np.stack([pts[:,0]*c - pts[:,1]*s, pts[:,0]*s + pts[:,1]*c], 1)
    hip_h = h + pts[:,1].max()
    return np.stack([x + facing*pts[:,0], hip_h - pts[:,1]], 1)
SOFT = {"stance", "block", "duck"}
BEAT = 0.4587
def target_angles(pose, name, t, ph):
    tg = rel_angles(pose)
    if name in SOFT:   # respiration, balancement et rebond des genoux sur le tempo
        bob = (math.sin(2*math.pi*(t - 4.08)/BEAT) + 1)/2
        tg[0] += 0.05*math.sin(t*3.1 + ph); tg[1] += 0.07*math.sin(t*2.3 + ph)
        tg[3] += 0.12*math.sin(t*4.0 + ph); tg[5] += 0.12*math.sin(t*3.6 + ph + 1)
        tg[7] -= 0.22*bob; tg[8] += 0.38*bob; tg[9] -= 0.18*bob; tg[10] += 0.3*bob
    return tg


# ================= rendu 3D : caméra perspective, plans 3D/2D, réactions aux coups =================
FPX3D = 520.0
# plans de caméra (coupes calées sur le beat). orbit = degrés/s
SHOTS = [
 (0.0,  dict(mode="2d", follow="orb")),
 (1.7,  dict(mode="3d", yaw=40,  pitch=-8,  dist=230, orbit=14,   follow="A")),
 (2.6,  dict(mode="2d")),
 (5.45, dict(mode="3d", yaw=-55, pitch=-14, dist=340, orbit=55,   follow="both")),
 (6.84, dict(mode="2d")),
 (7.71, dict(mode="3d", yaw=25,  pitch=50,  dist=380, orbit=-25,  follow="B")),
 (8.1,  dict(mode="2d")),
 (8.87, dict(mode="3d", yaw=70,  pitch=6,   dist=270, orbit=-45,  follow="both")),
 (9.16, dict(mode="2d")),
 (10.7, dict(mode="3d", yaw=100, pitch=8,   dist=430, orbit=-135, follow="both")),
 (11.42,dict(mode="3d", yaw=28,  pitch=-12, dist=250, orbit=14,   follow="both")),
 (11.88,dict(mode="2d")),
]
def shot_at(t):
    i = max(k for k, s in enumerate(SHOTS) if s[0] <= t); return i, SHOTS[i]

# arrêts sur image (hitstop) rattrapés juste après : la synchro musique reste exacte
HITS = [(ft, fs) for ft, fx, fh, fs, kind in FX if kind in ("hit", "clash", "land") and fs >= 1]
def anim_time(t):
    lag = 0.0
    for te, fs in HITS:
        dz = 0.04 + 0.025*fs
        if te <= t < te + dz: lag += t - te
        elif te + dz <= t < te + dz + 0.2: lag += dz*(1 - (t - te - dz)/0.2)
    return t - lag

def look(T, yaw, pitch, dist):
    y, p = math.radians(yaw), math.radians(pitch)
    C = T + dist*np.array([math.sin(y)*math.cos(p), math.sin(p), math.cos(y)*math.cos(p)])
    C[1] = max(C[1], 8)
    fw = T - C; fw /= np.linalg.norm(fw)
    rt = np.cross(fw, [0, 1, 0]); rt /= np.linalg.norm(rt)
    up = np.cross(rt, fw)
    return C, fw, rt, up

ruins = []
for k in range(110):
    a = random.uniform(0, 2*math.pi); R = random.uniform(5000, 6500)
    ruins.append((100 + R*math.sin(a), -R*math.cos(a), random.uniform(80, 260), random.uniform(60, 260)))
ash = [[random.uniform(0, W), random.uniform(0, H), random.uniform(0.3, 1.2)] for _ in range(70)]
yy, xx = np.mgrid[0:H, 0:W]
vign = (1 - 0.65*(((xx-W/2)/(W*0.75))**2 + ((yy-H/2)/(H*0.7))**2)).clip(0.25, 1)[..., None]
ZOFF = np.array([0, 0, 0, 0, 7, 7, -7, -7, 7, 7, -7, -7], float)
COL = [(110, 235, 255), (255, 55, 75)]
FACING = [1, -1]
REACT = {"hit", "flail", "lie", "block"}

ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                       "-r", str(FPS), "-i", "-", "-ss", str(START), "-t", str(DUR), "-i", AUDIO,
                       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-c:a", "aac", "-shortest", OUT],
                      stdin=subprocess.PIPE)

bodies = [Body(P["tuck"]), Body(P["stance"])]
kb = np.zeros(2); kbv = np.zeros(2); hitflash = np.zeros(2)
camT = np.array([-80.0, 750.0, 0.0]); zoom = 1.0; cur_shot = -1
shake = flash = 0.0; sparks = []; rings = []; lines_t = -99; trails = [[], []]; prev = [None, None]
fired = set(); ta_prev = 0.0

for f in range(int(DUR*FPS)):
    t = f / FPS
    ta = anim_time(t); dta = ta - ta_prev; ta_prev = ta
    st = [sample(A, ta), sample(B, ta)]
    ahead = [sample(A, ta + 0.06), sample(B, ta + 0.06)]
    if dta > 0:
        for i in range(2):
            bodies[i].step(target_angles(ahead[i][3], ahead[i][4], ta, i*1.7), dta)

    # ---------- impacts + réactions ----------
    for k, (ft, fx, fh, fs, kind) in enumerate(FX):
        if k in fired or t < ft: continue
        fired.add(k)
        if kind != "dust":
            shake = max(shake, fs*7); flash = max(flash, min(1, fs/3))
        for _ in range(int(10 + fs*14)):
            grd = kind in ("land", "dust")
            a = random.uniform(0.1, math.pi-0.1) if grd else random.uniform(0, 2*math.pi)
            v = random.uniform(3, 6 + fs*4); zz = random.uniform(-1, 1)*v*0.8
            col = (255, 225, 140) if kind in ("hit", "clash") else (150, 120, 90)
            sparks.append([fx, fh, 0.0, math.cos(a)*v*(1.6 if grd else 1), math.sin(a)*v, zz, 1.0, col])
        if kind in ("land", "clash", "hit") and fs >= 1: rings.append([fx, fh, 0.0, fs, kind == "land"])
        if kind == "clash" or fs >= 2.5: lines_t = f
        # qui encaisse ? celui en pose de réaction (ou les deux sur un choc / atterrissage)
        for j in range(2):
            hitme = (st[j][4] in REACT and kind == "hit") or kind == "clash" or (kind == "land" and abs(st[j][0]-fx) < 60)
            if not hitme or abs(st[j][0] - fx) > 130: continue
            s_ = fs*(0.5 if kind == "land" else 1)
            bodies[j].v[[0, 1, 2]] += np.array([-6, -13, -24])*s_          # buste et tête projetés en arrière
            bodies[j].v[[3, 4, 5, 6]] += np.random.uniform(-20, 20, 4)*s_  # bras qui battent
            bodies[j].v[[7, 8, 9, 10]] += np.array([-8, 14, -8, 14])*s_     # genoux qui plient
            if kind != "land":
                kbv[j] += -FACING[j]*(6 + 5*fs)                              # recul
                hitflash[j] = 1.0

    # recul qui glisse puis revient doucement
    for j in range(2):
        kb[j] += kbv[j]; kbv[j] = kbv[j]*0.78 - kb[j]*0.03; hitflash[j] *= 0.6
    xs_ = [st[0][0] + kb[0], st[1][0] + kb[1]]
    sk = [skeleton2(xs_[i], st[i][1], st[i][2], bodies[i].a, FACING[i]) for i in range(2)]

    # poussière quand ça glisse au sol
    for i in range(2):
        if prev[i] is not None and st[i][1] < 2:
            vx = xs_[i] - prev[i]
            if abs(vx) > 5:
                for _ in range(2):
                    sparks.append([xs_[i], 0, random.uniform(-15, 15), -vx*0.3 + random.uniform(-2, 2),
                                   random.uniform(1, 4), random.uniform(-1, 1), 0.8, (140, 110, 80)])
        prev[i] = xs_[i]

    # ---------- caméra ----------
    si, (t0, sh) = shot_at(t)
    cut = si != cur_shot; cur_shot = si
    if cut: trails = [[], []]
    if sh.get("follow") == "orb":
        T = np.array([-80, st[0][1] - 40, 0.0]); zt = 1.25
    elif sh.get("follow") in ("A", "B"):
        j = 0 if sh["follow"] == "A" else 1
        T = np.array([xs_[j], st[j][1] + 45, 0.0]); zt = zoom
    else:
        lim = xs_[0] + (60 if t < 2.6 else 520)
        xx2 = [xs_[0], min(xs_[1], lim)]
        T = np.array([sum(xx2)/2, max(st[0][1], st[1][1])*0.55 + 60, 0.0])
        zt = float(np.clip(300/(abs(xx2[1]-xx2[0]) + 230), 0.42, 1.35))
    if cut and sh["mode"] == "3d": camT = T.copy()
    camT += (T - camT) * (0.35 if (t < 1.7 or sh["mode"] == "3d") else 0.25)
    zoom += (zt - zoom) * (1 if cut else 0.2)
    if sh["mode"] == "2d":
        yaw, pitch, dist = 0.0, 3.0, 1500.0; fpx = 1.9*zoom*dist
    else:
        yaw = sh["yaw"] + sh["orbit"]*(t - t0); pitch, dist, fpx = sh["pitch"], sh["dist"], FPX3D
    C, fw, rt, up = look(camT, yaw, pitch, dist)
    shake *= 0.82; flash *= 0.78
    ox, oy = random.uniform(-shake, shake), random.uniform(-shake, shake)
    CY = H*0.55

    def proj(p):
        v = np.asarray(p, float) - C; z = v @ fw
        if z < 4.9: return None
        return (W/2 + fpx*(v @ rt)/z + ox, CY - fpx*(v @ up)/z + oy, z)
    def seg(p, q):
        a, b = np.asarray(p, float), np.asarray(q, float)
        za, zb = (a - C) @ fw, (b - C) @ fw
        if za < 5 and zb < 5: return None
        if za < 5: a = a + (b - a)*(5 - za)/(zb - za)
        if zb < 5: b = b + (a - b)*(5 - zb)/(za - zb)
        return proj(a), proj(b)

    # ---------- ciel + sol en perspective ----------
    hd = np.array([fw[0], 0, fw[2]]); hd /= (np.linalg.norm(hd) + 1e-9)
    hy = CY - fpx*(hd @ up)/max(1e-3, hd @ fw) + oy
    rows = (np.arange(H) - hy)[:, None]
    k_ = np.clip(-rows/900, 0, 1); g_ = np.clip(rows/500, 0, 1)
    skyc = np.concatenate([18 + 30*(1-k_), 15 + 22*(1-k_), 24 + 26*(1-k_)], 1)
    grc = np.concatenate([88 - 50*g_, 66 - 40*g_, 50 - 32*g_], 1)
    img = Image.fromarray(np.repeat(np.where(rows < 0, skyc, grc)[:, None, :], W, 1).astype(np.uint8))
    d = ImageDraw.Draw(img)
    for gx in range(-800, 1001, 90):     # quadrillage au sol : rend la 3D lisible
        s_ = seg((gx, 0, -700), (gx, 0, 700))
        if s_: d.line([s_[0][:2], s_[1][:2]], fill=(70, 55, 44), width=1)
    for gz in range(-700, 701, 90):
        s_ = seg((-800, 0, gz), (1000, 0, gz))
        if s_: d.line([s_[0][:2], s_[1][:2]], fill=(70, 55, 44), width=1)
    rs = []
    for rx, rz, rw, rh in ruins:
        pb = proj((rx, 0, rz))
        if pb and pb[2] > dist + 500 and -200 < pb[0] < W + 200: rs.append((pb, rw, rh))
    for pb, rw, rh in sorted(rs, key=lambda r: -r[0][2]):
        s2 = fpx/pb[2]
        d.rectangle([pb[0] - rw*s2/2, pb[1] - rh*s2, pb[0] + rw*s2/2, pb[1]], fill=(22, 18, 24))

    glow = Image.new("RGB", (W, H)); gd = ImageDraw.Draw(glow)

    if t < 1.7:   # orbe lumineux
        pp = proj((-80, st[0][1] + 40, 0))
        if pp:
            px, py = pp[:2]
            for r, c in ((60, (90, 140, 160)), (30, (200, 240, 255))):
                gd.ellipse([px-r, py-r, px+r, py+r], fill=c)
            gd.line([px, py, px, py - 400], fill=(120, 200, 230), width=18)
            d.ellipse([px-14, py-14, px+14, py+14], fill=(255, 255, 255))

    # ombres au sol (cercles projetés)
    for i in range(2):
        if t < 1.7 and i == 0: continue
        rr = 38/(1 + st[i][1]/150)
        poly = [proj((xs_[i] + rr*math.cos(a), 0, rr*0.6*math.sin(a))) for a in np.linspace(0, 2*math.pi, 20)]
        if all(poly): d.polygon([p[:2] for p in poly], fill=(32, 25, 22))

    # ---------- bonhommes (le plus loin d'abord) ----------
    order = sorted(range(2), key=lambda i: -(((np.array([xs_[i], 60, 0]) - C) @ fw)))
    for i in order:
        if t < 1.7 and i == 0: continue
        pz = -6 if i == 0 else 6
        P3 = [(sk[i][n][0], sk[i][n][1], pz + ZOFF[n]*FACING[i]) for n in range(12)]
        scr = [proj(p) for p in P3]
        if any(p is None for p in scr): continue
        trails[i] = (trails[i] + [scr])[-5:]
        base = COL[i]
        hc = tuple(int(c + (255 - c)*hitflash[i]) for c in base)
        for j, tr in enumerate(trails[i][:-1]):
            a = (j + 1)/len(trails[i])*0.45
            for b0, b1 in BONES:
                w_ = max(2, int(4.5*fpx/tr[b0][2]))
                gd.line([tr[b0][:2], tr[b1][:2]], fill=tuple(int(v*a) for v in base), width=w_)
        for dr, mul, c in ((gd, 2, hc), (d, 1, tuple(min(255, v + 60) for v in hc))):
            for b0, b1 in BONES:
                w_ = max(2, int(4.5*mul*fpx/((scr[b0][2] + scr[b1][2])/2)))
                dr.line([scr[b0][:2], scr[b1][:2]], fill=c, width=w_)
                for p in (scr[b0], scr[b1]):
                    r_ = w_/2; dr.ellipse([p[0]-r_, p[1]-r_, p[0]+r_, p[1]+r_], fill=c)
            hx, hy2, hz = scr[3]; r_ = 11*fpx/hz
            dr.ellipse([hx-r_, hy2-r_, hx+r_, hy2+r_], fill=c)

    # ---------- particules, ondes de choc, lignes de vitesse ----------
    for s in sparks:
        s[0] += s[3]; s[1] += s[4]; s[2] += s[5]; s[4] -= 0.7; s[6] -= 0.045
        if s[1] < 0: s[1] = 0; s[4] *= -0.3; s[3] *= 0.7
        if s[6] > 0:
            q = seg((s[0], s[1], s[2]), (s[0] - s[3]*1.5, s[1] - s[4]*1.5, s[2] - s[5]*1.5))
            if q:
                c = tuple(int(v*s[6]) for v in s[7])
                gd.line([q[0][:2], q[1][:2]], fill=c, width=5); d.line([q[0][:2], q[1][:2]], fill=c, width=2)
    sparks = [s for s in sparks if s[6] > 0]
    for r in rings:
        r[2] += 1; a = max(0, 1 - r[2]/14); rad = r[2]*(14 + r[3]*6)
        col = tuple(int(255*a) for _ in range(3)); wd = max(1, int(6*a))
        if r[4]:
            poly = [proj((r[0] + rad*math.cos(u), 1, rad*math.sin(u))) for u in np.linspace(0, 2*math.pi, 28)]
            if all(poly): gd.line([p[:2] for p in poly], fill=col, width=wd)
        else:
            pc = proj((r[0], r[1], 0))
            if pc:
                rp = rad*fpx/pc[2]; gd.ellipse([pc[0]-rp, pc[1]-rp, pc[0]+rp, pc[1]+rp], outline=col, width=wd)
    rings = [r for r in rings if r[2] < 14]
    if f - lines_t < 8:
        a = 1 - (f - lines_t)/8
        for _ in range(40):
            ang = random.uniform(0, 2*math.pi); r0 = random.uniform(180, 300)
            gd.line([W/2 + math.cos(ang)*r0, H/2 + math.sin(ang)*r0, W/2 + math.cos(ang)*900, H/2 + math.sin(ang)*900],
                    fill=tuple(int(200*a) for _ in range(3)), width=2)
    for s in ash:
        s[0] = (s[0] - 1.5*s[2]) % W; s[1] = (s[1] + 0.6*s[2]) % H
        d.point((s[0], s[1]), fill=(170, 150, 130))

    arr = np.asarray(img, np.float32) + np.asarray(glow.filter(ImageFilter.GaussianBlur(10)), np.float32)*0.9 \
          + np.asarray(glow, np.float32)*0.25
    arr = arr*vign + flash*160
    if f - lines_t == 0: arr = 255 - np.clip(arr, 0, 255)
    if sh["mode"] == "3d":   # bandes cinéma pendant les plans 3D
        arr[:70] *= 0.0; arr[-70:] *= 0.0
    ff.stdin.write(np.clip(arr, 0, 255).astype(np.uint8).tobytes())

ff.stdin.close(); ff.wait()
