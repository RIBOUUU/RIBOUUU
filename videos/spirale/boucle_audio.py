"""Musique ORIGINALE en BOUCLE (16 s, 120 BPM) : montee qui pulse -> tunnel (riser) -> DROP -> retour a la montee.

  0-2 s   : noires qui pulsent (kick + nappe pompee)          | la mineur
  2-4 s   : croches, charleston                               | fa
  4-6 s   : doubles croches qui montent, riser                | sol
  6-8 s   : TUNNEL (tourbillon + tube) : roulement, sifflement, coupure juste avant le drop
  8-16 s  : DROP : kick a chaque temps, basse et accords « supersaw » qui pompent, melodie sur les blocs
La fin du drop retombe sur le debut de la montee : la boucle est parfaite (la reverb deborde sur le debut).
La video demarre a OFFSET = 4 s (en pleine montee) : le drop arrive des la 4e seconde.

Usage : python3 boucle_audio.py -> timeline_boucle.json + audio_boucle.wav
"""
import json, wave
import numpy as np

SR = 48000; P = 16.0; OFFSET = 4.0; BEAT = 0.5
rng = np.random.default_rng(11)
NAMES = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
midi = lambda n: 12 * (int(n[-1]) + 1) + NAMES[n[:-1]]
fr = lambda n: 440.0 * 2 ** ((midi(n) - 69) / 12)

CH = {"Am": ["A2", "A3", "C4", "E4"], "F": ["F2", "A3", "C4", "F4"], "C": ["C3", "G3", "C4", "E4"],
      "G": ["G2", "G3", "B3", "D4"], "E": ["E2", "G#3", "B3", "E4"]}

hits = []
def add(t, note, dur, sec, chord): hits.append(dict(t=round(t, 4), note=note, dur=round(dur, 4), sec=sec, chord=chord))
for k, n in enumerate(["A4", "C5", "E5", "C5"]): add(0 + 0.5 * k, n, 0.5, 0, "Am")
for k, n in enumerate(["F4", "A4", "C5", "A4", "F4", "A4", "C5", "F5"]): add(2 + 0.25 * k, n, 0.25, 0, "F")
up = ["G4", "A4", "B4", "C5", "D5", "E5", "F5", "G5", "A5", "B5", "C6", "D6", "E6", "F6"]
for k, n in enumerate(up): add(4 + 0.125 * k, n, 0.125, 0, "G")
add(5.75, "E6", 0.25, 0, "E")
TUN = dict(rim=6.0, drop=7.5, exit=8.0)
DROP = [("Am", "A5 A5 E6 A5 C6 A5 E6 D6"), ("F", "F5 F5 C6 F5 A5 F5 C6 A5"),
        ("C", "E5 E5 G5 E5 C6 E5 G5 E6"), ("G", "D6 B5 G5 D6 B5 G#5 E5 B5")]
for b, (c, ns) in enumerate(DROP):
    for k, n in enumerate(ns.split()):
        add(8 + 2 * b + 0.25 * k, n, 0.25, 1, "E" if (b == 3 and k >= 4) else c)
KICKS = [0.5 * k for k in range(12)] + [4.25 + 0.5 * k for k in range(4)] + [8 + 0.5 * k for k in range(16)]
KICKS = sorted(set(KICKS))
json.dump({"period": P, "offset": OFFSET, "hits": hits, "tunnel": TUN, "kicks": KICKS, "boom": TUN["exit"]},
          open("timeline_boucle.json", "w"), indent=1)

# ---------------- synthese ----------------
N = int((P + 3.0) * SR); L = np.zeros(N); R = np.zeros(N)
TT = np.arange(N) / SR
sin = lambda f, tt: np.sin(2 * np.pi * f * tt)

