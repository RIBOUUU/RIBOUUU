"""Combat de bonhommes sur 3 jours (projections, décor détruit, rayon final) : chorégraphie générée sur les kicks, coups réalistes, caméra 3D/2D, jour/nuit."""
import sys, subprocess, math, random, os
SLOW = float(os.environ.get('SLOW', '1'))   # 0.5 = tout au ralenti (2x plus lent)
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

AUDIO, OUT = sys.argv[1], sys.argv[2]
W, H, FPS = 540, 960, 30
START, DUR = 28.0, 34.0
random.seed(11); np.random.seed(11)

# ============================== musique : kicks ==============================
SR = 22050; AF = 100
y = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", AUDIO, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                                 capture_output=True).stdout, np.int16) / 32768.
hop = SR // AF; fr = np.fft.rfftfreq(1024, 1/SR); band = (fr > 30) & (fr < 150)
low = np.array([np.abs(np.fft.rfft(y[i*hop:i*hop+1024]))[band].sum() for i in range(len(y)//hop - 11)])
low /= low.max()
KICKS = [i/AF - START for i in range(8, len(low)-9)
         if low[i] == low[i-8:i+9].max() and low[i] > 0.45 and START <= i/AF <= START + DUR]

# ============================== poses (face à droite, hanche = origine, y vers le bas) ==============================
# ordre : cou, tête, coude avant, main avant, coude arrière, main arrière, genou avant, pied avant, genou arrière, pied arrière
P = {
 "stance":  [(4,-58),(6,-80),(20,-44),(32,-62),(-6,-42),(14,-58),(16,24),(24,54),(-14,26),(-26,54)],
 "jab_w":   [(0,-58),(0,-80),(14,-46),(24,-60),(-8,-42),(10,-58),(16,24),(24,54),(-14,26),(-26,54)],
 "jab":     [(10,-57),(14,-78),(34,-58),(60,-62),(-6,-42),(12,-58),(18,24),(30,54),(-16,24),(-30,54)],
 "cross_w": [(-6,-57),(-10,-79),(18,-46),(30,-62),(-18,-44),(-8,-60),(16,24),(24,54),(-14,26),(-26,54)],
 "cross":   [(16,-55),(24,-76),(10,-44),(22,-60),(30,-56),(58,-62),(20,24),(32,54),(-12,26),(-34,52)],
 "hook_w":  [(-4,-57),(-6,-79),(4,-50),(-6,-66),(-8,-42),(10,-58),(16,24),(24,54),(-14,26),(-26,54)],
 "hook":    [(12,-56),(18,-77),(30,-64),(52,-60),(-6,-44),(12,-60),(18,24),(28,54),(-14,24),(-28,54)],
 "upper_w": [(10,-48),(16,-68),(18,-30),(28,-22),(-6,-36),(10,-52),(22,14),(24,44),(-18,18),(-30,44)],
 "upper":   [(10,-60),(14,-82),(30,-60),(36,-96),(-8,-42),(8,-56),(16,24),(24,54),(-18,24),(-30,54)],
 "elbow_w": [(-4,-57),(-6,-79),(-6,-56),(10,-66),(-8,-42),(10,-58),(16,24),(24,54),(-14,26),(-26,54)],
 "elbow":   [(16,-54),(24,-74),(36,-62),(14,-66),(0,-44),(16,-58),(20,24),(30,54),(-14,26),(-30,52)],
 "knee_w":  [(6,-57),(10,-78),(26,-50),(44,-60),(14,-50),(36,-60),(16,24),(24,54),(-14,26),(-26,54)],
 "knee":    [(10,-56),(16,-76),(30,-46),(40,-30),(18,-44),(30,-28),(30,-20),(36,8),(-6,26),(-12,54)],
 "kick_w":  [(-6,-57),(-10,-78),(16,-46),(28,-62),(-12,-42),(4,-58),(26,-14),(16,14),(-6,26),(-12,54)],
 "kick":    [(-12,-56),(-18,-77),(8,-48),(22,-62),(-26,-44),(-40,-28),(32,-10),(68,-32),(-4,26),(-8,54)],
 "hkick_w": [(-10,-56),(-16,-77),(12,-48),(24,-62),(-20,-44),(-30,-30),(26,-30),(8,-6),(-4,26),(-8,54)],
 "hkick":   [(-24,-50),(-36,-68),(-4,-46),(10,-60),(-34,-38),(-52,-28),(32,-32),(64,-58),(-2,26),(-6,54)],
 "bkick_w": [(-4,-56),(-6,-78),(16,-46),(28,-60),(-8,-42),(8,-58),(14,26),(18,54),(-20,6),(-6,28)],
 "bkick":   [(22,-52),(34,-70),(34,-40),(44,-26),(10,-42),(24,-30),(14,26),(18,54),(-34,-6),(-70,-12)],
 "sweep_w": [(8,-44),(14,-64),(20,-30),(30,-20),(-4,-34),(6,-24),(24,12),(26,38),(-20,18),(-34,38)],
 "sweep":   [(-16,-36),(-24,-56),(-24,-16),(-30,20),(-8,-14),(-12,20),(28,8),(62,18),(-6,14),(-26,20)],
 "hb_w":    [(-10,-56),(-18,-76),(26,-52),(48,-58),(20,-50),(42,-56),(16,24),(24,54),(-14,26),(-26,54)],
 "hb":      [(22,-52),(38,-66),(30,-50),(50,-56),(24,-48),(44,-52),(22,24),(32,54),(-12,26),(-32,52)],
 "grab":    [(10,-57),(14,-78),(30,-56),(54,-62),(26,-52),(50,-58),(18,24),(30,54),(-16,24),(-30,54)],
 "throw":   [(-24,-50),(-38,-64),(-20,-72),(-40,-86),(-14,-74),(-34,-90),(14,24),(26,54),(-18,24),(-34,52)],
 "hit_head":[(-14,-54),(-30,-68),(-2,-46),(10,-30),(-24,-44),(-36,-58),(10,24),(18,54),(-14,24),(-28,54)],
 "hit_body":[(18,-40),(30,-54),(16,-26),(14,-8),(10,-24),(8,-6),(18,20),(20,50),(-14,22),(-24,50)],
 "hit_legs":[(6,-56),(10,-76),(18,-40),(28,-56),(-8,-38),(6,-54),(22,12),(28,36),(-8,32),(-34,34)],
 "block":   [(-2,-56),(0,-78),(18,-56),(20,-78),(12,-50),(16,-70),(16,24),(26,54),(-16,24),(-30,54)],
 "parry":   [(-4,-57),(-6,-79),(24,-62),(44,-80),(4,-46),(16,-62),(16,24),(26,54),(-16,24),(-30,54)],
 "leanback":[(-22,-52),(-38,-66),(-6,-50),(4,-64),(-24,-44),(-12,-58),(14,26),(26,54),(-20,22),(-30,52)],
 "duck":    [(16,-32),(26,-48),(22,-22),(36,-34),(4,-20),(20,-30),(26,6),(22,32),(-16,16),(-30,32)],
 "tuck":    [(4,-40),(10,-58),(20,-26),(24,-6),(10,-24),(14,-4),(24,-14),(20,10),(18,-8),(10,14)],
 "land":    [(18,-44),(26,-62),(28,-20),(30,30),(0,-34),(-24,-52),(28,4),(26,30),(-10,18),(-30,30)],
 "dash":    [(30,-46),(44,-62),(16,-30),(0,-16),(10,-34),(-8,-22),(26,14),(20,40),(-20,22),(-46,36)],
 "run_a":   [(14,-56),(20,-77),(-6,-40),(4,-26),(22,-44),(36,-52),(22,14),(18,40),(-10,26),(-30,44)],
 "run_b":   [(14,-56),(20,-77),(22,-44),(36,-52),(-6,-40),(4,-26),(-10,26),(-30,44),(22,14),(18,40)],
 "flail":   [(-6,-56),(-10,-78),(-24,-70),(-36,-92),(16,-70),(30,-90),(18,18),(10,46),(-10,26),(-24,46)],
}
P.update({
 "land":    [(8,-56),(12,-78),(30,-50),(46,-40),(-16,-48),(-32,-40),(18,22),(26,52),(-16,24),(-28,52)],
 "upper_w": [(2,-56),(4,-78),(18,-36),(26,-26),(-8,-42),(10,-58),(16,24),(24,54),(-14,26),(-26,54)],
 "hit_legs":[(-8,-56),(-14,-77),(4,-46),(14,-32),(-20,-44),(-30,-58),(30,10),(48,30),(-12,26),(-22,54)],
 "hit_body":[(16,-50),(28,-66),(16,-32),(18,-12),(8,-30),(10,-10),(14,26),(20,54),(-14,26),(-24,54)],
 "charge":  [(-8,-56),(-12,-78),(-16,-34),(-28,-26),(-18,-32),(-30,-24),(16,24),(24,53),(-14,25),(-24,53)],
 "stance2": [(2,-59),(3,-81),(18,-40),(30,-52),(-8,-40),(10,-50),(14,25),(20,54),(-12,26),(-22,54)],
 "stance3": [(8,-57),(12,-78),(22,-48),(30,-70),(0,-46),(16,-66),(18,24),(28,54),(-16,25),(-30,54)],
 "fly":     [(4,-58),(6,-80),(18,-46),(30,-62),(-6,-44),(12,-60),(10,26),(4,56),(-8,24),(-18,52)],
 "dazed":   [(6,-56),(10,-77),(22,-68),(14,-84),(-12,-66),(0,-86),(14,25),(22,54),(-14,26),(-24,54)],
 "power":   [(-2,-58),(-6,-80),(16,-36),(24,-16),(-14,-36),(-22,-16),(16,24),(26,54),(-16,24),(-28,54)],
 "scream":  [(-4,-58),(-12,-79),(24,-42),(40,-28),(-24,-42),(-40,-28),(18,24),(30,53),(-18,24),(-32,53)],
 "stuck":   [(0,-58),(0,-80),(-22,-70),(-38,-90),(22,-70),(38,-90),(16,28),(30,54),(-16,28),(-30,54)],
 "rage":    [(10,-54),(18,-72),(18,-36),(20,-18),(-6,-36),(-6,-18),(16,24),(28,53),(-18,24),(-32,53)],
 "rage2":   [(-2,-58),(-8,-80),(22,-44),(30,-26),(-22,-44),(-30,-26),(16,24),(28,53),(-18,24),(-32,53)],
 "fire":    [(14,-55),(22,-76),(26,-54),(52,-54),(24,-52),(50,-50),(18,24),(28,53),(-16,25),(-28,53)],
})
P = {k: np.array(v, float) for k, v in P.items()}
def pose_of(name, t):
    if name == "run":
        s = 0.5 + 0.5*math.sin(t*2*math.pi*4); return P["run_a"]*s + P["run_b"]*(1-s)
    return P[name]

# ============================== squelette ==============================
# points : 0 hanche,1 buste,2 cou,3 tête,4 coude av,5 main av,6 coude arr,7 main arr,8 genou av,9 pied av,10 genou arr,11 pied arr
BD = [(0,1,-1),(1,2,0),(2,3,1),(2,4,1),(4,5,3),(2,6,1),(6,7,5),(0,8,-1),(8,9,7),(0,10,-1),(10,11,9)]
LEN = np.array([29, 29, 22, 22, 24, 22, 24, 30, 30, 30, 30], float)
BONES = [(0,1),(1,2),(2,3),(2,4),(4,5),(2,6),(6,7),(0,8),(8,9),(0,10),(10,11)]
OMEGA = np.array([34, 24, 15, 30, 22, 30, 22, 32, 26, 32, 26], float); ZETA = 0.55
DELAY = np.array([0.015, 0.03, 0.05, 0.04, 0.06, 0.04, 0.06, 0, 0, 0, 0])   # chaîne cinétique : jambes -> hanche -> épaule -> poing
LEAD = 0.06
def pts12(pose):
    p = np.vstack([[0, 0], pose]); return np.array([p[0], (p[0]+p[1])/2, *p[1:]])
_rel_cache = {}
def rel_angles(pose):
    q = pts12(pose); ab = []; out = []
    for a, b, par in BD:
        ang = math.atan2(q[b][1]-q[a][1], q[b][0]-q[a][0]); ab.append(ang)
        out.append((ang - (ab[par] if par >= 0 else 0) + math.pi) % (2*math.pi) - math.pi)
    return np.array(out)
def fk(rel):
    q = np.zeros((12, 2)); ab = np.zeros(11)
    for i, (a, b, par) in enumerate(BD):
        ab[i] = rel[i] + (ab[par] if par >= 0 else 0)
        q[b] = q[a] + LEN[i]*np.array([math.cos(ab[i]), math.sin(ab[i])])
    return q
def ik2(root, tgt, L1, L2, sgn):
    v = tgt - root; dist = float(np.clip(np.hypot(*v), 1e-3, L1 + L2 - 0.5)); a = math.atan2(v[1], v[0])
    b = math.acos(np.clip((L1*L1 + dist*dist - L2*L2)/(2*L1*dist), -1, 1))
    k1 = root + L1*np.array([math.cos(a+b), math.sin(a+b)]); k2 = root + L1*np.array([math.cos(a-b), math.sin(a-b)])
    e_ = root + dist*np.array([math.cos(a), math.sin(a)]); u_, f_ = k1 - root, e_ - k1
    knee = k1 if (u_[0]*f_[1] - u_[1]*f_[0])*sgn > 0 else k2   # coude / genou ne plient que dans le bon sens
    return knee, root + dist*np.array([math.cos(a), math.sin(a)])
LIMB = {"fha": (2, 4, 5, 22, 24, -1), "bha": (2, 6, 7, 22, 24, -1),
        "ffo": (0, 8, 9, 30, 30, 1), "bfo": (0, 10, 11, 30, 30, 1)}
# butées : colonne, cou, coudes (ne plient que vers l'avant), genoux (que vers l'arrière)
LO = np.array([-9, -0.6, -0.7, -9, -2.9, -9, -2.9, -9, -0.03, -9, -0.03])
HI = np.array([9, 0.6, 0.7, 9, 0.05, 9, 0.05, 9, 2.6, 9, 2.6])
END = {"fha": 5, "bha": 7, "ffo": 9, "bfo": 11, "fel": 4, "fkn": 8, "head": 3}
ZONE = {"head": 3, "chest": 1, "belly": 0.6, "legs": 8, "neck": 2}
class Body:
    def __init__(self, pose): self.a = rel_angles(pose); self.v = np.zeros(11)
    def step(self, target, dt):
        for _ in range(4):
            d = (target - self.a + math.pi) % (2*math.pi) - math.pi
            self.v += (OMEGA**2*d - 2*ZETA*OMEGA*self.v)*dt/4; self.a += self.v*dt/4
            out = (self.a < LO) | (self.a > HI)
            if out.any(): self.a = np.clip(self.a, LO, HI); self.v[out] *= -0.2

# ============================== pistes d'animation ==============================
G = 1400.0
EASE = {"grav": lambda p: p, "lin": lambda p: p, "in": lambda p: p*p, "out": lambda p: 1-(1-p)**2, "io": lambda p: p*p*(3-2*p)}
BOTH = frozenset("fb"); NONE = frozenset()
class Track:
    def __init__(s, **k): s.keys = [dict(t=0.0, x=0.0, z=0.0, h=0.0, rot=0.0, spin=0.0, pose="stance", plant=BOTH, F=1, ease="io") | k]
    def seg(s, t):
        ks = s.keys
        if t <= ks[0]["t"]: return ks[0], ks[0], 1.0
        for a, b in zip(ks, ks[1:]):
            if t <= b["t"]: return a, b, (t - a["t"])/max(1e-6, b["t"] - a["t"])
        return ks[-1], ks[-1], 1.0
    def state(s, t):
        a, b, p = s.seg(t); e = EASE[b["ease"]](p)
        q = min(1, p/0.35); q = q*q*(3-2*q)
        o = {c: a[c] + (b[c] - a[c])*e for c in ("x", "z", "h", "rot", "spin")}
        if b["ease"] == "grav":   # chute libre : trajectoire parabolique, vitesse horizontale constante
            Tq = max(1e-3, b["t"] - a["t"]); tau = min(Tq, max(0.0, t - a["t"])); vy = (b["h"] - a["h"] + 0.5*G*Tq*Tq)/Tq
            o = {c: a[c] + (b[c] - a[c])*p for c in ("x", "z", "rot", "spin")}; o["h"] = max(0.0, a["h"] + vy*tau - 0.5*G*tau*tau)
        o["pose"] = pose_of(a["pose"], t)*(1-q) + pose_of(b["pose"], t)*q
        o["name"] = b["pose"] if q > 0.5 else a["pose"]
        o["plant"] = b["plant"] if p >= 1 else (a["plant"] & b["plant"])
        o["F"] = a["F"] if p < 1 else b["F"]
        return o
    def add(s, t, **kw):
        st = s.state(t); last = [k for k in s.keys if k["t"] < t - 1e-6][-1]
        base = dict(last, t=t, x=st["x"], z=st["z"], h=st["h"], rot=st["rot"], spin=st["spin"], ease="io")
        if "dspin" in kw: base["spin"] = st["spin"] + kw.pop("dspin")
        base.update(kw)
        s.keys = [k for k in s.keys if k["t"] < t - 1e-6] + [base]
    def turn(s, t, dur=0.2):
        st = s.state(t); F = [k for k in s.keys if k["t"] <= t][-1]["F"]
        s.add(t); s.add(t + 1e-3, F=-F, spin=st["spin"] + 180); s.add(t + dur, spin=st["spin"] + 360, ease="io")

# ============================== metteur en scène ==============================
MOVES = {  # pose armée, pose frappe, membre, allonge, temps d'armé, zones, appui, rotation, poids, force
 "jab":   ("jab_w", "jab", "fha", 70, 0.12, ["head"], BOTH, 0, 3, 1.0),
 "cross": ("cross_w", "cross", "bha", 74, 0.18, ["head", "chest"], BOTH, 0, 3, 1.2),
 "hook":  ("hook_w", "hook", "fha", 58, 0.2, ["head"], BOTH, 0, 2, 1.4),
 "upper": ("upper_w", "upper", "fha", 50, 0.22, ["head"], BOTH, 0, 2, 1.8),
 "elbow": ("elbow_w", "elbow", "fel", 42, 0.15, ["head"], BOTH, 0, 1, 1.4),
 "knee":  ("knee_w", "knee", "fkn", 40, 0.16, ["belly"], frozenset("b"), 0, 1, 1.4),
 "fkick": ("kick_w", "kick", "ffo", 88, 0.2, ["belly", "chest"], frozenset("b"), 0, 2, 1.5),
 "hkick": ("hkick_w", "hkick", "ffo", 84, 0.26, ["head"], frozenset("b"), 0, 2, 2.0),
 "bkick": ("bkick_w", "bkick", "bfo", 86, 0.3, ["chest", "belly"], frozenset("f"), 180, 1, 2.2),
 "headb": ("hb_w", "hb", "head", 36, 0.18, ["head"], BOTH, 0, 1, 1.6),
 "throw": ("grab", "grab", "fha", 50, 0.2, ["neck"], BOTH, 0, 1, 2.4),
}
REACT_POSE = {"head": "hit_head", "neck": "hit_head", "chest": "hit_body", "belly": "hit_body", "legs": "hit_legs"}
T = [Track(x=-80, h=950, pose="tuck", plant=NONE, F=1), Track(x=700, F=-1)]
IKS = [[], []]; FX = []; SHOT3 = []
def fx(t, kind, s, at, victim=None, zone=None): FX.append(dict(t=t, kind=kind, s=s, at=at, victim=victim, zone=zone))
def shot3(t0, t1, **k):
    if all(t1 < a or t0 > b for a, b, _ in SHOT3): SHOT3.append((t0, t1, k))
RAMPS = []
def slowmo(ti, v, t_next, S=0.8, C=0.32, rate=0.3):
    """Ralenti à l'impact (vue 3D qui tourne), puis accélération pour rester calé sur la musique."""
    t0 = ti - 0.08
    if t_next - t0 < S + C + 0.05 or t0 + S + C > TC - 0.3: return False
    if any(not (t0 + S + C < a or t0 > a + b + c) for a, b, c, _ in RAMPS): return False
    if not all(t0 + S < a or t0 > b for a, b, _ in SHOT3): return False
    RAMPS.append((t0, S, C, rate))
    shot3(t0, t0 + S, yaw=random.choice([-1, 1])*random.uniform(40, 70), pitch=random.choice([-8, 6, 20]), dist=300,
          orbit=random.choice([-1, 1])*40, follow="A" if v == 0 else "B")
    return True
def rshot(t0, t1):
    shot3(t0, t1, yaw=random.choice([-1, 1])*random.uniform(30, 80), pitch=random.choice([-12, -6, 8, 40]),
          dist=random.uniform(250, 380), orbit=random.choice([-1, 1])*random.uniform(20, 60), follow="both")

# --- intro : l'orbe tombe à l'aube, le rouge arrive en courant ---
T[0].add(1.7, h=0, pose="land", plant=NONE, ease="in"); T[0].add(2.6, pose="land")
T[0].add(3.3, pose="stance", plant=BOTH); T[0].add(3.9, x=10)
T[1].add(2.3, pose="run", plant=NONE, ease="lin"); T[1].add(3.5, x=170, ease="lin")
T[1].add(3.75, x=125, pose="leanback", plant=BOTH, ease="out"); T[1].add(4.0, pose="stance")
fx(1.7, "land", 3, (0, 0)); fx(3.6, "dust", 0.6, (1, 9))
shot3(1.7, 2.6, yaw=40, pitch=-8, dist=230, orbit=14, follow="A")

FLIGHTS = []; PROJ = []
MOUNTS = []
for k in range(26):   # chaîne lointaine tout autour
    an = random.uniform(-math.pi, math.pi); R = random.uniform(7000, 9500)
    MOUNTS.append(dict(xc=R*math.sin(an), zc=-R*math.cos(an), r=random.uniform(900, 1700), h=random.uniform(700, 1500), near=False))
MOUNTS = []   # terrain totalement plat
for xc in []:
    MOUNTS.append(dict(xc=xc + random.uniform(-150, 150), zc=-950, r=random.uniform(230, 300), h=random.uniform(280, 360), near=True))
def dazed(d, t0, t_next):   # sonné : se tient la tête, titube
    if t_next - 0.55 - t0 < 0.8 or random.random() < 0.35: return
    dur = min(1.4, t_next - 0.55 - t0); Td = T[d]; x0 = Td.state(t0)["x"]
    Td.add(t0 + 0.15, pose="dazed")
    for k in range(1, int(dur/0.3)): Td.add(t0 + 0.15 + k*0.3, x=x0 + random.uniform(-14, 14), pose="dazed")
    Td.add(t0 + dur, pose="stance")

RAGE = []; THEME_T = []
def strike(a, d, m, ti, outc, kd, wu, t_next, air=False, last=False, rage=False, avail=None):
    Ta, Td = T[a], T[d]; ts = ti - wu
    sa, sd = Ta.state(ts), Td.state(ti); Fa = sa["F"]; hv = sd["h"]
    if hv > 8 or abs(sd["x"] - sa["x"]) > 160:
        if m in ("throw", "knee", "headb"): m = "cross"
        if outc != "hit" and hv > 8 and not air: outc = "hit"
    if air and outc == "dodge": outc = "block"
    wp, sp, limb, reach, _, zones, plant, spin, _, power = MOVES[m]
    zone = random.choice(zones); zi = ZONE[zone]
    xa_imp = sd["x"] - Fa*reach + (Fa*10 if outc == "dodge" else 0)
    far = abs(xa_imp - sa["x"]) > 50
    if far and avail:   # la poursuite démarre plus tôt pour qu'on la voie (vitesse ~1800/s)
        lead = min(max(wu, abs(xa_imp - sa["x"])/1800), avail)
        if lead > wu + 0.02: ts = ti - lead; sa = Ta.state(ts)
    chase = far or hv > 8 or sa["h"] > 8
    rest, hrest, prest = ("fly", hv, NONE) if air else ("stance", 0, BOTH)
    sk = lambda f_: ({"dspin": spin*f_} if spin else {})
    Ta.add(ts)
    if chase:
        Ta.add(ts + (ti - ts)*0.6, pose="dash" if far else wp, x=sa["x"] + (xa_imp - sa["x"])*0.75, h=sa["h"] + (hv - sa["h"])*0.7, plant=NONE, ease="in", **sk(0.3))
        Ta.add(ti, pose=sp, x=xa_imp, h=hv, plant=NONE, ease="out", **sk(0.7))
    else:
        Ta.add(ts + wu*0.6, pose=wp, x=sa["x"] - Fa*3 + (xa_imp - sa["x"])*0.2, plant=plant, ease="out", **sk(0.3))
        Ta.add(ti, pose=sp, x=xa_imp, plant=plant, ease="in", **sk(0.7))
    if outc in ("hit", "block") and m != "throw":
        Ta.add(ti + 0.14, pose=sp, x=xa_imp + Fa*6, h=hv, ease="out")
        if hv > 8 and not air:   # retombe avec la gravité
            Ta.add(ti + 0.08 + math.sqrt(2*hv/G) + 0.05, pose="stance", x=xa_imp + Fa*16, h=0, ease="grav", **sk(1.0)); Ta.add(ti + 0.6, plant=BOTH)
        else:
            Ta.add(ti + 0.36, pose=rest, x=xa_imp + Fa*12, h=hrest, plant=prest, **sk(1.0))
    elif m != "throw":
        Ta.add(ti + 0.12, pose=sp if spin else "dash", x=xa_imp + Fa*28, h=hv, ease="out")
        Ta.add(ti + 0.45, pose=rest, x=xa_imp + Fa*20, h=hrest, plant=prest, **sk(1.0))
    if limb in LIMB:
        tgt = {"hit": ("zone", d, zi, (0, 0)), "block": ("joint", d, 5, (0, 0)),
               "dodge": ("fix", d, zi, (0, 0)), "parry": ("fix", d, zi, (0, 30))}[outc]
        IKS[a].append(dict(t0=ts + wu*0.3, t1=ti, t2=ti + 0.3, limb=limb, tgt=tgt, cap=None))
    xd = sd["x"]
    if m == "throw" and outc == "hit":
        IKS[a].append(dict(t0=ts, t1=ti, t2=ti + 0.3, limb="bha", tgt=("zone", d, 2, (0, 0)), cap=None))
        Ta.add(ti + 0.35, pose="throw", x=xa_imp - Fa*6); Ta.add(ti + 0.7, pose="stance", plant=BOTH)
        Td.add(ti); Td.add(ti + 0.06, pose="flail", plant=NONE)
        Td.add(ti + 0.95, x=xa_imp - Fa*700, h=0, rot=-270, pose="flail", ease="grav"); Td.add(ti + 1.0, pose="hit_head")
        Td.add(ti + 1.2, x=xa_imp - Fa*840, ease="out")
        fx(ti, "hit", 1.0, (d, 2), d, "neck"); fx(ti + 0.95, "land", 2.6, (d, 0), d)
        FLIGHTS.append((xd, xa_imp - Fa*700))
        Ta.turn(ti + 0.8)
        tg = max(ti + 1.4, t_next - 1.3)
        Td.add(tg); Td.add(tg + 0.3, rot=-360, pose="stance", h=0); Td.add(tg + 0.4, plant=BOTH); Td.turn(tg + 0.42)
        slowmo(ti, d, t_next) or rshot(ti - 0.2, ti + 1.2); return
    if outc == "hit":
        fx(ti, "hit", power, (d, zi), d, zone)
        rp = REACT_POSE[zone]
        if rage:   # projeté, rebondit deux fois, retombe sur ses pieds... et il est furieux
            D1 = 380 + 100*power; t1_ = ti + 0.38; t2_ = t1_ + 0.3; tl = t2_ + 0.25
            Td.add(ti); Td.add(ti + 0.05, pose="flail", x=xd + Fa*30, h=hv + 8, rot=-20, plant=NONE, ease="out")
            Td.add(t1_, pose="flail", x=xd + Fa*D1, h=0, rot=-300, ease="grav")
            Td.add(t2_, pose="flail", x=xd + Fa*(D1 + 230), h=0, rot=-560, ease="grav")
            Td.add(tl, pose="rage", x=xd + Fa*(D1 + 380), h=0, rot=-720, ease="grav")
            Td.add(tl + 0.05, plant=BOTH)
            fx(t1_, "land", 2.0, (d, 0), d); fx(t2_, "land", 1.5, (d, 0), d)
            FLIGHTS.append((xd, xd + Fa*(D1 + 380)))
            t0 = tl + 0.06; S_ = 0.8; C_ = (t_next - 0.12) - (t0 + S_)
            if C_ < 0.2: S_ = max(0.4, (t_next - 0.12 - t0) - 0.25); C_ = (t_next - 0.12) - (t0 + S_)
            RAMPS.append((t0, S_, C_, 0.25))
            SHOT3[:] = [x for x in SHOT3 if x[1] < t0 or x[0] > t0 + S_]
            SHOT3.append((t0, t0 + S_, dict(yaw=-Fa*random.uniform(30, 55), pitch=-8, dist=190, orbit=Fa*25, follow="A" if d == 0 else "B")))
            tla = t0 + 0.25*S_
            Td.add(tl + 0.08, pose="rage"); Td.add(tla - 0.08, pose="rage2", ease="out"); Td.add(tla - 0.01, pose="rage2")
            fx(tl + 0.08, "rage", 2.0, (d, 0), d)
            xr = xd + Fa*(D1 + 380)
            Td.add(tla, pose="dash", plant=NONE, ease="in")
            xa_ = Ta.state(t_next - 0.3)["x"]
            Td.add(t_next - 0.3, x=xa_ + Fa*130, pose="dash", ease="in")
            fx(tla, "erupt", 5, ("pt", xr + Fa*40, 0, 0))   # le sol explose derrière lui
            THEME_T.append(tla); RAGE.append((tl + 0.05, t_next + 0.9, d))
            return
        if not air and power >= 1.2 and t_next - ti >= 1.85 and hv < 8 and random.random() < 0.75:
            Ph = 0.0; Pz = 0.0; Px = xd + Fa*random.uniform(450, 700); tm = ti + 0.5
            Td.add(ti); Td.add(ti + 0.05, pose="flail", x=xd + Fa*15, h=hv + 10, plant=NONE, ease="out")
            Td.add(tm, pose="stuck", x=Px, h=0, z=0, rot=-90, ease="grav")
            for k in range(1, 3): Td.add(tm + k*0.25, pose="stuck", x=Px + random.uniform(-1.5, 1.5))
            Td.add(tm + 0.7, pose="fly", rot=0, h=40)
            Td.add(tm + 1.15, x=xa_imp + Fa*140, h=0, z=0, pose="stance", ease="io"); Td.add(tm + 1.2, plant=BOTH)
            fx(tm, "land", 3.4, ("pt", Px, 0, 0), d); fx(tm + 0.65, "breakout", 2.0, ("pt", Px, Ph, Pz))
            slowmo(ti, d, t_next) or shot3(ti - 0.1, tm + 0.8, yaw=30, pitch=8, dist=600, orbit=12, follow="A" if d == 0 else "B")
            return
        if air and not last:   # en plein vol : repoussé, se rattrape en l'air
            D = 600 + 250*power
            Td.add(ti); Td.add(ti + 0.05, pose=rp, x=xd + Fa*D*0.2, plant=NONE, ease="out")
            Td.add(ti + 0.55, x=xd + Fa*D, h=hv + random.uniform(-25, 35), ease="out"); Td.add(ti + 0.75, pose="fly")
            return
        if air and last:       # écrasé au sol depuis le ciel
            Td.add(ti); Td.add(ti + 0.04, pose="flail", x=xd + Fa*10, plant=NONE, ease="out")
            tl = ti + 0.04 + max(0.3, math.sqrt(2*hv/G)*0.75)
            Td.add(tl, pose="flail", x=xd + Fa*500, h=0, rot=-450, ease="grav"); Td.add(tl + 0.05, pose="hit_head")
            Td.add(tl + 0.5, x=xd + Fa*680, ease="out")
            fx(tl, "land", 3.0, (d, 0), d)
            tg = max(tl + 0.5, min(t_next - 1.3, tl + 1.3))
            Td.add(tg); Td.add(tg + 0.32, rot=-360, pose="stance", ease="out"); Td.add(tg + 0.42, plant=BOTH)
            dazed(d, tg + 0.42, t_next)
            Ta.add(ti + 0.5, h=hv, pose="fly"); Ta.add(ti + 1.2, h=0, pose="stance", ease="io"); Ta.add(ti + 1.25, plant=BOTH)
            slowmo(ti, d, t_next) or rshot(ti - 0.2, ti + 0.9); return
        D = 650 + 260*power + random.uniform(0, 150)       # expulsé extrêmement loin
        fly = 0.7 + 0.12*power
        tumble = power >= 1.8 or zone == "legs" or kd
        sg = 1 if zone == "legs" else -1
        Td.add(ti); Td.add(ti + 0.05, pose="flail" if tumble else rp, x=xd + Fa*D*0.08, h=hv + 6, rot=sg*20 if tumble else -15, plant=NONE, ease="out")
        FLIGHTS.append((xd, xd + Fa*D))
        if tumble:   # vrille, retombe avec la gravité, glisse, se relève
            Td.add(ti + fly, pose="flail", x=xd + Fa*D, h=0, rot=sg*450, ease="grav"); Td.add(ti + fly + 0.06, pose="hit_head")
            Td.add(ti + fly + 0.5, x=xd + Fa*(D + 200), ease="out")
            fx(ti + fly, "land", 1.9, (d, 0), d)
            tg = ti + fly + (max(0.4, min(1.4, t_next - ti - fly - 1.0)) if kd else 0.4)
            Td.add(tg); Td.add(tg + 0.32, rot=sg*360, h=0, pose="stance", ease="out"); Td.add(tg + 0.42, plant=BOTH)
            dazed(d, tg + 0.42, t_next)
        else:        # retombe sur ses pieds et dérape
            Td.add(ti + fly, pose="leanback", x=xd + Fa*D, h=0, rot=0, ease="grav")
            Td.add(ti + fly + 0.5, x=xd + Fa*(D + 200), ease="out")
            Td.add(ti + fly + 0.62, pose="stance", plant=BOTH)
            fx(ti + fly, "dust", 1.2, (d, 9))
        if power >= 1.5: slowmo(ti, d, t_next) or (power >= 1.8 and rshot(ti - 0.25, ti + 0.8))
    elif outc == "block":
        Td.add(ts + wu*0.3, pose="block"); Td.add(ti)
        Td.add(ti + 0.5, x=xd + Fa*(260 + 120*power), plant=NONE, ease="out"); Td.add(ti + 0.5, pose=rest, plant=prest)
        fx(ti, "block", 0.9, (d, 5), d, "block")
    elif outc == "parry":
        Td.add(ti - 0.1, pose="parry"); Td.add(ti + 0.35, x=xd + Fa*160, pose=rest, ease="out")
        Ta.add(ti + 0.02); Ta.add(ti + 0.4, x=xa_imp - Fa*220, pose="leanback", plant=NONE, ease="out"); Ta.add(ti + 0.55, pose=rest, plant=prest)
        if limb in LIMB: IKS[d].append(dict(t0=ti - 0.16, t1=ti, t2=ti + 0.2, limb="fha", tgt=("joint", a, END[limb], (0, 0)), cap=None))
        fx(ti, "parry", 0.7, (a, END[limb]), a, "head")
    else:
        if zone in ("head", "neck"):
            Td.add(ti - 0.14, pose="leanback", x=xd + Fa*10, ease="out"); Td.add(ti + 0.3, pose="stance")
        else:
            Td.add(ti - 0.16, pose="leanback", plant=NONE); Td.add(ti - 0.02, h=26, x=xd + Fa*34, ease="out")
            Td.add(ti + 0.2, h=0, x=xd + Fa*50, pose="stance", ease="grav"); Td.add(ti + 0.25, plant=BOTH)
        fx(ti, "whoosh", 0.4, (a, END[limb]))

# --- finale : le dernier gros kick déclenche le tir ---
TF = max([k for k in KICKS if DUR - 2.6 <= k <= DUR - 1.8] or [DUR - 2.2]); TC = TF - 5.6
WIN, LOS = 0, 1

ks = [k for k in KICKS if 4.08 <= k < TC - 0.6]
groups, cur = [], [ks[0]]
for k in ks[1:]:
    if k - cur[-1] <= 0.62 and len(cur) < 4: cur.append(k)
    else: groups.append(cur); cur = [k]
groups.append(cur)
upright_ = lambda s_: abs(((s_["rot"] + 180) % 360) - 180) < 1 and s_["h"] < 1
att, last_m = 0, None
RAGE_G = []
for gi_ in range(3, len(groups)):
    gp__ = groups[gi_][0] - groups[gi_-1][-1]
    if gp__ >= 2.0 and groups[gi_][0] < TC - 1 and len(RAGE_G) < 2 and (not RAGE_G or gi_ - RAGE_G[-1] >= 3): RAGE_G.append(gi_)
RAGED = None
for gi, g in enumerate(groups):
    a, d = att, 1 - att
    if gi in RAGE_G and RAGED is not None: a, d = RAGED, 1 - RAGED
    t_next = groups[gi+1][0] if gi + 1 < len(groups) else TC
    tp = g[0] - 0.7
    sa, sd = T[a].state(tp), T[d].state(tp)
    gp_ = g[0] - (groups[gi-1][-1] if gi else 4.0)
    if gi >= 1 and gp_ >= 1.45 and random.random() < 0.8 and not gi % 3 == 2 and gi not in RAGE_G:
        tb0 = g[0] - gp_ + 0.35                      # rafale de boules d'énergie
        sa_, sd_ = T[a].state(tb0 - 0.02), T[d].state(tb0 - 0.02)
        tls = [tb0 + k*0.12 for k in range(6)]
        if abs(sa_["z"]) < 5 and abs(sd_["z"]) < 5 and tls[-1] + 0.3 < g[0] - 0.35:
            Fa_ = 1 if sd_["x"] > sa_["x"] else -1
            for i_, s_ in ((a, sa_), (d, sd_)):   # se stabilisent (au sol ou en vol)
                T[i_].add(tb0 - 0.45); T[i_].add(tb0 - 0.2, rot=round(s_["rot"]/360)*360, pose="fly" if s_["h"] > 20 else "stance", ease="out")
            if (sd_["x"] - sa_["x"])*sa_["F"] < 0: T[a].turn(tb0 - 0.19)
            T[a].add(tb0 - 0.12); T[d].add(tb0)
            for k, tl in enumerate(tls): T[a].add(tl, pose="jab" if k % 2 == 0 else "cross", ease="out"); T[a].add(tl + 0.07, pose="fly" if sa_["h"] > 20 else "stance2")
            T[d].add(tls[0] + 0.1, pose="block")
            for k, tl in enumerate(tls):
                PROJ.append(dict(t0=tl, t1=tl + 0.26, a=a, d=d, miss=k % 2 == 1, cap=None, done=False))
                if k % 2 == 0: T[d].add(tl + 0.26, x=T[d].state(tl + 0.26)["x"] + Fa_*70, pose="block", ease="out")
            T[d].add(tls[-1] + 0.5, pose="fly" if sd_["h"] > 20 else "stance")
            sa, sd = T[a].state(tp), T[d].state(tp)
    if (sd["x"] - sa["x"])*sa["F"] < 0: T[a].turn(tp - 0.25)
    gap_prev = g[0] - (groups[gi-1][-1] if gi else 4.0)
    air = gi % 3 == 2 and gap_prev > 0.8 and gi not in RAGE_G and (gi + 1) not in RAGE_G
    if air:   # ils s'envolent pour se battre dans le ciel
        Hair = random.uniform(150, 230)
        for i_ in (a, d):
            s_ = T[i_].state(g[0] - 0.8)
            T[i_].add(g[0] - 1.1); T[i_].add(g[0] - 0.95, pose="power", h=0, z=0, rot=round(s_["rot"]/360)*360, plant=BOTH, ease="out")
            T[i_].add(g[0] - 0.62, pose="power")                       # concentre son énergie pour décoller
            T[i_].add(g[0] - 0.5, pose="fly", plant=NONE, ease="out")
            T[i_].add(g[0] - 0.22, h=Hair + (12 if i_ == a else 0), ease="out")
            fx(g[0] - 0.95, "power", 1.6, (i_, 9)); fx(g[0] - 0.5, "dust", 1.6, (i_, 9))
        shot3(g[0] - 0.8, g[0] - 0.1, yaw=random.choice([-50, 50]), pitch=-25, dist=380, orbit=20, follow="both")
    for si, ti in enumerate(g):
        last = si == len(g) - 1
        prev = g[si-1] if si else ti - 0.6
        avail = ti - prev - 0.07
        nxt_gap = t_next - ti
        cands = [m for m, M in MOVES.items() if M[4] <= avail and m != last_m
                 and (m != "throw" or (last and nxt_gap > 2.2 and not air)) and not (air and m in ("knee", "headb", "bkick"))]
        if not cands: cands = ["jab"]
        m = random.choices(cands, [MOVES[c][8] for c in cands])[0]; last_m = m
        wu = min(MOVES[m][4], max(0.06, avail))
        outc = "hit" if (m == "throw" or (air and last)) else random.choices(["hit", "block", "dodge", "parry"],
                                                       [0.85, 0.07, 0.04, 0.04] if last else [0.62, 0.16, 0.12, 0.1])[0]
        kd = outc == "hit" and last and nxt_gap > 1.9 and random.random() < 0.6
        rg = last and (gi + 1) in RAGE_G and not air
        if rg or (gi in RAGE_G and si == 0):   # coup qui déclenche la rage / contre-attaque furieuse
            m = "cross" if MOVES["hkick"][4] > avail else "hkick"; wu = min(MOVES[m][4], max(0.06, avail)); outc = "hit"; kd = False
        strike(a, d, m, ti, outc, kd, wu, t_next, air, last, rg, avail)
        if rg: RAGED = d
        if outc == "parry": a, d = d, a
    att = d if random.random() < 0.7 else a

# --- finale : le rouge est sonné ; le bleu se transforme (cheveux dorés), puis charge son rayon ---
for i_ in (WIN, LOS): T[i_].add(TC)
sw, sl = T[WIN].state(TC), T[LOS].state(TC)
xl = sl["x"]
T[LOS].add(TC + 0.4, rot=round(sl["rot"]/360)*360, h=0, z=0, pose="dazed", ease="grav" if sl["h"] > 1 else "out"); T[LOS].add(TC + 0.45, plant=BOTH)
if (sl["x"] - sw["x"])*sw["F"] < 0: T[WIN].turn(TC)
if (sw["x"] - sl["x"])*sl["F"] < 0: T[LOS].turn(TC + 0.46)
Fw = T[WIN].state(TC + 0.25)["F"]; xw = xl - Fw*320
DK0 = TC + 0.8; T_SSJ = TC + 2.3
T[WIN].add(TC + 0.15); T[WIN].add(TC + 0.6, x=xw, h=0, z=0, pose="land", plant=NONE, rot=round(sw["rot"]/360)*360, ease="grav")
T[WIN].add(TC + 0.8, pose="power", plant=BOTH)
for k in range(1, 4): T[WIN].add(TC + 0.8 + k*0.37, pose="power", x=xw + random.uniform(-3, 3))   # la puissance monte
T[WIN].add(T_SSJ - 0.05, pose="power"); T[WIN].add(T_SSJ + 0.1, pose="scream", ease="out"); T[WIN].add(T_SSJ + 0.65, pose="scream")
T[WIN].add(T_SSJ + 0.9, pose="charge")
for k in range(1, 6): T[WIN].add(T_SSJ + 0.9 + k*0.4, pose="charge", x=xw + random.uniform(-3, 3))
T[WIN].add(TF - 0.06, pose="charge"); T[WIN].add(TF, pose="fire", ease="out")
T[WIN].add(TF + 1.0, x=xw - Fw*22, pose="fire"); T[WIN].add(DUR + 1, pose="fire")
for k in range(1, 6): T[LOS].add(TC + 0.45 + k*0.3, x=xl + random.uniform(-14, 14), pose="dazed")
T[LOS].add(T_SSJ, pose="stance"); T[LOS].add(T_SSJ + 0.15, pose="leanback", x=xl + Fw*25, ease="out")   # soufflé par la transformation
T[LOS].add(T_SSJ + 0.7, pose="stance"); T[LOS].add(TF - 0.55, pose="block"); T[LOS].add(TF + 0.12, pose="block")
T[LOS].add(TF + 1.0, x=xl + Fw*115, pose="block", plant=NONE, ease="lin")
T[LOS].add(TF + 1.05, pose="flail")
T[LOS].add(TF + 2.25, x=xl + Fw*1400, h=0, rot=-1080, pose="flail", ease="grav")
fx(T_SSJ, "ssj", 4, (WIN, 1)); fx(TF, "clash", 3.5, (WIN, 5)); fx(TF + 0.12, "block", 1.5, (LOS, 5), LOS, "block"); fx(TF + 1.0, "boom", 5, (LOS, 1))
BEAM = dict(tc=T_SSJ + 0.9, t0=TF, tk=TF + 0.12, tb=TF + 1.0, t1=TF + 2.0, who=WIN, vic=LOS)
FINAL_WALLS = [xl + Fw*380, xl + Fw*700, xl + Fw*1020]
shot3(TC + 0.8, T_SSJ, yaw=55, pitch=-14, dist=330, dolly=-60, orbit=-20, follow="A")
shot3(T_SSJ, T_SSJ + 0.9, yaw=Fw*25, pitch=-10, dist=170, dolly=-20, orbit=10, follow="A")
shot3(T_SSJ + 0.9, T_SSJ + 1.7, yaw=-Fw*40, pitch=2, dist=210, dolly=-30, orbit=8, follow="B")
shot3(TF - 0.5, TF, yaw=Fw*35, pitch=-4, dist=150, dolly=-50, orbit=0, follow="A")
shot3(TF, TF + 1.0, yaw=-Fw*28, pitch=5, dist=520, orbit=Fw*6, follow="A")
shot3(TF + 1.0, DUR + 1, yaw=Fw*55, pitch=8, dist=430, orbit=0, follow="B")

# --- jamais immobiles : petits pas, changements de garde, flottement en vol ---
for i_ in range(2):
    ks_ = T[i_].keys; new = [ks_[0]]
    for k0, k1 in zip(ks_, ks_[1:]):
        if k0["pose"] in ("stance", "fly") and k1["pose"] in ("stance", "fly") and k1["t"] - k0["t"] > 0.7 and k0["plant"] == k1["plant"] and k1["ease"] != "grav":
            n = int((k1["t"] - k0["t"])/0.4)
            for j in range(1, n):
                tt = k0["t"] + (k1["t"] - k0["t"])*j/n; s_ = T[i_].state(tt)
                kk = dict(k0, t=tt, x=s_["x"] + random.uniform(-14, 14), h=s_["h"] + (random.uniform(-12, 12) if s_["h"] > 20 else 0),
                          rot=s_["rot"], spin=s_["spin"], ease="io")
                if k0["pose"] == "stance": kk["pose"] = random.choice(["stance", "stance2", "stance3"])
                new.append(kk)
        new.append(k1)
    T[i_].keys = new

# plans de caméra : 2D par défaut, 3D sur les gros moments + un plan large à chaque lever du soleil
DAY = 10.5; SUNRISE0 = 1.8
for k in range(1, 3): shot3(SUNRISE0 + k*DAY - 0.2, SUNRISE0 + k*DAY + 1.3, yaw=-35, pitch=14, dist=560, orbit=22, follow="both")
SHOT3.sort()
def shot_at(t):
    if t < 1.7: return ("orb", None)
    for i, (a, b, k) in enumerate(SHOT3):
        if a <= t < b: return (i, k)
    return ("2d", None)

HITS = []
_last = -9
for e in sorted(FX, key=lambda e: e["t"]):
    te = e["t"]
    if e["kind"] in ("hit", "block", "parry") and te < TC - 0.5 and te - _last > 0.42 \
       and all(not (te - 0.05 < a + b + c and te + 0.45 > a) for a, b, c, _ in RAMPS):
        RAMPS.append((te, 0.24, 0.17, 0.3)); _last = te   # 0,24 s à 30 % puis rattrapage en 0,17 s
RAMPS.sort()
def anim_time(t):   # ralentis + arrêts sur image, toujours rattrapés : synchro musique conservée
    for t0, S_, C_, r_ in RAMPS:
        if t0 <= t < t0 + S_ + C_:
            if t < t0 + S_: return t0 + r_*(t - t0)
            return t0 + r_*S_ + (t - t0 - S_)*((S_ + C_) - r_*S_)/C_
    lag = 0.0
    for te, s in HITS:
        dz = 0.06 + 0.035*s
        if te <= t < te + dz: lag += t - te
        elif te + dz <= t < te + dz + 0.2: lag += dz*(1 - (t - te - dz)/0.2)
    return t - lag

# ============================== ciel : jour / nuit ==============================
def mix(a, b, w): return tuple(a[i] + (b[i] - a[i])*w for i in range(3))
NIGHT = ((6, 8, 22), (20, 22, 46)); TWI = ((62, 48, 112), (255, 128, 70)); DAYC = ((62, 124, 210), (178, 204, 232))
THEMES = ["base", "volcan", "glace"]
def theme_at(ta_):
    return sum(1 for x in THEME_T if ta_ >= x)
def sky_state(t):
    ph = 2*math.pi*(t - SUNRISE0)/DAY; e = math.sin(ph)
    if e < 0: w = min(1, -e/0.35); top, hor = mix(TWI[0], NIGHT[0], w), mix(TWI[1], NIGHT[1], w)
    else: w = min(1, e/0.4); top, hor = mix(TWI[0], DAYC[0], w), mix(TWI[1], DAYC[1], w)
    L = 0.32 + 0.68*float(np.clip((e + 0.2)/0.5, 0, 1))
    return ph, e, top, hor, L
STARS = [(random.uniform(-1.6, 1.6), random.uniform(0.08, 1.2), random.uniform(0, 6)) for _ in range(160)]
CLOUDS = [[random.uniform(-1.6, 1.6), random.uniform(0.12, 0.7), random.uniform(40, 90)] for _ in range(9)]
try:
    FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 46)
except OSError:
    FONT = ImageFont.load_default()

# ============================== rendu ==============================
def look(Tg, yaw, pitch, dist):
    yw, p = math.radians(yaw), math.radians(pitch)
    C = Tg + dist*np.array([math.sin(yw)*math.cos(p), math.sin(p), math.cos(yw)*math.cos(p)]); C[1] = max(C[1], 8)
    fw = Tg - C; fw /= np.linalg.norm(fw); rt = np.cross(fw, [0, 1, 0]); rt /= np.linalg.norm(rt)
    return C, fw, rt, np.cross(rt, fw)
ruins = []
for k in range(110):
    an = random.uniform(0, 2*math.pi); R = random.uniform(5000, 6500)
    ruins.append((100 + R*math.sin(an), -R*math.cos(an), random.uniform(80, 260), random.uniform(60, 260)))
DUST3 = [[random.uniform(-700, 700), random.uniform(10, 270), random.uniform(-700, 700), random.uniform(-0.8, 0.8)] for _ in range(90)]
ash = [[random.uniform(0, W), random.uniform(0, H), random.uniform(0.3, 1.2)] for _ in range(60)]
yy, xx = np.mgrid[0:H, 0:W]
vign = (1 - 0.6*(((xx-W/2)/(W*0.75))**2 + ((yy-H/2)/(H*0.7))**2)).clip(0.3, 1)[..., None]
ZOFF = np.array([0, 0, 0, 0, 7, 7, -7, -7, 7, 7, -7, -7], float)
COL = [(110, 235, 255), (255, 55, 75)]

# piliers de pierre le long de l'arène (placés là où le combat passe)
_xs = [T[i].state(tt)["x"] for i in range(2) for tt in np.arange(2.5, DUR - 0.5, 0.1)]
PILLARS = []
px_ = min(_xs) - 350
while px_ < max(_xs) + 350:
    z_ = random.uniform(-110, -45); w_ = random.uniform(26, 46)
    PILLARS.append(dict(kind="pillar", x=px_, z0=z_ - w_/2, z1=z_ + w_/2, w=w_, h=random.uniform(90, 230), alive=True))
    px_ += random.uniform(130, 240)
for x0_, x1_ in FLIGHTS:
    if False:
        wx = x0_ + (x1_ - x0_)*0.55
        if all(abs(p["x"] - wx) > 170 for p in PILLARS if p["kind"] == "wall"):
            PILLARS[:] = [p for p in PILLARS if abs(p["x"] - wx) > 60]
            PILLARS.append(dict(kind="wall", x=wx, z0=-90, z1=55, w=26, h=random.uniform(170, 215), alive=True))
for wx in []:
    PILLARS[:] = [p for p in PILLARS if abs(p["x"] - wx) > 60]
    PILLARS.append(dict(kind="wall", x=wx, z0=-90, z1=55, w=26, h=random.uniform(200, 260), alive=True))
CRATERS = []; MARKS = []; DEBRIS = []; MCRATERS = []
LAVA = []
for k in range(70):
    x_, z_ = random.uniform(min(_xs) - 500, max(_xs) + 500), random.uniform(-420, 600); pl = [(x_, 0.6, z_)]
    an = random.uniform(0, 2*math.pi)
    for j in range(6):
        an += random.uniform(-0.7, 0.7); x_ += math.cos(an)*45; z_ += math.sin(an)*30; pl.append((x_, 0.6, z_))
    LAVA.append(pl)
def crater(x, r, z=None):
    CRATERS.append((x, random.uniform(-10, 10) if z is None else z, r, [(random.uniform(0, 2*math.pi), random.uniform(1.3, 2.4)) for _ in range(7)]))
def debris(x, h, z, n, push=0.0, up=1.0, fl=0.0):
    for _ in range(n):
        DEBRIS.append([x + random.uniform(-10, 10), h + random.uniform(0, 20), z + random.uniform(-10, 10),
                       push + random.uniform(-4, 4), random.uniform(2, 9)*up, random.uniform(-3, 3), random.uniform(3, 8), False, fl])
def break_pillars(x, rad, push=0.0):
    for p in PILLARS:
        if p["alive"] and abs(p["x"] - x) < rad:
            p["alive"] = False; zc = (p["z0"] + p["z1"])/2; nb = 55 if p["kind"] == "wall" else 22
            debris(p["x"], p["h"]*0.45, zc, nb, push, 1.2)
            sparks.extend([[p["x"], random.uniform(0, p["h"]), (p["z0"] + p["z1"])/2, push*0.5 + random.uniform(-4, 4), random.uniform(0, 6), random.uniform(-2, 2), 1.0, (150, 130, 110)] for _ in range(25)])

ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                       "-r", str(FPS), "-i", "-", "-ss", str(START), "-t", str(DUR), "-i", AUDIO, "-af", f"atempo={SLOW}",
                       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-c:a", "aac", "-shortest", OUT],
                      stdin=subprocess.PIPE)
bodies = [Body(P["tuck"]), Body(P["stance"])]
feet = [dict(anc=[None, None], stp=[None, None], last=[0.0, 0.0]) for _ in range(2)]
prevsk = [np.zeros((12, 2)), np.zeros((12, 2))]
hitflash = np.zeros(2); camT = np.array([-80.0, 750.0, 0.0]); zoom = 1.0; cur_shot = None
shake = flash = 0.0; sparks = []; rings = []; lines_t = -99; inv_t = -99; LASTV = None; trails = [[], []]
fired = set(); ta_prev = 0.0; L_prev = 1.0

def ik_target(ik, ta):
    kind, j, idx, off = ik["tgt"]
    if kind == "pt": return np.array(idx, float) + off
    p = prevsk[j][int(idx)] if not isinstance(idx, float) else prevsk[j][0] + (prevsk[j][1] - prevsk[j][0])*idx/0.6*0.6 + (prevsk[j][1]-prevsk[j][0])*0.0
    if kind == "fix":
        if ik["cap"] is None: ik["cap"] = p.copy()
        p = ik["cap"]
    return p + np.array(off)

def rig(i, st, ta, dta):
    X, F, rot, h = st["x"], st["F"], st["rot"], st["h"]
    c = math.cos(math.radians(st["spin"]))
    q = fk(bodies[i].a)
    qt = fk(rel_angles(st["pose"]))
    upright = abs(((rot + 180) % 360) - 180) < 1 and h < 0.5 and abs(c) > 0.3
    gp = st["plant"] if upright else NONE
    hip_y = None
    fs = feet[i]
    if gp:
        hh = max(qt[9][1] if "f" in gp else 0, qt[11][1] if "b" in gp else 0)
        tg = {}
        for li, (leg, kn, ft) in enumerate((("f", 8, 9), ("b", 10, 11))):
            if leg not in gp: fs["anc"][li] = None; fs["stp"][li] = None; continue
            want = X + F*c*qt[ft][0]
            if fs["anc"][li] is None:
                fs["anc"][li] = want if abs(fs["last"][li] - want) < 4 else fs["last"][li]
                if abs(fs["last"][li] - want) >= 4: fs["stp"][li] = [ta, fs["last"][li], want]
            stp = fs["stp"][li]
            if stp:
                p = min(1, (ta - stp[0])/0.11); fx_ = stp[1] + (stp[2] - stp[1])*p*p*(3-2*p); fy = 10*math.sin(math.pi*p)
                if p >= 1: fs["anc"][li] = stp[2]; fs["stp"][li] = None
            else:
                fx_, fy = fs["anc"][li], 0.0
                other = fs["stp"][1-li]
                if other is None and abs(fs["anc"][li] - want) > 16: fs["stp"][li] = [ta, fs["anc"][li], want]
            tg[li] = (fx_, fy)
        for li, (_, fy) in tg.items():
            dx = (tg[li][0] - X)*F/c
            hh = min(hh, math.sqrt(max(1, 59.5**2 - dx*dx)) + fy)
        for li, (fx_, fy) in tg.items():
            kn, ft = (8, 9) if li == 0 else (10, 11)
            knee, end = ik2(q[0], np.array([(fx_ - X)*F/c, hh - fy]), 30, 30, 1)
            q[kn], q[ft] = knee, end
        hip_y = hh
    else:
        for li, ft in ((0, 9), (1, 11)): fs["anc"][li] = None; fs["stp"][li] = None
    if abs(((rot + 180) % 360) - 180) < 1 and abs(c) > 0.5:   # le poing / le pied va réellement sur la cible
        if hip_y is None: hip_y = h + q[:, 1].max()
        for ik in IKS[i]:
            if not (ik["t0"] <= ta <= ik["t2"]): continue
            if ta < ik["t1"]: w = (ta - ik["t0"])/max(1e-3, ik["t1"] - ik["t0"]); w = w*w*(3-2*w)
            elif ta < ik["t1"] + 0.07: w = 1.0
            else: w = max(0, 1 - (ta - ik["t1"] - 0.07)/max(1e-3, ik["t2"] - ik["t1"] - 0.07)); w = w*w*(3-2*w)
            r0, mi, en, L1, L2, pref = LIMB[ik["limb"]]
            tw = ik_target(ik, ta)
            knee, end = ik2(q[r0], np.array([(tw[0] - X)*F/c, hip_y - tw[1]]), L1, L2, pref)
            q[mi] = q[mi] + (knee - q[mi])*w; q[en] = q[en] + (end - q[en])*w
    r = math.radians(rot); cr, sr = math.cos(r), math.sin(r)
    q = np.stack([(q[:, 0]*cr - q[:, 1]*sr)*c, q[:, 0]*sr + q[:, 1]*cr], 1)
    if hip_y is None: hip_y = h + q[:, 1].max()
    w = np.stack([X + F*q[:, 0], hip_y - q[:, 1]], 1)
    fs["last"] = [w[9][0], w[11][0]]
    return w

for f in range(int(DUR*FPS/SLOW)):
    t = f*SLOW/FPS
    ta = anim_time(t); dta = ta - ta_prev; ta_prev = ta; spd = float(np.clip(dta*FPS, 0, 3))
    day_i = int(max(0, t - SUNRISE0)//DAY)
    st = [T[0].state(ta), T[1].state(ta)]
    FZ = [st[0]["z"], st[1]["z"]]
    for i in range(2):
        if st[i]["name"] == "fly" and st[i]["h"] > 15: st[i]["h"] += 7*math.sin(ta*3.2 + i*2)   # flotte en vol
    if dta > 0:
        for i in range(2):
            tg = np.zeros(11)
            for dl in sorted(set(DELAY)):
                s2 = T[i].state(ta + LEAD - dl); ra = rel_angles(s2["pose"])
                tg[DELAY == dl] = ra[DELAY == dl]
            tg += 0.035*np.sin(ta*(1.3 + 0.37*np.arange(11)) + np.arange(11) + 2*i)   # jamais figé
            if st[i]["name"] == "dazed":   # sonné : vacille, la tête roule
                tg[0] += 0.22*math.sin(ta*4.5 + i); tg[1] += 0.2*math.sin(ta*6.1 + i); tg[2] += 0.3*math.sin(ta*7.3)
            if st[i]["name"] in ("stance", "stance2", "stance3", "block", "fly"):   # respiration + rebond sur le tempo, plus marqués avec la fatigue
                amp = 1 + 0.45*day_i; bob = (math.sin(2*math.pi*(ta - 4.08)/0.4587) + 1)/2
                tg[0] += 0.04*amp*math.sin(ta*3.1 + i); tg[1] += 0.06*amp*math.sin(ta*2.3 + i)
                tg[3] += 0.1*amp*math.sin(ta*4 + i); tg[5] += 0.1*amp*math.sin(ta*3.6 + i + 1)
            bodies[i].step(tg, dta)

    # impacts
    for k, e in enumerate(FX):
        if k in fired or ta < e["t"]: continue
        fired.add(k)
        if e["at"][0] == "pt": _, fxp, fh, fz = e["at"]
        else:
            j, idx = e["at"]
            pos = prevsk[j][idx] if isinstance(idx, int) else prevsk[j][0] + (prevsk[j][1] - prevsk[j][0])*idx
            fxp, fh, fz = pos[0], max(0, pos[1]), FZ[j]
        s, kind = e["s"], e["kind"]
        if kind not in ("dust", "whoosh"): shake = max(shake, s*9); flash = max(flash, min(1, s/3.2))
        n = int(8 + s*14) if kind != "whoosh" else 0
        for _ in range(n):
            grd = kind in ("land", "dust")
            an = random.uniform(0.1, math.pi - 0.1) if grd else random.uniform(0, 2*math.pi)
            v = random.uniform(3, 6 + s*4)
            col = (255, 225, 140) if kind in ("hit", "clash", "parry") else (190, 200, 255) if kind == "block" else (150, 120, 90)
            sparks.append([fxp, fh, fz, math.cos(an)*v*(1.6 if grd else 1), math.sin(an)*v, random.uniform(-1, 1)*v*0.8, 1.0, col])
        if kind == "whoosh":
            for _ in range(6):
                sparks.append([fxp, fh, fz, random.uniform(-9, 9), random.uniform(-2, 2), 0, 0.6, (200, 200, 220)])
        if kind in ("land", "clash", "hit") and s >= 1: rings.append([fxp, fh, 0.0, s, kind == "land"])
        if kind in ("clash", "boom", "hit", "block"): lines_t = f
        if kind in ("clash", "boom") or s >= 2.0: inv_t = f
        if kind == "boom":
            for _ in range(140):
                an = random.uniform(0, 2*math.pi); vv = random.uniform(6, 26)
                sparks.append([fxp, fh, fz, math.cos(an)*vv, math.sin(an)*vv, random.uniform(-1, 1)*vv*0.6, 1.0, random.choice([(255, 240, 200), (120, 200, 255), (255, 255, 255)])])
            for k_ in range(4): rings.append([fxp, fh, -k_*3, 6, k_ % 2 == 0])
            crater(fxp, 120, fz); debris(fxp, 0, 0, 60, 0, 2.0); break_pillars(fxp, 320)
        if kind == "land" and s >= 1.5: crater(fxp, 18 + 10*s, fz); debris(fxp, 0, 0, int(6*s)); break_pillars(fxp, 60)
        if kind == "hit" and s >= 2.0: break_pillars(fxp, 90)
        if kind == "mountain":   # cratère dans la paroi de la montagne
            MCRATERS.append((fxp, fh, fz + 2, 36, [(random.uniform(0, 2*math.pi), random.uniform(1.4, 2.6)) for _ in range(8)]))
            debris(fxp, fh, fz + 10, 40, 0, 1.0); shake = max(shake, 14)
        if kind == "breakout": debris(fxp, fh, fz + 10, 30, 0, 1.4)
        if kind == "rage":
            for _ in range(60):
                an = random.uniform(0.1, math.pi - 0.1); vv = random.uniform(3, 12)
                sparks.append([fxp + random.uniform(-25, 25), random.uniform(0, 30), fz, math.cos(an)*vv, math.sin(an)*vv, random.uniform(-2, 2), 1.0, (255, 60, 40)])
            crater(fxp, 45, fz); rings.append([fxp, 0, 0.0, 2.5, True]); debris(fxp, 0, fz, 14, 0, 0.0, ta + 0.5)
        if kind == "erupt":   # le sol explose : colonne de roches, onde de choc, flash qui change le décor
            for _ in range(160):
                an = random.uniform(0.2, math.pi - 0.2); vv = random.uniform(8, 30)
                sparks.append([fxp + random.uniform(-40, 40), random.uniform(0, 20), fz + random.uniform(-30, 30), math.cos(an)*vv*0.6, math.sin(an)*vv, random.uniform(-4, 4), 1.0, random.choice([(255, 150, 60), (255, 230, 180), (140, 110, 90)])])
            debris(fxp, 0, fz, 70, 0, 2.6); crater(fxp, 150, fz)
            for k_ in range(3): rings.append([fxp, 0, -k_*3, 6, True])
            break_pillars(fxp, 260); flash = 1.0; inv_t = f; lines_t = f
        if kind in ("ssj", "power"):
            for _ in range(120 if kind == "ssj" else 35):
                an = random.uniform(0.05, math.pi - 0.05); vv = random.uniform(4, 20 if kind == "ssj" else 10)
                sparks.append([fxp + random.uniform(-20, 20), random.uniform(0, 40), fz, math.cos(an)*vv, math.sin(an)*vv, random.uniform(-1, 1)*vv*0.5, 1.0, (255, 215, 80)])
            rings.append([fxp, 0, 0.0, 5 if kind == "ssj" else 2, True]); crater(fxp, 90 if kind == "ssj" else 25, fz)
            if kind == "ssj": rings.append([fxp, 80, -4, 6, False]); break_pillars(fxp, 300); lines_t = f; flash = 1.0
        v = e["victim"]
        if v is not None and kind in ("hit", "block"): LASTV = v
        if v is not None:
            b = bodies[v]; z = e["zone"]
            if kind == "land": b.v[[0, 1, 2]] += np.array([3, 6, 12])*s*0.5; b.v[3:7] += np.random.uniform(-12, 12, 4)*s
            elif z in ("head", "neck"):   # la tête part d'abord, le corps suit
                b.v[[0, 1, 2]] += np.array([-5, -12, -26])*s; b.v[3:7] += np.random.uniform(-18, 18, 4)*s; hitflash[v] = 1
            elif z in ("chest", "belly"):   # plié en deux
                b.v[[0, 1, 2]] += np.array([9, 12, 10])*s; b.v[3:7] += np.random.uniform(-8, 8, 4)*s; hitflash[v] = 1
            elif z == "legs":
                b.v[[7, 8, 9, 10]] += np.array([-12, 20, -12, 20])*s; hitflash[v] = 1
            elif z == "block":
                b.v[[3, 4, 5, 6]] += np.array([-10, 14, -10, 14])*s; b.v[1] -= 4*s
    hitflash *= 0.6

    sk = [rig(i, st[i], ta, dta) for i in range(2)]
    if dta > 0:
        for i in range(2):
            vx_ = (st[i]["x"] - T[i].state(ta - dta)["x"])/(dta*FPS)
            if abs(vx_) > 7 and st[i]["name"] not in ("dash", "run", "charge", "fire"):
                for p in PILLARS:
                    if p["alive"] and abs(p["x"] - st[i]["x"]) < p["w"]/2 + 14 and st[i]["h"] < p["h"] and abs(st[i]["z"]) < 60:
                        break_pillars(p["x"], 5, vx_*0.6); shake = max(shake, 13 if p["kind"] == "wall" else 9); flash = max(flash, 0.35)
            if st[i]["h"] < 2 and abs(vx_) > 4:
                MARKS.append((st[i]["x"] - vx_, st[i]["x"], (-6 if i == 0 else 6)))
                if len(MARKS) > 500: MARKS.pop(0)
    prevsk = [sk[0].copy(), sk[1].copy()]
    if dta > 0:
        for i in range(2):
            vxs = (st[i]["x"] - T[i].state(ta - dta)["x"])/(dta*FPS)
            if abs(vxs) > 14 and st[i]["name"] not in ("dash", "run"):
                for _ in range(3):
                    sparks.append([st[i]["x"] - vxs*random.uniform(0, 0.8), st[i]["h"] + random.uniform(20, 70), st[i]["z"] + random.uniform(-10, 10),
                                   -vxs*0.05, random.uniform(0.8, 1.6), 0, 0.75, (175, 165, 155)])
    xs_ = [st[0]["x"], st[1]["x"]]

    # poussière quand ça glisse
    for i in range(2):
        if st[i]["h"] < 2 and dta > 0:
            vx = (T[i].state(ta)["x"] - T[i].state(ta - dta)["x"])
            if abs(vx) > 5 and st[i]["plant"]:
                sparks.append([xs_[i], 0, random.uniform(-15, 15), -vx*0.3 + random.uniform(-2, 2), random.uniform(1, 4), random.uniform(-1, 1), 0.8, (140, 110, 80)])

    # ---------- caméra ----------
    sid, sh = shot_at(t)
    cut = sid != cur_shot; cur_shot = sid
    if cut: trails = [[], []]
    if sid == "orb":
        Tg = np.array([-80, st[0]["h"] - 40, 0.0]); zt = 1.25
    elif sh is not None and sh.get("follow") in ("A", "B"):
        j_ = 0 if sh["follow"] == "A" else 1
        Tg = np.array([xs_[j_], st[j_]["h"] + 45, st[j_]["z"]]); zt = zoom
    else:
        lim = xs_[0] + (60 if t < 2.6 else 700); xx2 = [xs_[0], min(xs_[1], lim) if xs_[1] > xs_[0] else max(xs_[1], xs_[0] - 700)]
        Tg = np.array([sum(xx2)/2, max(st[0]["h"], st[1]["h"])*0.55 + 60, (st[0]["z"] + st[1]["z"])/2])
        zt = float(np.clip(300/(abs(xx2[1] - xx2[0]) + 230), 0.38, 1.35))
        if abs(xs_[1] - xs_[0]) > 520 and LASTV is not None:
            Tg = np.array([xs_[LASTV], st[LASTV]["h"]*0.6 + 60, st[LASTV]["z"]]); zt = 0.62
    if cut and sh is not None: camT = Tg.copy()
    camT += (Tg - camT)*(0.35 if (sid == "orb" or sh is not None) else 0.25)
    zoom += (zt - zoom)*(1 if cut else 0.2)
    if sh is None: yaw, pitch, dist = 14 + 10*math.sin(t*0.17) + 0.8*math.sin(t*1.3), 8 + 0.5*math.sin(t*1.7), 700.0; fpx = 1.9*zoom*dist
    else:
        t0 = SHOT3[sid][0]; yaw = sh["yaw"] + sh["orbit"]*(t - t0); pitch, dist, fpx = sh["pitch"], sh["dist"] + sh.get("dolly", 0)*(t - t0), 520.0
    C, fw, rt, up = look(camT, yaw, pitch, dist)
    shake *= 0.82; flash *= 0.78
    ox, oy = random.uniform(-shake, shake), random.uniform(-shake, shake)
    CY = H*0.55
    def proj(p):
        v = np.asarray(p, float) - C; z = v @ fw
        if z < 4.9: return None
        return (W/2 + fpx*(v @ rt)/z + ox, CY - fpx*(v @ up)/z + oy, z)
    def seg(p, q):
        a, b = np.asarray(p, float), np.asarray(q, float); za, zb = (a - C) @ fw, (b - C) @ fw
        if za < 5 and zb < 5: return None
        if za < 5: a = a + (b - a)*(5 - za)/(zb - za)
        if zb < 5: b = b + (a - b)*(5 - zb)/(za - zb)
        return proj(a), proj(b)

    # ---------- ciel jour/nuit ----------
    ph, el, top, hor, L = sky_state(t)
    TH = THEMES[min(2, theme_at(ta))]
    if TH == "volcan": ph, el, top, hor, L = -math.pi/2, -0.4, (34, 8, 6), (255, 86, 28), 0.62
    elif TH == "glace": ph, el, top, hor, L = math.pi*0.42, 0.55, (70, 120, 190), (205, 228, 245), 1.0
    hd = np.array([fw[0], 0, fw[2]]); hd /= (np.linalg.norm(hd) + 1e-9)
    hy = CY - fpx*(hd @ up)/max(1e-3, hd @ fw) + oy
    rows = (np.arange(H) - hy)[:, None]
    k_ = np.clip(-rows/700, 0, 1); g_ = np.clip(rows/500, 0, 1)
    skyc = np.array(hor)[None, :]*(1 - k_) + np.array(top)[None, :]*k_
    gb = np.array([110, 84, 62])*L + np.array(hor)*0.12
    if TH == "volcan": gb = np.array([58, 40, 36]) + np.array(hor)*0.08
    elif TH == "glace": gb = np.array([196, 212, 228])
    grc = gb[None, :]*(1 - 0.55*g_)
    sky_img = np.repeat(np.where(rows < 0, skyc, grc)[:, None, :], W, 1)
    img = Image.fromarray(np.clip(sky_img, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    view_az = -math.radians(yaw)
    def sky_pt(az, elv):
        rel = az - view_az
        if abs(rel) > 1.3: return None
        return (W/2 + 300*math.tan(rel) + ox, hy - 300*math.tan(min(elv, 1.25))*0.62)
    night = float(np.clip(-el/0.3, 0, 1))
    if night > 0:
        for az, elv, tw in STARS:
            p = sky_pt(az, elv)
            if p and p[1] < hy:
                b = int(255*night*(0.5 + 0.5*math.sin(t*3 + tw)))
                d.point(p, fill=(b, b, b))
    skyg = Image.new("RGB", (W, H)); sgd = ImageDraw.Draw(skyg)
    for (bph, rad, kind) in ((ph, 26, "sun"), (ph + math.pi, 17, "moon")):
        sel = math.sin(bph); saz = -math.cos(bph)*1.05
        if sel < -0.1: continue
        p = sky_pt(saz, math.asin(max(-0.1, sel))*1.0)
        if not p: continue
        if kind == "sun":
            c1 = mix((255, 120, 50), (255, 245, 210), float(np.clip(sel/0.4, 0, 1)))
            sgd.ellipse([p[0]-rad*2.6, p[1]-rad*2.6, p[0]+rad*2.6, p[1]+rad*2.6], fill=tuple(int(v*0.55) for v in c1))
        else:
            c1 = (225, 230, 245); sgd.ellipse([p[0]-rad*2, p[1]-rad*2, p[0]+rad*2, p[1]+rad*2], fill=(40, 45, 60))
        d.ellipse([p[0]-rad, p[1]-rad, p[0]+rad, p[1]+rad], fill=tuple(int(v) for v in c1))
        if kind == "moon": d.ellipse([p[0]-rad+7, p[1]-rad-3, p[0]+rad+7, p[1]+rad-3], fill=tuple(int(v) for v in skyc[0]) if False else tuple(int(v) for v in mix(top, hor, 0.3)))
    # nuages en accéléré
    cm = Image.new("L", (W, H)); cd = ImageDraw.Draw(cm)
    for cl in CLOUDS:
        cl[0] += 0.55/FPS
        if cl[0] > 1.6: cl[0] -= 3.2
        p = sky_pt(cl[0], cl[1])
        if p and p[1] < hy:
            s_ = cl[2]
            for dx_, dy_, r_ in ((0, 0, 1), (-0.8, 0.2, 0.7), (0.8, 0.25, 0.75)):
                cd.ellipse([p[0] + dx_*s_ - r_*s_, p[1] + dy_*s_ - r_*s_*0.5, p[0] + dx_*s_ + r_*s_, p[1] + dy_*s_ + r_*s_*0.5], fill=150)
    cm = cm.filter(ImageFilter.GaussianBlur(14))
    img = Image.fromarray(np.clip(np.asarray(img, np.float32) + np.asarray(skyg.filter(ImageFilter.GaussianBlur(16)), np.float32), 0, 255).astype(np.uint8))
    ccol = mix(mix(hor, (255, 255, 255), 0.5), (40, 42, 60), night)
    img = Image.composite(Image.new("RGB", (W, H), tuple(int(v) for v in ccol)), img, cm)
    d = ImageDraw.Draw(img)

    glow = Image.new("RGB", (W, H)); gd = ImageDraw.Draw(glow)
    gcol = tuple(int(v*0.75) for v in gb)
    gx0 = int(camT[0]//90)*90; gz0 = int(camT[2]//90)*90
    def fogc(z_): w_ = float(np.clip((z_ - 300)/2200, 0, 1)); return tuple(int(gcol[k]*(1 - w_) + hor[k]*0.55*w_ + gb[k]*0.45*w_) for k in range(3))
    for gx in range(gx0 - 1440, gx0 + 1441, 90):
        for zz in range(gz0 - 1800, gz0 + 900, 300):
            s_ = seg((gx, 0, zz), (gx, 0, zz + 300))
            if s_: d.line([s_[0][:2], s_[1][:2]], fill=fogc((s_[0][2] + s_[1][2])/2), width=1)
    for gz in range(gz0 - 1800, gz0 + 901, 90):
        for xx_ in range(gx0 - 1440, gx0 + 1440, 360):
            s_ = seg((xx_, 0, gz), (xx_ + 360, 0, gz))
            if s_: d.line([s_[0][:2], s_[1][:2]], fill=fogc((s_[0][2] + s_[1][2])/2), width=1)
    if TH == "volcan":
        for pl in LAVA:
            q_ = [proj(p) for p in pl]
            if all(q_):
                gd.line([p[:2] for p in q_], fill=(255, 100, 25), width=5); d.line([p[:2] for p in q_], fill=(255, 190, 90), width=2)
    elif TH == "glace":
        for pl in LAVA:
            q_ = [proj(p) for p in pl]
            if all(q_): d.line([p[:2] for p in q_], fill=(150, 190, 225), width=2)
    rcol = tuple(int(v) for v in mix(hor, (8, 6, 12), 0.72))
    rs = []
    for rx, rz, rw, rh in ruins:
        pb = proj((rx, 0, rz))
        if pb and pb[2] > dist + 500 and -200 < pb[0] < W + 200: rs.append((pb, rw, rh))
    for pb, rw, rh in sorted(rs, key=lambda r: -r[0][2]):
        s2 = fpx/pb[2]; d.rectangle([pb[0] - rw*s2/2, pb[1] - rh*s2, pb[0] + rw*s2/2, pb[1]], fill=rcol)
    mbase = np.array([84, 76, 74])*L + np.array(hor)*0.18
    for M in sorted(MOUNTS, key=lambda M: -((np.array([M["xc"], 0, M["zc"]]) - C) @ fw)):
        dep = (np.array([M["xc"], 0, M["zc"]]) - C) @ fw
        if dep < 60: continue
        r = M["r"]; ap_ = np.array([M["xc"], M["h"], M["zc"]])
        bs = [np.array(v, float) for v in ((M["xc"] - r, 0, M["zc"] + r), (M["xc"] + r, 0, M["zc"] + r), (M["xc"] + r, 0, M["zc"] - r), (M["xc"] - r, 0, M["zc"] - r))]
        haze = 0.12 if M["near"] else min(0.7, dep/14000)
        col0 = np.array(mix(mbase, hor, haze))
        for k in range(4):
            b0, b1 = bs[k], bs[(k + 1) % 4]
            n_ = np.cross(b1 - b0, ap_ - b0)
            if n_ @ (C - (b0 + b1 + ap_)/3) <= 0: continue
            P_ = [proj(b0), proj(b1), proj(ap_)]
            if not all(P_): continue
            shd = 0.8 + 0.25*(n_[0]/np.linalg.norm(n_))*(-math.cos(ph))
            d.polygon([p[:2] for p in P_], fill=tuple(int(np.clip(v*shd, 0, 255)) for v in col0))
            S_ = [proj(b0 + (ap_ - b0)*0.74), proj(b1 + (ap_ - b1)*0.74), P_[2]]   # neige au sommet
            if all(S_): d.polygon([p[:2] for p in S_], fill=tuple(int(np.clip(v*shd, 0, 255)) for v in mix(col0, (255, 110, 30) if TH == "volcan" else (235, 238, 245), 0.55*L + 0.2 if TH != "volcan" else 0.8)))
    for mx, my, mz, mr, cracks in MCRATERS:   # trou laissé dans la paroi
        poly = [proj((mx + mr*math.cos(u), my + mr*0.8*math.sin(u), mz)) for u in np.linspace(0, 2*math.pi, 18)]
        if all(poly): d.polygon([p[:2] for p in poly], fill=tuple(int(v*0.35) for v in mbase))
        for an, ln in cracks:
            pts_ = [proj((mx + mr*k_*math.cos(an + 0.2*math.sin(k_*5)), my + mr*k_*math.sin(an + 0.2*math.sin(k_*5)), mz)) for k_ in np.linspace(0.9, ln, 5)]
            if all(pts_): d.line([p[:2] for p in pts_], fill=tuple(int(v*0.4) for v in mbase), width=2)

    if t < 1.7:
        pp = proj((-80, st[0]["h"] + 40, 0))
        if pp:
            px, py = pp[:2]
            for r_, c_ in ((60, (90, 140, 160)), (30, (200, 240, 255))): gd.ellipse([px-r_, py-r_, px+r_, py+r_], fill=c_)
            gd.line([px, py, px, py - 400], fill=(120, 200, 230), width=18); d.ellipse([px-14, py-14, px+14, py+14], fill=(255, 255, 255))

    # ---------- décor abîmé ----------
    dark = tuple(int(v*0.5) for v in gb); rim = tuple(int(min(255, v*1.15)) for v in gb)
    for cx_, cz_, r_, cracks in CRATERS:
        poly = [proj((cx_ + r_*math.cos(u), 0.5, cz_ + r_*0.7*math.sin(u))) for u in np.linspace(0, 2*math.pi, 24)]
        if all(poly):
            d.polygon([p[:2] for p in poly], fill=dark); d.line([p[:2] for p in poly] + [poly[0][:2]], fill=rim, width=2)
        for an, ln in cracks:
            pts_ = [proj((cx_ + r_*k_*math.cos(an + 0.15*math.sin(k_*7)), 0.5, cz_ + r_*k_*0.7*math.sin(an + 0.15*math.sin(k_*7)))) for k_ in np.linspace(0.9, ln, 5)]
            if all(pts_): d.line([p[:2] for p in pts_], fill=dark, width=2)
    for x0_, x1_, z_ in MARKS:
        q_ = seg((x0_, 0.3, z_), (x1_, 0.3, z_))
        if q_: d.line([q_[0][:2], q_[1][:2]], fill=dark, width=max(1, int(5*fpx/q_[0][2])))
    stone = np.array([120, 108, 96])*L + np.array(hor)*0.08
    def box(x0, x1, z0, z1, h_):
        cx_, cz_ = (x0 + x1)/2, (z0 + z1)/2
        faces = [((cx_, h_/2, z1), (0, 0, 1), [(x0, 0, z1), (x1, 0, z1), (x1, h_, z1), (x0, h_, z1)], 1.0),
                 ((cx_, h_/2, z0), (0, 0, -1), [(x1, 0, z0), (x0, 0, z0), (x0, h_, z0), (x1, h_, z0)], 0.6),
                 ((x1, h_/2, cz_), (1, 0, 0), [(x1, 0, z1), (x1, 0, z0), (x1, h_, z0), (x1, h_, z1)], 0.75),
                 ((x0, h_/2, cz_), (-1, 0, 0), [(x0, 0, z0), (x0, 0, z1), (x0, h_, z1), (x0, h_, z0)], 0.75),
                 ((cx_, h_, cz_), (0, 1, 0), [(x0, h_, z1), (x1, h_, z1), (x1, h_, z0), (x0, h_, z0)], 1.2)]
        for ctr, nrm, cs, sh_ in faces:
            if np.dot(nrm, C - np.array(ctr)) <= 0: continue
            pp_ = [proj(p) for p in cs]
            if all(pp_): d.polygon([p[:2] for p in pp_], fill=tuple(int(min(255, v*sh_)) for v in stone))
    for p in sorted(PILLARS, key=lambda p: -((np.array([p["x"], 50, (p["z0"] + p["z1"])/2]) - C) @ fw)):
        x0_, x1_ = p["x"] - p["w"]/2, p["x"] + p["w"]/2
        if p["kind"] == "wall" and sh is None: continue
        if p["alive"]: box(x0_, x1_, p["z0"], p["z1"], p["h"])
        elif p["kind"] == "wall":   # mur troué là où le corps est passé
            box(x0_, x1_, p["z0"], -26, p["h"]); box(x0_, x1_, 22, p["z1"], p["h"]*0.8); box(x0_, x1_, -26, 22, 26)
        else: box(x0_, x1_, p["z0"], p["z1"], p["h"]*0.28)
    for c_ in DEBRIS:
        if t < c_[8]:   # cailloux qui lévitent pendant la charge
            c_[1] += 1.1; c_[0] += math.sin(t*3 + c_[6])*0.6
        elif not c_[7]:
            c_[0] += c_[3]*spd; c_[1] += c_[4]*spd; c_[2] += c_[5]*spd; c_[4] -= 0.8*spd
            if c_[1] <= 0: c_[1] = 0; c_[4] *= -0.3; c_[3] *= 0.5; c_[5] *= 0.5
            if c_[1] == 0 and abs(c_[3]) < 0.3: c_[7] = True
        pc = proj((c_[0], c_[1] + c_[6]/2, c_[2]))
        if pc:
            r_ = c_[6]*fpx/pc[2]
            d.polygon([(pc[0], pc[1] - r_), (pc[0] + r_, pc[1]), (pc[0], pc[1] + r_*0.6), (pc[0] - r_, pc[1])], fill=tuple(int(v*0.85) for v in stone))
    if len(DEBRIS) > 900: DEBRIS[:] = DEBRIS[-900:]

    # ombres (direction selon le soleil)
    sel = math.sin(ph); sh_off = float(np.clip(math.cos(ph)/max(0.3, sel), -2.5, 2.5))*22 if sel > 0 else 0
    for i in range(2):
        if t < 1.7 and i == 0: continue
        rr = 38/(1 + st[i]["h"]/150)
        poly = [proj((xs_[i] + sh_off + rr*(1 + abs(sh_off)/60)*math.cos(an), 0, st[i]["z"] + rr*0.6*math.sin(an))) for an in np.linspace(0, 2*math.pi, 20)]
        if all(poly): d.polygon([p[:2] for p in poly], fill=tuple(int(v*0.35) for v in gb))

    gmul = 1.0 - 0.45*float(np.clip(el/0.4, 0, 1))
    order = sorted(range(2), key=lambda i: -(((np.array([xs_[i], 60, 0]) - C) @ fw)))
    for i in order:
        if t < 1.7 and i == 0: continue
        pz = st[i]["z"] + (-6 if i == 0 else 6)
        F = st[i]["F"]
        scr = [proj((sk[i][n][0], sk[i][n][1], pz + ZOFF[n]*F)) for n in range(12)]
        if any(p is None for p in scr): continue
        trails[i] = (trails[i] + [scr])[-5:]
        base = COL[i]; hc = tuple(int(c_ + (255 - c_)*hitflash[i]) for c_ in base)
        for j, tr in enumerate(trails[i][:-1]):
            a_ = (j + 1)/len(trails[i])*0.4*gmul
            for b0, b1 in BONES:
                gd.line([tr[b0][:2], tr[b1][:2]], fill=tuple(int(v*a_) for v in base), width=max(2, int(4.5*fpx/tr[b0][2])))
        for dr, mul, c_ in ((gd, 2, tuple(int(v*gmul) for v in hc)), (d, 1, tuple(min(255, v + 60) for v in hc))):
            for b0, b1 in BONES:
                w_ = max(2, int(4.5*mul*fpx/((scr[b0][2] + scr[b1][2])/2)))
                dr.line([scr[b0][:2], scr[b1][:2]], fill=c_, width=w_)
                for p in (scr[b0], scr[b1]):
                    r_ = w_/2; dr.ellipse([p[0]-r_, p[1]-r_, p[0]+r_, p[1]+r_], fill=c_)
            hx, hy2, hz = scr[3]; r_ = 11*fpx/hz
            dr.ellipse([hx-r_, hy2-r_, hx+r_, hy2+r_], fill=c_)

    for i in range(2):
        if st[i]["name"] == "dazed":
            hd_ = sk[i][3]
            for k_ in range(3):
                an = ta*6 + k_*2.09; ps = proj((hd_[0] + math.cos(an)*20, hd_[1] + 20, st[i]["z"] + math.sin(an)*20))
                if ps:
                    r_ = 6*fpx/ps[2]
                    for dr in (gd, d): dr.polygon([(ps[0], ps[1]-r_), (ps[0]+r_*0.3, ps[1]-r_*0.3), (ps[0]+r_, ps[1]), (ps[0]+r_*0.3, ps[1]+r_*0.3), (ps[0], ps[1]+r_), (ps[0]-r_*0.3, ps[1]+r_*0.3), (ps[0]-r_, ps[1]), (ps[0]-r_*0.3, ps[1]-r_*0.3)], fill=(255, 230, 90))
        if st[i]["name"] == "fly" and st[i]["h"] > 15:
            ap = proj((st[i]["x"], st[i]["h"] + 55, st[i]["z"]))
            if ap: ra = 70*fpx/ap[2]; gd.ellipse([ap[0]-ra*0.55, ap[1]-ra, ap[0]+ra*0.55, ap[1]+ra*0.9], outline=tuple(v//3 for v in COL[i]), width=3)
    if t >= T_SSJ - 1.3:
        on = t >= T_SSJ or random.random() < (t - (T_SSJ - 1.3))/1.3*0.5   # les cheveux scintillent avant la transformation
        hd_ = proj((sk[WIN][3][0], sk[WIN][3][1], st[WIN]["z"])); nk_ = proj((sk[WIN][2][0], sk[WIN][2][1], st[WIN]["z"]))
        if on and hd_ and nk_:
            ux, uy = hd_[0] - nk_[0], hd_[1] - nk_[1]; nn = math.hypot(ux, uy) + 1e-6; ux, uy = ux/nn, uy/nn
            r_ = 11*fpx/hd_[2]; sF = st[WIN]["F"]*(1 if (rt[0] >= 0) else -1)
            for k_, ang in enumerate((-80, -50, -22, 6, 34, 64)):
                a_ = math.radians(ang + sF*28)
                dx_, dy_ = ux*math.cos(a_) - uy*math.sin(a_), ux*math.sin(a_) + uy*math.cos(a_)
                L_ = r_*(1.5 + (0.6 if k_ in (2, 3) else 0.2) + 0.12*math.sin(t*35 + k_))
                px_, py_ = -dy_, dx_
                b0 = (hd_[0] + dx_*r_*0.6 + px_*r_*0.38, hd_[1] + dy_*r_*0.6 + py_*r_*0.38)
                b1 = (hd_[0] + dx_*r_*0.6 - px_*r_*0.38, hd_[1] + dy_*r_*0.6 - py_*r_*0.38)
                tip = (hd_[0] + dx_*(r_*0.6 + L_), hd_[1] + dy_*(r_*0.6 + L_))
                gd.polygon([b0, tip, b1], fill=(255, 180, 30)); d.polygon([b0, tip, b1], fill=(255, 226, 80))
        if t >= T_SSJ:   # aura dorée en flammes
            for k_ in range(9):
                off = random.uniform(-34, 34); hgt = random.uniform(120, 190)
                pts_ = [proj((st[WIN]["x"] + off*(1 - u)*1.0 + 6*math.sin(t*20 + k_ + u*6), u*hgt, st[WIN]["z"])) for u in np.linspace(0, 1, 6)]
                if all(pts_): gd.line([p[:2] for p in pts_], fill=(255, 190, 50), width=3)
            ap = proj((st[WIN]["x"], 85, st[WIN]["z"]))
            if ap: ra = 105*fpx/ap[2]; gd.ellipse([ap[0]-ra*0.55, ap[1]-ra, ap[0]+ra*0.55, ap[1]+ra*0.85], outline=(255, 200, 60), width=4)
    for r0_, r1_, ri in RAGE:
        if r0_ <= ta < r1_:
            hd_ = proj((sk[ri][3][0], sk[ri][3][1], st[ri]["z"]))
            if hd_:
                r_ = 11*fpx/hd_[2]; sF = st[ri]["F"]*(1 if rt[0] >= 0 else -1)
                ex_, ey_ = hd_[0] + sF*r_*0.45, hd_[1] - r_*0.1
                gd.ellipse([ex_ - r_*0.7, ey_ - r_*0.45, ex_ + r_*0.7, ey_ + r_*0.45], fill=(255, 30, 30))
                gd.line([ex_, ey_, ex_ - sF*r_*2.2, ey_ - r_*0.3], fill=(255, 40, 40), width=max(2, int(r_*0.3)))
                d.ellipse([ex_ - r_*0.22, ey_ - r_*0.16, ex_ + r_*0.22, ey_ + r_*0.16], fill=(255, 240, 240))
            for k_ in range(7):
                off = random.uniform(-30, 30); hgt = random.uniform(110, 170)
                pts_ = [proj((st[ri]["x"] + off*(1 - u) + 5*math.sin(t*22 + k_ + u*6), st[ri]["h"] + u*hgt, st[ri]["z"])) for u in np.linspace(0, 1, 6)]
                if all(pts_): gd.line([p[:2] for p in pts_], fill=(255, 50, 40), width=3)
    for pj in PROJ:   # boules d'énergie
        if pj["t0"] <= t < pj["t1"]:
            if pj["cap"] is None:
                hw_ = prevsk[pj["a"]][5]; pj["cap"] = (hw_[0], hw_[1], FZ[pj["a"]]); sv = T[pj["d"]].state(pj["t1"])
                pj["tg"] = (sv["x"] + random.choice([-1, 1])*random.uniform(50, 110), 0, random.uniform(-40, 40)) if pj["miss"] else (sv["x"], sv["h"] + 75, sv["z"])
            u_ = (t - pj["t0"])/(pj["t1"] - pj["t0"])
            pp_ = proj([pj["cap"][k] + (pj["tg"][k] - pj["cap"][k])*u_ for k in range(3)])
            if pp_:
                r_ = 9*fpx/pp_[2]; gd.ellipse([pp_[0]-r_*2.3, pp_[1]-r_*2.3, pp_[0]+r_*2.3, pp_[1]+r_*2.3], fill=COL[pj["a"]])
                d.ellipse([pp_[0]-r_, pp_[1]-r_, pp_[0]+r_, pp_[1]+r_], fill=(255, 255, 255))
        elif t >= pj["t1"] and not pj["done"] and pj["cap"] is not None:
            pj["done"] = True; ex, ey, ez = pj["tg"]
            for _ in range(30):
                an = random.uniform(0, 2*math.pi); vv = random.uniform(3, 12)
                sparks.append([ex, ey, ez, math.cos(an)*vv, abs(math.sin(an))*vv, random.uniform(-3, 3), 1.0, COL[pj["a"]]])
            rings.append([ex, ey, 0.0, 1.5, ey < 5]); shake = max(shake, 5); flash = max(flash, 0.2)
            if ey < 5: crater(ex, 26, ez); debris(ex, 0, ez, 10); break_pillars(ex, 40)
            else: hitflash[pj["d"]] = 0.7
    if DK0 <= t < TF + 1.0 and random.random() < 0.12:   # orage pendant la montée en puissance
        tgp = proj((st[WIN]["x"] + random.uniform(-260, 260), 0, random.uniform(-250, 40)))
        if tgp:
            x_ = random.uniform(0, W); pts_ = [(x_, 0)]
            for k_ in range(1, 11):
                u_ = k_/10; pts_.append((x_ + (tgp[0] - x_)*u_ + (random.uniform(-28, 28) if k_ < 10 else 0), tgp[1]*u_))
            gd.line(pts_, fill=(190, 200, 255), width=5); d.line(pts_, fill=(255, 255, 255), width=2); flash = max(flash, 0.25)
    for s in sparks:
        s[0] += s[3]*spd; s[1] += s[4]*spd; s[2] += s[5]*spd; s[4] -= 0.7*spd; s[6] -= 0.045*spd
        if s[1] < 0: s[1] = 0; s[4] *= -0.3; s[3] *= 0.7
        if s[6] > 0:
            q = seg((s[0], s[1], s[2]), (s[0] - s[3]*1.5, s[1] - s[4]*1.5, s[2] - s[5]*1.5))
            if q:
                c_ = tuple(int(v*s[6]) for v in s[7])
                gd.line([q[0][:2], q[1][:2]], fill=c_, width=5); d.line([q[0][:2], q[1][:2]], fill=c_, width=2)
    sparks = [s for s in sparks if s[6] > 0]
    for r in rings:
        r[2] += spd; a_ = max(0, 1 - r[2]/14); rad = r[2]*(14 + r[3]*6)
        if r[2] < 1: continue
        col = tuple(int(255*a_) for _ in range(3)); wd = max(1, int(6*a_))
        if r[4]:
            poly = [proj((r[0] + rad*math.cos(u), 1, rad*math.sin(u))) for u in np.linspace(0, 2*math.pi, 28)]
            if all(poly): gd.line([p[:2] for p in poly], fill=col, width=wd)
        else:
            pc = proj((r[0], r[1], 0))
            if pc: rp = rad*fpx/pc[2]; gd.ellipse([pc[0]-rp, pc[1]-rp, pc[0]+rp, pc[1]+rp], outline=col, width=wd)
    rings = [r for r in rings if r[2] < 14]
    if f - lines_t < 8:
        a_ = 1 - (f - lines_t)/8
        for _ in range(40):
            an = random.uniform(0, 2*math.pi); r0 = random.uniform(180, 300)
            gd.line([W/2 + math.cos(an)*r0, H/2 + math.sin(an)*r0, W/2 + math.cos(an)*900, H/2 + math.sin(an)*900],
                    fill=tuple(int(200*a_) for _ in range(3)), width=2)
    if BEAM["tc"] <= t < BEAM["t1"]:
        wi, vi = BEAM["who"], BEAM["vic"]; Fw_ = st[wi]["F"]
        hw = (sk[wi][5] + sk[wi][7])/2; hp_ = proj((hw[0], hw[1], 0))
        if t < BEAM["t0"]:   # charge : l'énergie converge, le sol craque, les pierres lévitent
            p_ = (t - BEAM["tc"])/(BEAM["t0"] - BEAM["tc"]); rb = 4 + 26*p_**1.5
            shake = max(shake, 1 + 5*p_)
            if hp_:
                for _ in range(int(8 + 20*p_)):
                    an = random.uniform(0, 2*math.pi); r1 = random.uniform(60, 200); r2 = r1*random.uniform(0.25, 0.6)
                    gd.line([hp_[0] + math.cos(an)*r1, hp_[1] + math.sin(an)*r1, hp_[0] + math.cos(an)*r2, hp_[1] + math.sin(an)*r2], fill=(90, 170, 255), width=2)
                for _ in range(1 + int(3*p_)):
                    pts_ = [hp_[:2]]; an = random.uniform(0, 2*math.pi)
                    for k_ in range(6): pts_.append((pts_[-1][0] + math.cos(an)*16 + random.uniform(-12, 12), pts_[-1][1] + math.sin(an)*16 + random.uniform(-12, 12)))
                    gd.line(pts_, fill=(200, 230, 255), width=2)
                R_ = rb*fpx/hp_[2]
                gd.ellipse([hp_[0]-R_*2.3, hp_[1]-R_*2.3, hp_[0]+R_*2.3, hp_[1]+R_*2.3], fill=(40, 120, 255))
                d.ellipse([hp_[0]-R_, hp_[1]-R_, hp_[0]+R_, hp_[1]+R_], fill=(220, 245, 255))
                ap = proj((st[wi]["x"], 60, 0))   # aura
                if ap:
                    ra = (70 + 30*p_)*fpx/ap[2]; gd.ellipse([ap[0]-ra*0.6, ap[1]-ra, ap[0]+ra*0.6, ap[1]+ra*0.9], outline=(60, 140, 255), width=max(2, int(6*p_)))
            if random.random() < 0.3 + 0.5*p_: debris(hw[0] + random.uniform(-160, 160), 0, random.uniform(-60, 40), 1, 0, 0.0, BEAM["t0"])
            for _ in range(3):   # vent de poussière aspiré vers lui
                xx_ = st[wi]["x"] + random.choice([-1, 1])*random.uniform(150, 300)
                sparks.append([xx_, random.uniform(0, 30), random.uniform(-40, 40), (st[wi]["x"] - xx_)*0.06, 0.8, 0, 0.7, (150, 125, 95)])
            if abs(t - BEAM["tc"]) < 0.5/FPS: crater(st[wi]["x"], 50)
            if abs(t - (BEAM["tc"] + 1.6)) < 0.5/FPS: crater(st[wi]["x"], 85)
        else:                 # tir : lutte puis percée
            el_ = t - BEAM["t0"]; xv = st[vi]["x"] - Fw_*12
            Lmax = abs(xv - hw[0]) if t < BEAM["tb"] else 2600
            Lb = min(Lmax, el_/0.12*abs(xv - hw[0]))
            fade = 1 if t < BEAM["t1"] - 0.4 else max(0, (BEAM["t1"] - t)/0.4)
            rb = ((20 + 5*math.sin(t*70)) if t < BEAM["tb"] else 34 + 6*math.sin(t*50))*fade
            for k_ in range(14):
                x0_ = hw[0] + Fw_*Lb*k_/14; x1_ = hw[0] + Fw_*Lb*(k_ + 1)/14
                q_ = seg((x0_, hw[1], 0), (x1_, hw[1], 0))
                if q_:
                    wz = fpx/((q_[0][2] + q_[1][2])/2)
                    gd.line([q_[0][:2], q_[1][:2]], fill=(50, 140, 255), width=max(2, int(rb*2.6*wz)))
                    d.line([q_[0][:2], q_[1][:2]], fill=(225, 248, 255), width=max(1, int(rb*1.1*wz)))
            if hp_:
                R_ = rb*1.5*fpx/hp_[2]; d.ellipse([hp_[0]-R_, hp_[1]-R_, hp_[0]+R_, hp_[1]+R_], fill=(235, 250, 255))
            if BEAM["tk"] <= t < BEAM["tb"]:   # point de contact : étincelles, il glisse en arrière
                cp = (hw[0] + Fw_*Lb, hw[1])
                for _ in range(10):
                    an = random.uniform(0, 2*math.pi); vv = random.uniform(4, 14)
                    sparks.append([cp[0], cp[1], 0, math.cos(an)*vv - Fw_*4, math.sin(an)*vv, random.uniform(-4, 4), 0.7, (180, 220, 255)])
                pc_ = proj((cp[0], cp[1], 0))
                if pc_: R_ = (30 + 8*math.sin(t*40))*fpx/pc_[2]; gd.ellipse([pc_[0]-R_, pc_[1]-R_, pc_[0]+R_, pc_[1]+R_], fill=(120, 190, 255))
                shake = max(shake, 5)
            else: shake = max(shake, 7*fade)
            if t >= BEAM["tb"] and t - BEAM["tb"] < 0.6:
                MARKS.append((hw[0] + Fw_*40, hw[0] + Fw_*min(Lb, 1800), 0)); break_pillars(hw[0] + Fw_*Lb*0.5, Lb*0.5)
    for p3 in DUST3:   # particules en 3D : les plus proches sont grosses et floues
        wx_ = camT[0] + ((p3[0] - camT[0] + 700) % 1400) - 700; wz_ = camT[2] + ((p3[2] - camT[2] + 700) % 1400) - 700
        p3[0] += p3[3]*spd; p3[1] = 10 + (p3[1] - 10 + 0.3*spd) % 260
        pp_ = proj((wx_, p3[1], wz_))
        if pp_:
            r_ = max(0.6, 2.2*fpx/pp_[2]); c_ = tuple(int(v*min(1, 180/pp_[2] + 0.25)) for v in (70, 62, 52))
            (gd if r_ > 3 else d).ellipse([pp_[0]-r_, pp_[1]-r_, pp_[0]+r_, pp_[1]+r_], fill=c_ if r_ > 3 else tuple(min(255, v + 90) for v in c_))
    for s in ash:
        if TH == "volcan":   # braises qui montent
            s[0] = (s[0] + 0.6*math.sin(t*2 + s[2]*9)) % W; s[1] = (s[1] - 1.8*s[2]) % H
            gd.ellipse([s[0]-2, s[1]-2, s[0]+2, s[1]+2], fill=(255, 120, 40)); d.point((s[0], s[1]), fill=(255, 200, 120))
        elif TH == "glace":  # neige
            s[0] = (s[0] - 0.8*s[2] + 0.5*math.sin(t + s[2]*5)) % W; s[1] = (s[1] + 2.2*s[2]) % H
            d.ellipse([s[0]-1.5, s[1]-1.5, s[0]+1.5, s[1]+1.5], fill=(250, 252, 255))
        else:
            s[0] = (s[0] - 1.5*s[2]) % W; s[1] = (s[1] + 0.6*s[2]) % H
            d.point((s[0], s[1]), fill=tuple(int(v) for v in mix((170, 150, 130), (90, 90, 110), night)))

    # « JOUR N » à chaque lever du soleil
    for k in (range(3) if not THEME_T or ta < THEME_T[0] else []):
        tt = t - (SUNRISE0 + k*DAY)
        if 0.1 < tt < 1.7:
            al = min(1, (tt - 0.1)/0.3, (1.7 - tt)/0.4)
            d.text((W/2, 130), f"JOUR {k+1}", font=FONT, anchor="mm", fill=tuple(int(v*al + mix(top, hor, 0.2)[n]*(1-al)) for n, v in enumerate((255, 240, 210))))

    dk = 0.55*float(np.clip((t - DK0)/(BEAM["t0"] - 0.1 - DK0), 0, 1)) if t < BEAM["tb"] else 0.55*max(0.35, 1 - (t - BEAM["tb"])/1.2)
    if t < DK0: dk = 0.0
    arr = np.asarray(img, np.float32)*(1 - dk) + np.asarray(glow.filter(ImageFilter.GaussianBlur(10)), np.float32)*0.9 \
          + np.asarray(glow, np.float32)*0.25
    arr = arr*vign + flash*150
    if f - inv_t == 0: arr = 255 - np.clip(arr, 0, 255)
    if sh is not None: arr[:70] = 0; arr[-70:] = 0
    ff.stdin.write(np.clip(arr, 0, 255).astype(np.uint8).tobytes())

ff.stdin.close(); ff.wait()
print("groupes", len(groups), "ralentis", [round(r[0], 1) for r in RAMPS], "rage/décor", [round(x, 1) for x in THEME_T])
