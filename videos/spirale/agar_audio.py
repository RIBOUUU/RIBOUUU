"""Musique ORIGINALE electro-house facon « musique de partie d'agar.io » (style NCS : plucks brillants,
supersaws, kick 4/4 qui pompe, montees et drops). 128 BPM, tout est cale sur la grille des temps.

  A  (intro, noires)            : pluck + nappe filtree + charleston
  -> tunnel 1 : montee (bruit + roulement + sirene), DROP a la sortie
  B  (croches pointees)         : kick 4/4, basse en contretemps, pads qui pompent, lead
  -> tunnel 2 : grosse montee, silence, DROP
  C  (croches, +2 demi-tons)    : supersaws, clap, kick, lead a l'octave, accord final

Usage : python3 agar_audio.py  -> timeline_agar.json + audio_agar.wav
"""
import json, wave
import numpy as np

SR = 48000
BPM = 128; BEAT = 60 / BPM
T0 = 0.06
rng = np.random.default_rng(8)
NAMES = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
NN = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
midi = lambda n: 12 * (int(n[-1]) + 1) + NAMES[n[:-1]]
nm = lambda m: NN[m % 12] + str(m // 12 - 1)
fr = lambda n: 440.0 * 2 ** ((midi(n) - 69) / 12)
tr = lambda n, k: nm(midi(n) + k)

CHORDS = {"Am": ("A1", ["A3", "C4", "E4"]), "F": ("F1", ["F3", "A3", "C4"]),
          "C": ("C2", ["G3", "C4", "E4"]), "G": ("G1", ["G3", "B3", "D4"])}
SECS = [   # unit en temps, tunnel F + D en temps
    dict(unit=1.0, last=1.0, F=3, D=1, tr=0,
         mel=["E5", "A5", "C6", "B5", "G5", "A5", "E5", "G5"],
         ch=["Am", "Am", "F", "F", "C", "C", "G", "G"]),
    dict(unit=0.75, last=0.75, F=3, D=1, tr=0,
         mel=["A5", "C6", "E6", "D6", "C6", "A5", "F5", "A5", "C6", "B5", "G5", "D6"],
         ch=["Am"] * 3 + ["F"] * 3 + ["C"] * 3 + ["G"] * 3),
    dict(unit=0.5, last=3.5, F=0, D=0, tr=2,
         mel=["A5", "C6", "E6", "A6", "G6", "E6", "F6", "E6", "C6", "D6", "E6", "G6", "B5", "A5"],
         ch=["Am"] * 4 + ["F"] * 4 + ["C"] * 3 + ["G"] * 2 + ["Am"]),
]

# ---------------- calendrier ----------------
hits, tunnels, t = [], [], T0
sec_start = []
for s, S in enumerate(SECS):
    sec_start.append(t); n = len(S["mel"])
    for i in range(n):
        d = (S["unit"] if i < n - 1 else S["last"]) * BEAT
        hits.append({"t": round(t, 5), "note": tr(S["mel"][i], S["tr"]), "dur": round(d, 5), "sec": s, "i": i, "chord": S["ch"][i]})
        t += d
    if S["F"]:
        F, D = S["F"] * BEAT, S["D"] * BEAT
        tunnels.append({"rim": round(t, 5), "drop": round(t + F, 5), "exit": round(t + F + D, 5)})
        t += F + D
END = round(hits[-1]["t"] + 1.6, 4)
json.dump({"hits": hits, "tunnels": tunnels, "end": END, "bpm": BPM}, open("timeline_agar.json", "w"), indent=1)

# ---------------- synthese ----------------
N = int((END + 3.0) * SR)
MAIN = np.zeros((N, 2)); SIDE = np.zeros((N, 2))      # SIDE = pistes qui « pompent » avec le kick
sin = lambda f, tt: np.sin(2 * np.pi * f * tt)

def put(sig, t0, gain=1.0, pan=0.5, bus=None):
    bus = MAIN if bus is None else bus
    a = int(round(t0 * SR))
    if a < 0: sig = sig[-a:]; a = 0
    k = min(len(sig), N - a)
    if k <= 0: return
    bus[a:a + k, 0] += sig[:k] * gain * np.sqrt(1 - pan); bus[a:a + k, 1] += sig[:k] * gain * np.sqrt(pan)

def saw(f, dur, cut, voices=(-0.012, -0.006, 0.0, 0.006, 0.012), att=0.005, rel=0.15, cut_env=None):
    """supersaw additive (sans repliement), coupure qui peut suivre une enveloppe cut_env(tt)"""
    n = int((dur + rel) * SR); tt = np.arange(n) / SR; s = np.zeros(n)
    c = cut if cut_env is None else cut * cut_env(tt)
    for d in voices:
        fd = f * (1 + d); ph = rng.uniform(0, 6.28)
        for k in range(1, 80):
            fk = k * fd
            if fk > 15000: break
            s += np.sin(2 * np.pi * fk * tt + k * ph) / k / (1 + (fk / c) ** 2)
    e = np.minimum(1, tt / att) * np.clip((dur + rel - tt) / rel, 0, 1)
    return s / len(voices) * e

def pluck(f, dur=0.45):
    return saw(f, min(dur, 0.45), 1, cut_env=lambda tt: 300 + 6000 * np.exp(-tt / 0.07), rel=0.12) * 1.4

def kick():
    tt = np.arange(int(0.45 * SR)) / SR
    f = 48 + 150 * np.exp(-tt / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.18) + rng.normal(0, 1, len(tt)) * np.exp(-tt / 0.002) * 0.25

def clap():
    tt = np.arange(int(0.3 * SR)) / SR; nz = np.diff(rng.normal(0, 1, len(tt) + 1))
    e = sum(np.exp(-np.maximum(tt - d, 0) / 0.008) * (tt >= d) for d in (0, 0.011, 0.022)) + np.exp(-tt / 0.09) * 0.6
    return nz * e * 0.35

def hat(open_=False):
    tt = np.arange(int((0.25 if open_ else 0.06) * SR)) / SR
    return np.diff(np.diff(rng.normal(0, 1, len(tt) + 2))) * np.exp(-tt / (0.07 if open_ else 0.012)) * 0.1

def sub_bass(f, dur):
    tt = np.arange(int(dur * SR)) / SR
    return (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt)) * np.minimum(1, tt / 0.005) * np.clip((dur - tt) / 0.03, 0, 1)