def put(sig, t0, gain=1.0, pan=0.5, buf=None):
    a = int(round(t0 * SR)); k = min(len(sig), N - a)
    if k <= 0: return
    if buf is None:
        L[a:a + k] += sig[:k] * gain * np.sqrt(1 - pan); R[a:a + k] += sig[:k] * gain * np.sqrt(pan)
    else:
        buf[0][a:a + k] += sig[:k] * gain * np.sqrt(1 - pan); buf[1][a:a + k] += sig[:k] * gain * np.sqrt(pan)

# enveloppe de « sidechain » : tout ce qui est pompe se creuse a chaque kick (y compris ceux de la boucle suivante)
SC = np.ones(N)
for kt in KICKS + [k + P for k in KICKS]:
    a = int(kt * SR)
    if a >= N: continue
    tt = np.arange(N - a) / SR
    SC[a:] = np.minimum(SC[a:], 1 - 0.88 * np.exp(-tt / 0.13))
PUMP = [np.zeros(N), np.zeros(N)]            # bus pompe

def kick(big=1.0):
    tt = np.arange(int(0.5 * SR)) / SR
    f = 48 + 130 * np.exp(-tt / 0.035)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / (0.2 * big))
    return np.tanh(2.2 * s) + rng.normal(0, 1, len(tt)) * np.exp(-tt / 0.002) * 0.4

def clap():
    tt = np.arange(int(0.3 * SR)) / SR; nz = np.diff(rng.normal(0, 1, len(tt) + 1))
    e = sum(np.exp(-np.maximum(tt - d, 0) / 0.008) * (tt >= d) for d in (0, 0.011, 0.022)) * 0.4 + np.exp(-tt / 0.12) * 0.6
    return nz * e * 0.6

def hat(open_=False):
    tt = np.arange(int((0.25 if open_ else 0.06) * SR)) / SR
    return np.diff(np.diff(rng.normal(0, 1, len(tt) + 2))) * np.exp(-tt / (0.07 if open_ else 0.015)) * 0.12

def snare():
    tt = np.arange(int(0.25 * SR)) / SR
    return np.diff(rng.normal(0, 1, len(tt) + 1)) * np.exp(-tt / 0.07) * 0.5 + sin(190, tt) * np.exp(-tt / 0.04) * 0.5

def saw_stack(f, dur, cut, voices=7, spread=0.012, rel=0.15):
    n = int((dur + rel) * SR); tt = np.arange(n) / SR; s = np.zeros(n)
    for v in range(voices):
        d = 1 + spread * (v / (voices - 1) - 0.5) * 2 if voices > 1 else 1
        ph = rng.uniform(0, 6.28)
        for k in range(1, 40):
            fk = k * f * d
            if fk > 15000: break
            s += np.sin(2 * np.pi * fk * tt + k * ph) / k / (1 + (fk / cut) ** 2)
    e = np.minimum(1, tt / 0.01) * np.clip((dur + rel - tt) / rel, 0, 1)
    return s / voices * e

def pluck(f, dur=0.6, bright=4000):
    n = int(dur * SR); tt = np.arange(n) / SR; s = np.zeros(n)
    for v, d in enumerate((0.996, 1.0, 1.004)):
        for k in range(1, 30):
            fk = k * f * d
            if fk > 15000: break
            s += np.sin(2 * np.pi * fk * tt) / k * np.exp(-tt * (5 + k * fk / bright))
    return s / 3 * np.minimum(1, tt / 0.002)

def bell(f, dur=1.5):
    tt = np.arange(int(dur * SR)) / SR
    return (sin(f, tt) * np.exp(-tt / 0.8) + 0.3 * sin(2.76 * f, tt) * np.exp(-tt / 0.3)
            + 0.15 * sin(5.4 * f, tt) * np.exp(-tt / 0.1)) * np.minimum(1, tt / 0.002)

