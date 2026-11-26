"""Musique ORIGINALE de plus en plus epique pour la video 'spirale epique'.

3 parties separees par 2 tunnels (entonnoir qui aspire la bille, puis tube en verre) :
  A (la mineur, lent)   : cloches + nappe de cordes douce
  -> tunnel 1 : sifflement qui monte, souffle aspire, BOUM a la sortie
  B (plus rapide)       : marimba + batterie + basse + cordes
  -> tunnel 2 : roulement de caisse claire, choeur qui enfle, BOUM
  C (si mineur, +2 demi-tons, encore plus rapide) : cuivres + choeur + timbales + cymbales, accord final

Usage : python3 epique_audio.py   -> timeline_epique.json + audio_epique.wav
"""
import json, wave
import numpy as np

SR = 48000
T0 = 0.06
rng = np.random.default_rng(3)
NAMES = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
NN = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
midi = lambda n: 12 * (int(n[-1]) + 1) + NAMES[n[:-1]]
nm = lambda m: NN[m % 12] + str(m // 12 - 1)
fr = lambda n: 440.0 * 2 ** ((midi(n) - 69) / 12)
tr = lambda n, k: nm(midi(n) + k)

CHORDS = {"Am": ("A2", ["A3", "C4", "E4"]), "F": ("F2", ["F3", "A3", "C4"]),
          "C": ("C3", ["C4", "E4", "G4"]), "E": ("E2", ["E3", "G#3", "B3"])}
SECS = [
    dict(unit=0.40, last=0.55, F=1.7, D=0.5, tr=0,
         mel=["A4", "C5", "E5", "A5", "G5", "E5", "F5", "E5"],
         ch=["Am", "Am", "Am", "Am", "C", "C", "F", "E"]),
    dict(unit=0.30, last=0.50, F=1.5, D=0.45, tr=0,
         mel=["A5", "E5", "C6", "E5", "F5", "C6", "A5", "C6", "E5", "G#5", "B5", "E6"],
         ch=["Am"] * 4 + ["F"] * 4 + ["E"] * 4),
    dict(unit=0.24, last=1.6, F=0, D=0, tr=2,
         mel=["A5", "C6", "E6", "F6", "E6", "C6", "E6", "D6", "C6", "B5", "G#5", "B5", "C6", "A5"],
         ch=["Am"] * 3 + ["F"] * 3 + ["C"] * 3 + ["E"] * 3 + ["Am", "Am"]),
]

# ---------------- calendrier ----------------
hits, tunnels, t = [], [], T0
for s, S in enumerate(SECS):
    n = len(S["mel"])
    for i in range(n):
        d = S["unit"] if i < n - 1 else S["last"]
        hits.append({"t": round(t, 4), "note": tr(S["mel"][i], S["tr"]), "dur": round(d, 4), "sec": s, "i": i,
                     "chord": S["ch"][i]})
        t += d
    if S["F"]:
        tunnels.append({"rim": round(t, 4), "drop": round(t + S["F"], 4), "exit": round(t + S["F"] + S["D"], 4)})
        t += S["F"] + S["D"]
END = round(hits[-1]["t"] + 1.5, 4)
json.dump({"hits": hits, "tunnels": tunnels, "end": END}, open("timeline_epique.json", "w"), indent=1)

# ---------------- outils de synthese ----------------
N = int((END + 3.0) * SR)
L = np.zeros(N); R = np.zeros(N)
sin = lambda f, tt: np.sin(2 * np.pi * f * tt)

def put(sig, t0, gain=1.0, pan=0.5):
    a = int(t0 * SR)
    if a < 0: sig = sig[-a:]; a = 0
    k = min(len(sig), N - a)
    if k <= 0: return
    L[a:a + k] += sig[:k] * gain * np.sqrt(1 - pan); R[a:a + k] += sig[:k] * gain * np.sqrt(pan)

def env_adsr(n, att, rel, total):
    tt = np.arange(n) / SR
    e = np.minimum(1, tt / max(att, 1e-4))
    return e * np.clip((total - tt) / rel, 0, 1)

def bell(f, dur=2.5):
    tt = np.arange(int(dur * SR)) / SR
    s = (sin(f, tt) * np.exp(-tt / 1.1) + 0.35 * sin(2.76 * f, tt) * np.exp(-tt / 0.5)
         + 0.2 * sin(5.4 * f, tt) * np.exp(-tt / 0.2) + 0.5 * sin(f / 2, tt) * np.exp(-tt / 0.8) * 0.3)
    return s * np.minimum(1, tt / 0.002)

def marimba(f, dur=1.8):
    tt = np.arange(int(dur * SR)) / SR
    s = (sin(f, tt) * np.exp(-tt / 0.55) + 0.2 * sin(2 * f, tt) * np.exp(-tt / 0.3)
         + 0.3 * sin(3.93 * f, tt) * np.exp(-tt / 0.12) + 0.1 * sin(9.9 * f, tt) * np.exp(-tt / 0.04))
    return (s + rng.normal(0, 1, len(tt)) * np.exp(-tt / 0.004) * 0.15) * np.minimum(1, tt / 0.002)

def additive(f, dur, weight, att=0.2, rel=0.5, det=(-0.006, 0.0, 0.007), vib=0.0):
    """dent de scie additive (sans repliement) ; weight(k, fk, tt) -> amplitude du partiel k."""
    n = int((dur + rel) * SR); tt = np.arange(n) / SR
    s = np.zeros(n)
    ph_vib = vib * np.sin(2 * np.pi * 5.2 * tt) if vib else 0
    for d in det:
        fd = f * (1 + d)
        for k in range(1, 60):
            fk = k * fd
            if fk > 14000: break
            w = weight(k, fk, tt)
            s += w / k * np.sin(2 * np.pi * fk * tt + k * ph_vib + rng.uniform(0, 6.28))
    return s / len(det) * env_adsr(n, att, rel, dur + rel)

def strings(f, dur, cut=2200.0):
    return additive(f, dur, lambda k, fk, tt: 1 / (1 + (fk / cut) ** 2), att=0.25, rel=0.6, vib=0.002)

def choir(f, dur):
    form = lambda fk: (np.exp(-((fk - 750) / 140) ** 2) + 0.7 * np.exp(-((fk - 1150) / 160) ** 2)
                       + 0.35 * np.exp(-((fk - 2700) / 260) ** 2) + 0.08)
    return additive(f, dur, lambda k, fk, tt: form(fk) * k ** 0.6, att=0.35, rel=0.8, det=(-0.008, -0.002, 0.004, 0.009), vib=0.004)

def brass(f, dur):
    def w(k, fk, tt):
        e = np.minimum(1, tt / 0.06) * np.exp(-tt / 0.9) * 0.7 + 0.3
        return np.exp(-fk / (500 + 3500 * e))
    return additive(f, dur, w, att=0.03, rel=0.25, det=(-0.004, 0.004))

def bass_pluck(f, dur):
    n = int((dur + 0.15) * SR); tt = np.arange(n) / SR
    s = np.zeros(n)
    for k in range(1, 12):
        s += sin(k * f, tt) / k * np.exp(-tt * (3 + 3 * k))
    return (s + 0.6 * sin(f, tt) * np.exp(-tt / 0.5)) * env_adsr(n, 0.004, 0.08, dur + 0.15)

def kick(big=1.0):
    tt = np.arange(int(0.7 * SR)) / SR
    f = 45 + 110 * np.exp(-tt / 0.045)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) * np.exp(-tt / (0.22 * big)) + rng.normal(0, 1, len(tt)) * np.exp(-tt / 0.003) * 0.3)

