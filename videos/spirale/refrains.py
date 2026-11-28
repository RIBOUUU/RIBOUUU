"""Boucle « seuls les objets font la musique » sur la VRAIE melodie des 3 morceaux.

Pour chaque morceau : on cherche le passage de ~10 s ou la melodie est la plus nette et la plus variee
(refrain), on transcrit ses notes (pyin : debut + hauteur de chaque note), et chaque note devient un rebond
sur un objet, qui joue cette note. Les ecarts entre objets suivent donc le vrai rythme de la melodie
(la bille garde une vitesse constante). Entre deux morceaux : un puits a pieces (tunnel) qui joue un arpege.

Usage : python3 refrains.py <fearless.mp3> <android.mp3> <trigger.mp3>  -> timeline_refrains.json + audio_refrains.wav
"""
import sys, json, wave
import numpy as np, librosa

FILES = sys.argv[1:4]
SR, FPS, L, TUN = 48000, 30, 10.0, 2.4          # duree d'un passage, duree d'un tunnel
HOP, SR0 = 256, 22050

def analyse(path):
    y, sr = librosa.load(path, sr=SR0, mono=True)
    yh = librosa.effects.harmonic(y)
    f0, vo, _ = librosa.pyin(yh, fmin=180, fmax=1400, sr=sr, frame_length=2048, hop_length=HOP)
    tt = librosa.times_like(f0, sr=sr, hop_length=HOP)
    on = librosa.onset.onset_detect(y=yh, sr=sr, hop_length=HOP, units="time", backtrack=True)
    return y, f0, vo, tt, on

def notes_of(f0, vo, tt, on, a, b):
    """segmente la melodie en notes : un changement de hauteur ou une attaque = nouvelle note"""
    m = (tt >= a) & (tt < b); idx = np.where(m)[0]; notes = []; cur = None
    ons = set(np.round(on[(on >= a) & (on < b)] / (HOP / SR0)).astype(int))
    for i in idx:
        if not vo[i] or np.isnan(f0[i]):
            if cur and tt[i] - cur["t1"] > 0.06: notes.append(cur); cur = None
            continue
        p = librosa.hz_to_midi(f0[i])
        attack = any(abs(i - o) <= 1 for o in ons)
        if cur is None or abs(p - cur["p"]) > 0.7 or (attack and tt[i] - cur["t0"] > 0.1):
            if cur: notes.append(cur)
            cur = dict(t0=tt[i], t1=tt[i], p=p, ps=[p])
        else:
            cur["t1"] = tt[i]; cur["ps"].append(p); cur["p"] = float(np.median(cur["ps"]))
    if cur: notes.append(cur)
    out = []
    for n_ in notes:                                # on garde les vraies notes (>= 70 ms), hauteur arrondie
        if n_["t1"] - n_["t0"] < 0.07: continue
        midi = int(round(n_["p"]))
        if out and n_["t0"] - out[-1][0] < 0.16:     # trop serre pour deux objets : on garde la premiere
            continue
        out.append((float(n_["t0"]), midi))
    return out