def band_noise(dur, center, width_oct=0.6):
    n = int(dur * SR); x = rng.normal(0, 1, n + 2048); win = np.hanning(1024); out = np.zeros(n + 2048)
    lf = np.log2(np.maximum(np.fft.rfftfreq(1024, 1 / SR), 1))
    for a in range(0, n, 256):
        g = np.exp(-((lf - np.log2(center(a / n))) / width_oct) ** 2)
        out[a:a + 1024] += np.fft.irfft(np.fft.rfft(x[a:a + 1024] * win) * g) * win
    out = out[:n]; return out / (np.abs(out).max() + 1e-9)

def sub_boom():
    tt = np.arange(int(1.6 * SR)) / SR
    return np.sin(2 * np.pi * np.cumsum(32 + 70 * np.exp(-tt / 0.2)) / SR) * np.exp(-tt / 0.7)

def crash(dur=2.2):
    tt = np.arange(int(dur * SR)) / SR
    return np.diff(rng.normal(0, 1, len(tt) + 1)) * np.exp(-tt / 0.8) * 0.45

# --- montee : kicks, nappe filtree qui s'ouvre, charleston, riser
for kt in KICKS:
    if kt < 6: put(kick(0.8), kt, 0.55)
    else: put(kick(1.2), kt, 0.85)
for c0, c1, ch in ((0, 2, "Am"), (2, 4, "F"), (4, 6, "G"), (6, 7.75, "E")):
    cut = 500 + 2500 * (c0 / 6) ** 1.5
    for q, n in enumerate(CH[ch][1:]):
        put(saw_stack(fr(n), c1 - c0, cut, voices=5, rel=0.3), c0, 0.07, 0.3 + 0.2 * q, PUMP)
    put(saw_stack(fr(CH[ch][0]), c1 - c0, 300, voices=2, rel=0.2), c0, 0.16, 0.5, PUMP)
for k in range(8):  put(hat(), 2 + 0.25 * k + 0.125, 0.8, 0.65)
for k in range(16): put(hat(), 4 + 0.125 * k, 0.7 + 0.03 * k, 0.35 + 0.3 * (k % 2))
# roulement : croches puis doubles puis triples, de 4 a 7.75 s
tq = 4.0
while tq < 7.74:
    x = (tq - 4) / 3.75
    put(snare(), tq, 0.12 + 0.5 * x, 0.5)
    tq += 0.25 if tq < 5 else (0.125 if tq < 6.5 else 0.0625)
put(band_noise(3.75, lambda u: 400 * 25 ** u) * np.linspace(0.1, 1, int(3.75 * SR)) ** 1.5, 4.0, 0.7)
# sifflement du tourbillon (monte avec la vitesse de rotation)
n = int(1.5 * SR); tt = np.arange(n) / SR; u = tt / 1.5
ph = 2 * np.pi * np.cumsum(260 * 5.5 ** (u ** 1.5)) / SR
put(np.sin(ph) * (0.2 + 0.8 * u ** 1.3) * (1 + 0.5 * np.sin(2 * np.pi * np.cumsum(3 + 22 * u ** 2) / SR)), 6.0, 0.3)
# riser de hauteur : accord en dents de scie qui monte d'une octave pendant le tunnel
n = int(1.75 * SR); tt = np.arange(n) / SR; u = tt / 1.75; rs = np.zeros(n)
for base in (fr("E3"), fr("B3"), fr("E4")):
    ph = 2 * np.pi * np.cumsum(base * 2 ** (u ** 1.6)) / SR
    for k in range(1, 12): rs += np.sin(k * ph) / k * (1 / (1 + (k * base * 2 / 3000) ** 2))
put(rs / 6 * u ** 1.2, 6.0, 0.35)
# chute dans le tube : souffle qui descend ; coupure (silence) le dernier quart de temps
put(band_noise(0.5, lambda u: 5000 * 0.1 ** u, 0.7) * np.sin(np.linspace(0, np.pi, int(0.5 * SR))) ** 0.5, 7.5, 0.5)