def snare():
    tt = np.arange(int(0.35 * SR)) / SR
    nz = np.diff(rng.normal(0, 1, len(tt) + 1))
    return nz * np.exp(-tt / 0.09) * 0.5 + sin(185, tt) * np.exp(-tt / 0.05) * 0.6

def hat():
    tt = np.arange(int(0.08 * SR)) / SR
    return np.diff(np.diff(rng.normal(0, 1, len(tt) + 2))) * np.exp(-tt / 0.018) * 0.12

def timpani(f):
    tt = np.arange(int(1.6 * SR)) / SR
    ff = f * (1 + 0.04 * np.exp(-tt / 0.1))
    ph = 2 * np.pi * np.cumsum(ff) / SR
    return (np.sin(ph) + 0.5 * np.sin(1.5 * ph) * np.exp(-tt / 0.3)) * np.exp(-tt / 0.6) + \
        rng.normal(0, 1, len(tt)) * np.exp(-tt / 0.01) * 0.2

def crash(dur=2.6):
    tt = np.arange(int(dur * SR)) / SR
    nz = np.diff(rng.normal(0, 1, len(tt) + 1))
    return nz * np.exp(-tt / 0.9) * np.minimum(1, tt / 0.003) * 0.5

def band_noise(dur, center, width_oct=0.6, amp=None):
    """bruit filtre dont la frequence centrale suit center(u), u = 0..1 (STFT)."""
    n = int(dur * SR); x = rng.normal(0, 1, n + 2048)
    win = np.hanning(1024); hop = 256; out = np.zeros(n + 2048)
    fq = np.fft.rfftfreq(1024, 1 / SR); lf = np.log2(np.maximum(fq, 1))
    for a in range(0, n, hop):
        u = a / n; c = np.log2(center(u))
        g = np.exp(-((lf - c) / width_oct) ** 2)
        seg = np.fft.irfft(np.fft.rfft(x[a:a + 1024] * win) * g)
        out[a:a + 1024] += seg * win
    out = out[:n]
    out /= np.abs(out).max() + 1e-9
    if amp is not None: out *= amp(np.arange(n) / n)
    return out