songs = []
for path in FILES:
    y, f0, vo, tt, on = analyse(path)
    dur = len(y) / SR0; best = None
    for a in np.arange(8, dur - L - 8, 1.0):        # cherche le passage le plus melodique
        ns = notes_of(f0, vo, tt, on, a, a + L)
        if len(ns) < 12: continue
        pitches = [p for _, p in ns]; distinct = len(set(pitches)); steps = np.mean(np.abs(np.diff(pitches)) > 0)
        gaps = np.diff([t for t, _ in ns] + [a + L]); regular = np.mean((gaps > 0.15) & (gaps < 1.2))
        m = (tt >= a) & (tt < a + L); voiced = vo[m].mean()
        score = voiced * min(1, distinct / 8) * steps * regular * min(1, len(ns) / 25)
        rng_ = np.percentile(pitches, 90) - np.percentile(pitches, 10); score *= 1.0 if rng_ <= 14 else 0.25   # pas de sauts d'octave bizarres
        if best is None or score > best[0]: best = (score, a, ns)
    score, a, ns = best
    a0 = ns[0][0] - 0.02                            # le passage commence sur la premiere note
    ns = notes_of(f0, vo, tt, on, a0, a0 + L)
    print(f"{path.split('/')[-1][9:40]:32s} passage {a0:6.2f}-{a0 + L:6.2f}s  {len(ns)} notes  score {score:.3f}  "
          f"notes : {[p for _, p in ns[:16]]}")
    # erreurs d'octave : chaque note est ramenee a moins d'une demi-octave de la mediane glissante, puis +12 (son « boite a musique »)
    ps = [p for _, p in ns]; fixed = []
    for i, p in enumerate(ps):
        ref = np.median(ps)
        while p - ref > 6: p -= 12
        while ref - p > 6: p += 12
        fixed.append(p + 12)
    ns = [(t, p) for (t, _), p in zip(ns, fixed)]
    print("   corrige :", [p for _, p in ns[:16]])
    songs.append(dict(f=path, a0=a0, notes=[(t - a0, p) for t, p in ns]))

# ---------- calendrier de la periode (passage, tunnel, passage, tunnel, passage, tunnel) ----------
raw = 3 * (L + TUN); NV = int(round(raw * FPS / 16)) * 16; PER = NV / FPS; k = PER / raw
hits, tunnels, t = [], [], 0.0
for s, S in enumerate(songs):
    ts = [t + x * k for x, _ in S["notes"]]; end = t + L * k
    for i, (x, p) in enumerate(S["notes"]):
        t1 = ts[i + 1] if i + 1 < len(ts) else end
        hits.append(dict(t=round(ts[i], 5), dur=round(t1 - ts[i], 5), sec=s, i=i, note=int(p), chord=""))
    tunnels.append(dict(rim=round(end, 5), drop=round(end + TUN * k * 0.75, 5), exit=round(end + TUN * k, 5)))
    t = end + TUN * k
# types d'objets : chaque passage = 2 series (moitie / moitie), comme avant
TY = [("ressort", "vrille"), ("verre", "bumper"), ("aimant", "ventilo")]
plan = {}
for s, S in enumerate(songs):
    nh = len(S["notes"]); mid = nh // 2
    plan[s] = [[1, mid - 1, TY[s][0]], [mid, nh - 2, TY[s][1]]]
OFF = round(0.5 * FPS) / FPS
json.dump(dict(loop=True, period=PER, offset=OFF, hits=hits, tunnels=tunnels, end=PER, plan=plan,
               sources=[S["f"].split("/")[-1] for S in songs], passages=[S["a0"] for S in songs]),
          open("timeline_refrains.json", "w"), indent=1)

# ---------- son : chaque objet joue sa note (timbre selon l'objet), rien d'autre ----------
n = int(round(PER * SR)); bus = np.zeros((n, 2)); rng = np.random.default_rng(1)
def marimba(f, d=1.2):
    t = np.arange(int(d * SR)) / SR
    return (np.sin(2*np.pi*f*t)*np.exp(-t/0.45) + 0.25*np.sin(2*np.pi*3.93*f*t)*np.exp(-t/0.08) + 0.12*np.sin(2*np.pi*9.9*f*t)*np.exp(-t/0.02)) * np.minimum(1, t/0.002)
def cloche(f, d=1.8):
    t = np.arange(int(d * SR)) / SR
    return (np.sin(2*np.pi*f*t)*np.exp(-t/0.9) + 0.4*np.sin(2*np.pi*2.76*f*t)*np.exp(-t/0.3) + 0.2*np.sin(2*np.pi*5.4*f*t)*np.exp(-t/0.1)) * np.minimum(1, t/0.002)
