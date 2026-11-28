"""Calendrier + audio pour « Lost Sky - Fearless [NCS Release] » : 31 temps (16,5 s) autour du 1er drop.
Rebonds sur la grille rythmique (noires puis croches), tunnel 2 qui se termine pile sur le drop,
« blop » (fichier fourni) a chaque rebond.
Usage : python3 fearless_timeline.py <fearless.mp3> <blop.mp3>  -> timeline_fearless.json + audio_fearless.wav
"""
import sys, json, subprocess, tempfile, os, wave
import numpy as np
SRC, BLOP = sys.argv[1], sys.argv[2]
B = 0.534059; DROP = 52.41; SR = 48000
A0 = DROP - 32 * B                     # 1 temps d'intro (la bille tombe), drop au temps 32 (17,1 s)
NB = 56; DURV = NB * B
beat = lambda k: k * B                 # temps k depuis le debut de l'extrait
hits = []
def add(k0, k1, step, sec):
    k = k0
    while k < k1 - 1e-9:
        hits.append(dict(t=round(beat(k), 5), dur=round(step * B, 5), sec=sec, note="A4", chord="", i=0)); k += step
add(1, 11, 1, 0)                       # A : noires (10 rebonds), tunnel 1 de 11 a 14
add(14, 28, 0.5, 1)                    # B : croches (28 rebonds), tunnel 2 de 28 a 32 = DROP
add(32, 43, 0.5, 2)                    # C (drop) : croches (22 rebonds), tunnel 3 de 43 a 46
add(46, 54, 0.5, 3)                    # D : croches (16 rebonds)
hits.append(dict(t=round(beat(54), 5), dur=round(2 * B, 5), sec=3, note="A4", chord="", i=0))   # saut final
for s in range(4):
    for i, h in enumerate([h for h in hits if h["sec"] == s]): h["i"] = i
tun = [dict(rim=beat(11), drop=beat(13), exit=beat(14)), dict(rim=beat(28), drop=beat(31), exit=beat(32)), dict(rim=beat(43), drop=beat(45), exit=beat(46))]
plan = {0: [[1, 8, "ressort"]], 1: [[1, 13, "booster"], [14, 26, "glace"]], 2: [[1, 10, "verre"], [11, 20, "aimant"]], 3: [[1, 7, "ventilo"], [8, 15, "canon"]]}
json.dump(dict(hits=hits, tunnels=[{k: round(v, 5) for k, v in t.items()} for t in tun], end=round(DURV, 5), plan=plan,
               source="Lost Sky - Fearless [NCS Release]", extrait=[A0, A0 + DURV]), open("timeline_fearless.json", "w"), indent=1)
def load(path, ss=None, t=None):
    tmp = tempfile.mktemp(suffix=".wav"); cmd = ["ffmpeg", "-v", "error", "-y"]
    if ss is not None: cmd += ["-ss", f"{ss:.4f}", "-t", f"{t:.4f}"]
    subprocess.run(cmd + ["-i", path, "-ar", str(SR), "-ac", "2", tmp], check=True)
    w = wave.open(tmp); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2) / 32768; os.remove(tmp); return x
mus = load(SRC, A0, DURV).copy(); n = int(round(DURV * SR)); mus = mus[:n]
fi = int(0.03 * SR); mus[:fi] *= np.linspace(0, 1, fi)[:, None]
fo = int(0.5 * SR); mus[-fo:] *= np.linspace(1, 0, fo)[:, None]
bl = load(BLOP); bl = bl / (np.abs(bl).max() + 1e-9)
for h in hits:
    a = int(round(h["t"] * SR)); k = min(len(bl), n - a); g = 0.35 if h["sec"] < 2 else 0.3
    mus[a:a + k] += bl[:k] * g
mus /= max(1.0, np.abs(mus).max() / 0.98)
w = wave.open("audio_fearless.wav", "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((mus * 32767).astype(np.int16).tobytes()); w.close()
print(len(hits), "rebonds ; drop a", round(tun[1]["exit"], 3), "s ; duree", round(DURV, 3))