def sub_boom():
    tt = np.arange(int(2.2 * SR)) / SR
    f = 30 + 60 * np.exp(-tt / 0.25)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.9)

# ---------------- ecriture ----------------
for h in hits:
    s, i, t0 = h["sec"], h["i"], h["t"]
    f = fr(h["note"]); S = SECS[s]
    pan = 0.5 + 0.22 * np.sin(i * 1.3)
    if s == 0:
        put(bell(f), t0, 0.55, pan); put(marimba(f / 2), t0, 0.25, 0.5)
    elif s == 1:
        put(marimba(f), t0, 0.7, pan); put(bell(f * 2, 1.5), t0, 0.12, 1 - pan)
    else:
        put(bell(f), t0, 0.45, pan); put(marimba(f / 2), t0, 0.35, 0.5)
        put(brass(f / 2, min(h["dur"], 0.5)), t0, 0.22, 0.45); put(brass(f / 4, min(h["dur"], 0.5)), t0, 0.16, 0.55)
    # petit "toc" du bloc qui rebondit
    tt = np.arange(int(0.12 * SR)) / SR
    put(sin(140 + 40 * s, tt) * np.exp(-tt / 0.03), t0, 0.25)

# nappes + basses par accord (segments consecutifs du meme accord)
for s, S in enumerate(SECS):
    hs = [h for h in hits if h["sec"] == s]
    k = 0
    while k < len(hs):
        j = k
        while j + 1 < len(hs) and hs[j + 1]["chord"] == hs[k]["chord"]: j += 1
        t0 = hs[k]["t"]; t1 = hs[j]["t"] + hs[j]["dur"]
        if s < len(tunnels) and j == len(hs) - 1: t1 = tunnels[s]["exit"]
        bass, notes = CHORDS[hs[k]["chord"]]
        bass = tr(bass, S["tr"]); notes = [tr(n, S["tr"]) for n in notes]
        dur = t1 - t0
        for q, n in enumerate(notes):
            put(strings(fr(n), dur, cut=1400 + 900 * s), t0, (0.10, 0.13, 0.15)[s], 0.25 + 0.25 * q)
            if s == 2: put(choir(fr(n) * (2 if q == 0 else 1), dur), t0, 0.09, 0.75 - 0.25 * q)
        if s == 0:
            put(strings(fr(bass), dur, cut=500), t0, 0.22)
        k = j + 1

for h in hits:
    s, i, t0 = h["sec"], h["i"], h["t"]
    b = fr(tr(CHORDS[h["chord"]][0], SECS[s]["tr"]))
    if s == 0:
        if i % 4 == 0: put(kick(0.8), t0, 0.35); put(timpani(b), t0, 0.25)
    if s >= 1:
        put(bass_pluck(b * (2 if i % 2 else 1), min(h["dur"], 0.4)), t0, 0.32 if s == 1 else 0.38)
        put(hat(), t0, 0.8, 0.65); put(hat(), t0 + h["dur"] / 2, 0.5, 0.35)
        if i % 4 == 0 or (s == 2 and i % 2 == 0): put(kick(), t0, 0.7)
        if i % 4 == 2: put(snare(), t0, 0.45 if s == 1 else 0.55)
    if s == 2:
        if i % 3 == 0: put(timpani(b), t0, 0.45)
        if i % 6 == 0: put(crash(), t0, 0.35)
        put(sub_boom()[:int(0.3 * SR)] * np.linspace(1, 0, int(0.3 * SR)), t0, 0.2)