def crash(dur=2.4):
    tt = np.arange(int(dur * SR)) / SR; nz = np.diff(rng.normal(0, 1, len(tt) + 1))
    return nz * np.exp(-tt / 0.8) * 0.45

def riser(dur, f0=300, f1=9000):
    """bruit filtre qui monte (STFT)"""
    n = int(dur * SR); x = rng.normal(0, 1, n + 2048); win = np.hanning(1024); hop = 256; out = np.zeros(n + 2048)
    fq = np.fft.rfftfreq(1024, 1 / SR); lf = np.log2(np.maximum(fq, 1))
    for a in range(0, n, hop):
        u = a / n; c = np.log2(f0 * (f1 / f0) ** u)
        out[a:a + 1024] += np.fft.irfft(np.fft.rfft(x[a:a + 1024] * win) * np.exp(-((lf - c) / 0.6) ** 2)) * win
    out = out[:n]; out /= np.abs(out).max() + 1e-9
    return out * np.linspace(0.1, 1, n) ** 1.5

def boom():
    tt = np.arange(int(1.8 * SR)) / SR
    return np.sin(2 * np.pi * np.cumsum(32 + 70 * np.exp(-tt / 0.2)) / SR) * np.exp(-tt / 0.7)

# ---- notes de la bille : pluck brillant (+ octave au drop final)
for h in hits:
    s, i, t0 = h["sec"], h["i"], h["t"]; f = fr(h["note"]); pan = 0.5 + 0.25 * np.sin(i * 1.7)
    put(pluck(f, h["dur"]), t0, 0.32 if s == 0 else 0.36, pan)
    if s >= 1: put(pluck(f / 2, h["dur"]), t0, 0.16, 1 - pan)
    if s == 2: put(saw(f, min(h["dur"], 0.45), 5000, rel=0.08), t0, 0.12, 0.5); put(pluck(f * 2, h["dur"]), t0, 0.1, pan)