def porcelaine(f, d=1.3):
    t = np.arange(int(d * SR)) / SR
    return (np.sin(2*np.pi*f*t)*np.exp(-t/0.5) + 0.5*np.sin(2*np.pi*f*2.71*t)*np.exp(-t/0.2) + 0.25*np.sin(2*np.pi*f*5.2*t)*np.exp(-t/0.06)
            + rng.normal(0, 1, len(t))*np.exp(-t/0.012)*0.2) * np.minimum(1, t/0.001)
def pluck(f, d=1.0):
    t = np.arange(int(d * SR)) / SR; s = sum(np.sin(2*np.pi*q*f*t)/q*np.exp(-t*(2.5+2.5*q)) for q in range(1, 10))
    return s * np.minimum(1, t/0.003)
def tom(f, d=0.8):
    t = np.arange(int(d * SR)) / SR
    return np.sin(2*np.pi*f*t)*np.exp(-t/0.3) + 0.5*np.sin(2*np.pi*f/2*t*(1+0.2*np.exp(-t/0.03)))*np.exp(-t/0.2) + rng.normal(0, 1, len(t))*np.exp(-t/0.008)*0.2
def flute(f, d=0.9):
    t = np.arange(int(d * SR)) / SR; e = np.minimum(1, t/0.025)*np.exp(-t/0.4)
    return (np.sin(2*np.pi*f*t) + 0.2*np.sin(4*np.pi*f*t) + rng.normal(0, 1, len(t))*0.04) * e
INSTR = {"normal": marimba, "ressort": pluck, "vrille": cloche, "verre": porcelaine, "bumper": tom, "aimant": cloche, "ventilo": flute}
def type_of(h):
    for d_, f_, ty in plan[h["sec"]]:
        if d_ <= h["i"] <= f_: return ty
    return "normal"
def put(x, t0, g, pan=0.5):
    a = int(round(t0 * SR)); idx = (np.arange(len(x)) + a) % n
    np.add.at(bus[:, 0], idx, x * g * np.sqrt(1 - pan)); np.add.at(bus[:, 1], idx, x * g * np.sqrt(pan))
for h in hits:
    f = 440 * 2 ** ((h["note"] - 69) / 12); x = INSTR[type_of(h)](f); put(x / (np.abs(x).max() + 1e-9), h["t"], 1.0, 0.5 + 0.25 * np.sin(h["i"] * 1.3))
for q, T_ in enumerate(tunnels):                    # le puits a pieces : arpege qui monte vers la 1re note du passage suivant
    nxt = hits[[h["sec"] for h in hits].index((q + 1) % 3)]["note"]; steps = [-12, -9, -7, -5, -3, 0]
    for j, st in enumerate(steps):
        tj = T_["rim"] + (T_["exit"] - T_["rim"]) * j / len(steps)
        x = cloche(440 * 2 ** ((nxt + st - 69) / 12), 1.0); put(x / np.abs(x).max(), tj, 0.35 + 0.1 * j)
ir = rng.normal(0, 1, int(1.0 * SR)) * np.exp(-np.arange(int(1.0 * SR)) / SR / 0.3); ir[:int(0.01 * SR)] = 0; ir /= np.sqrt((ir ** 2).sum())
for c in (0, 1):
    M = 1 << (2 * n).bit_length(); y_ = np.fft.irfft(np.fft.rfft(bus[:, c], M) * np.fft.rfft(ir, M), M)
    rv = y_[:n].copy(); rv[:n] += np.pad(y_[n:2 * n], (0, max(0, n - len(y_[n:2 * n]))))[:n]; bus[:, c] += 0.2 * rv
bus /= np.abs(bus).max() / 0.95
bus = np.roll(bus, -int(round(OFF * SR)), axis=0)
w = wave.open("audio_refrains.wav", "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((bus * 32767).astype(np.int16).tobytes()); w.close()
print(f"{len(hits)} rebonds, periode {PER:.2f}s ({NV} images), tunnels {[(round(x['rim'], 1), round(x['exit'], 1)) for x in tunnels]}")