# --- melodie sur les blocs
for i, h in enumerate(hits):
    f = fr(h["note"]); pan = 0.5 + 0.2 * np.sin(i * 1.7)
    if h["sec"] == 0:
        put(bell(f), h["t"], 0.32, pan); put(pluck(f, 0.4, 2500), h["t"], 0.25, 1 - pan)
    else:
        put(pluck(f, 0.5, 9000), h["t"], 0.42, pan); put(bell(f * 2, 0.8), h["t"], 0.10, 1 - pan)
        put(saw_stack(f, 0.18, 6000, voices=5, rel=0.08), h["t"], 0.10, 0.5)

# --- DROP
put(sub_boom(), 8.0, 1.0); put(crash(), 8.0, 0.6); put(crash(), 12.0, 0.35)
for b, (c, _) in enumerate(DROP):
    t0 = 8 + 2 * b
    parts = [(t0, 2.0, c)] if b < 3 else [(t0, 1.0, "G"), (t0 + 1, 1.0, "E")]
    for s0, d, ch in parts:
        for q, n in enumerate(CH[ch][1:]):
            put(saw_stack(fr(n), d, 5500, voices=7, rel=0.05), s0, 0.085, 0.2 + 0.3 * q, PUMP)
            put(saw_stack(fr(n) * 2, d, 7000, voices=5, rel=0.05), s0, 0.035, 0.8 - 0.3 * q, PUMP)
        for k in range(int(d / 0.25)):              # basse en croches (pompee)
            bt = s0 + 0.25 * k
            put(saw_stack(fr(CH[ch][0]), 0.22, 900, voices=2, rel=0.02), bt, 0.28, 0.5, PUMP)
            put(sin(fr(CH[ch][0]) / 2, np.arange(int(0.24 * SR)) / SR) * np.hanning(int(0.24 * SR)), bt, 0.35, 0.5, PUMP)
for k in range(16):
    bt = 8 + 0.5 * k
    put(hat(True), bt + 0.25, 0.9, 0.62)
    put(hat(), bt, 0.5, 0.38); put(hat(), bt + 0.125, 0.35, 0.4); put(hat(), bt + 0.375, 0.35, 0.6)
    if k % 2 == 1: put(clap(), bt, 0.55, 0.5)
for k in range(4): put(snare(), 15.5 + 0.125 * k, 0.25 + 0.1 * k, 0.5)     # petite relance vers la montee

L += PUMP[0] * SC; R += PUMP[1] * SC
# coupure avant le drop : tout sauf le souffle s'efface de 7.75 a 8.0
a, b = int(7.72 * SR), int(8.0 * SR)
g = np.ones(N); g[a:b] = np.linspace(1, 0.15, b - a) ** 2
L *= g; R *= g

# reverb
ir_t = np.arange(int(2.0 * SR)) / SR
def ir():
    x = rng.normal(0, 1, len(ir_t)) * np.exp(-ir_t / 0.45); x[:int(0.012 * SR)] = 0
    return x / np.sqrt((x ** 2).sum())
def conv(x, h):
    n = len(x) + len(h); M = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, M) * np.fft.rfft(h, M), M)[:len(x)]
L = L + 0.22 * conv(L, ir()); R = R + 0.22 * conv(R, ir())
# boucle : la queue (apres 16 s) se replie sur le debut, puis on demarre a OFFSET
n = int(P * SR)
for ch in (L, R): ch[:N - n] += ch[n:].copy()
L, R = L[:n], R[:n]
k0 = int(OFFSET * SR); L, R = np.roll(L, -k0), np.roll(R, -k0)
m = max(np.abs(L).max(), np.abs(R).max())
L, R = np.tanh(1.8 * L / m) / np.tanh(1.8), np.tanh(1.8 * R / m) / np.tanh(1.8)
st = (np.stack([L, R], 1) * 0.92 * 32767).astype(np.int16)
w = wave.open("audio_boucle.wav", "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(st.tobytes()); w.close()
print(len(hits), "notes ; boucle", P, "s ; depart a", OFFSET, "s")