# ---- accords (nappes / supersaws) et basse, par blocs d'accord
for s, S in enumerate(SECS):
    hs = [h for h in hits if h["sec"] == s]; k = 0
    while k < len(hs):
        j = k
        while j + 1 < len(hs) and hs[j + 1]["chord"] == hs[k]["chord"]: j += 1
        t0 = hs[k]["t"]; t1 = hs[j]["t"] + hs[j]["dur"]
        if s < len(tunnels) and j == len(hs) - 1: t1 = tunnels[s]["rim"]
        b, notes = CHORDS[hs[k]["chord"]]; b = fr(tr(b, S["tr"])); notes = [fr(tr(x, S["tr"])) for x in notes]
        dur = t1 - t0
        for q, f in enumerate(notes):
            put(saw(f, dur, (700, 2200, 4500)[s], att=0.05, rel=0.2), t0, (0.07, 0.09, 0.11)[s], 0.2 + 0.3 * q, SIDE)
        if s >= 1:          # basse en contretemps (sur la croche « et »)
            tq = t0 + BEAT / 2
            while tq < t1 - 0.05:
                put(sub_bass(b * 2, BEAT * 0.45), tq, 0.45, 0.5, SIDE); tq += BEAT
        else:
            put(sub_bass(b * 2, dur), t0, 0.18, 0.5, SIDE)
        k = j + 1

# ---- batterie sur la grille des temps
kicks = []
for s, S in enumerate(SECS):
    t0 = sec_start[s]; t1 = tunnels[s]["rim"] if s < len(tunnels) else hits[-1]["t"]
    nb = int(round((t1 - t0) / BEAT))
    for b in range(nb):
        tb = t0 + b * BEAT
        put(hat(), tb + BEAT / 2, 0.9 if s else 0.6, 0.65)
        if s >= 1:
            put(kick(), tb, 0.9); kicks.append(tb)
            if b % 2 == 1: put(clap(), tb, 0.5 if s == 1 else 0.65, 0.45)
            put(hat(), tb, 0.5, 0.35)
            if s == 2: put(hat(True), tb + BEAT / 2, 0.5, 0.6)
        elif b % 2 == 0: put(kick() * 0.6, tb, 0.5); kicks.append(tb)
tf = hits[-1]["t"]; kicks.append(tf)

# ---- tunnels : montee + roulement qui accelere + sirene, silence d'un demi-temps, puis DROP
for k, T in enumerate(tunnels):
    tot = T["exit"] - T["rim"]; up = tot - BEAT / 2
    put(riser(up), T["rim"], 0.35 + 0.15 * k)
    n = int(up * SR); tt = np.arange(n) / SR; u = tt / up
    put(np.sin(2 * np.pi * np.cumsum(300 * 6 ** (u ** 1.4)) / SR) * u ** 1.5, T["rim"], 0.12)
    tq = 0.0; step = BEAT / 2
    while tq < up - 1e-3:
        x = tq / up; put(clap() * 0.8, T["rim"] + tq, 0.2 + 0.6 * x, 0.5)
        tq += step
        if tq > up * 0.5: step = BEAT / 4
        if tq > up * 0.8: step = BEAT / 8
    put(boom(), T["exit"], 0.9); put(kick(), T["exit"], 1.0); put(crash(), T["exit"], 0.55)

# accord final
for x in ["B3", "D4", "F#4", "B4"]: put(saw(fr(x), 1.4, 5000, att=0.01, rel=0.6), tf, 0.1, 0.5)
put(boom(), tf, 0.9); put(crash(3.0), tf, 0.6)

# ---- sidechain : SIDE « pompe » a chaque kick
pump = np.ones(N); tt = np.arange(int(BEAT * SR)) / SR
shape = 1 - 0.85 * np.exp(-tt / 0.09)
for kb in kicks:
    a = int(kb * SR); m = min(len(shape), N - a)
    if m > 0: pump[a:a + m] = np.minimum(pump[a:a + m], shape[:m])
mix = MAIN + SIDE * pump[:, None]

# reverb courte + limiteur doux
ir_t = np.arange(int(1.8 * SR)) / SR
def conv(x, h):
    n = len(x) + len(h); M = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, M) * np.fft.rfft(h, M), M)[:len(x)]
for c in (0, 1):
    ir = rng.normal(0, 1, len(ir_t)) * np.exp(-ir_t / 0.45); ir[:int(0.012 * SR)] = 0; ir /= np.sqrt((ir ** 2).sum())
    mix[:, c] += 0.2 * conv(mix[:, c], ir)
n = int(END * SR); mix = mix[:n]
m = np.abs(mix).max(); mix = np.tanh(1.8 * mix / m) / np.tanh(1.8)
fade = int(0.5 * SR); mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
w = wave.open("audio_agar.wav", "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((mix * 0.93 * 32767).astype(np.int16).tobytes()); w.close()
print(f"{len(hits)} notes, {len(tunnels)} tunnels, fin {END:.2f}s, {BPM} BPM")