# tunnels : sifflement de tourbillon, souffle aspire, roulement, BOUM
for k, T in enumerate(tunnels):
    F = T["drop"] - T["rim"]; D = T["exit"] - T["drop"]; tot = T["exit"] - T["rim"]
    n = int(F * SR); tt = np.arange(n) / SR; u = tt / F
    f = 260 * (5.5 ** (u ** 1.5))                       # monte avec la vitesse de rotation
    ph = 2 * np.pi * np.cumsum(f) / SR
    wob = 1 + 0.5 * np.sin(2 * np.pi * np.cumsum(3 + 22 * u ** 2) / SR)
    put(np.sin(ph) * wob * (0.15 + 0.85 * u ** 1.3), T["rim"], 0.22)
    put(band_noise(tot, lambda x: 300 * 20 ** x, 0.5, lambda x: 0.25 + 0.75 * x ** 1.5), T["rim"], 0.8 + 0.2 * k)
    put(band_noise(D, lambda x: 4000 * 0.12 ** x, 0.7, lambda x: np.sin(np.pi * x) ** 0.5), T["drop"], 0.7)
    # roulement de caisse claire qui accelere (plus fort au 2e tunnel)
    tq = 0.0
    while tq < tot - 0.05:
        x = tq / tot
        put(snare(), T["rim"] + tq, (0.15 + 0.6 * x) * (0.7 if k == 0 else 1.0), 0.5 + 0.2 * np.sin(tq * 20))
        tq += 0.16 - 0.11 * x
    if k == 1:
        put(choir(fr("E4"), tot), T["rim"], 0.12); put(choir(fr("B4"), tot), T["rim"], 0.10)
    put(crash()[::-1][-int(tot * SR):] * 0.6, T["exit"] - tot, 0.4)   # cymbale a l'envers
    # sortie : BOUM
    put(sub_boom(), T["exit"], 0.9); put(kick(1.5), T["exit"], 0.8); put(crash(), T["exit"], 0.55)
    put(timpani(fr("A2") if k == 0 else fr("B2")), T["exit"], 0.6)

# accord final
hf = hits[-1]; tf = hf["t"]
for n in ["B2", "B3", "D4", "F#4", "B4"]:
    put(brass(fr(n), 1.4), tf, 0.16); put(choir(fr(n) * (2 if n > "B3" else 1), 1.6), tf, 0.10)
put(sub_boom(), tf, 0.9); put(crash(3.0), tf, 0.6); put(timpani(fr("B2")), tf, 0.7)
put(bell(fr("B5"), 3.0), tf, 0.5); put(bell(fr("F#6"), 3.0), tf, 0.3)

# reverb (salle) + compression douce
ir_t = np.arange(int(2.6 * SR)) / SR
def ir():
    x = rng.normal(0, 1, len(ir_t)) * np.exp(-ir_t / 0.7); x[:int(0.015 * SR)] = 0
    return x / np.sqrt((x ** 2).sum())
def conv(x, h):
    n = len(x) + len(h); M = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, M) * np.fft.rfft(h, M), M)[:len(x)]
L = L + 0.3 * conv(L, ir()); R = R + 0.3 * conv(R, ir())
n = int(END * SR); L, R = L[:n], R[:n]
m = max(np.abs(L).max(), np.abs(R).max())
L, R = np.tanh(1.6 * L / m) / np.tanh(1.6), np.tanh(1.6 * R / m) / np.tanh(1.6)
fade = int(0.5 * SR); L[-fade:] *= np.linspace(1, 0, fade); R[-fade:] *= np.linspace(1, 0, fade)
st = (np.stack([L, R], 1) * 0.92 * 32767).astype(np.int16)
w = wave.open("audio_epique.wav", "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(st.tobytes()); w.close()
print(f"{len(hits)} notes, {len(tunnels)} tunnels, fin {END:.2f}s")
