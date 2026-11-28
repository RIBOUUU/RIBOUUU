"""Boucle de 19,2 s qui enchaine les drops de 3 morceaux, relies par les tunnels :
  Lost Sky - Fearless (110 BPM)  ->  Kraddy - Android (95 BPM)  ->  Gioni - Trigger (90 BPM)  -> (boucle)
Chaque tunnel = les 4 derniers temps de la montee du morceau suivant ; la bille sort du tube pile sur son drop.
Rebonds sur chaque croche du drop. Duree = 576 images (multiple de 16 : boucle audio AAC parfaite).

Usage : python3 medley_boucle.py <fearless.mp3> <android.mp3> <trigger.mp3> <blop.mp3>
        -> timeline_medley.json + audio_medley.wav
"""
import sys, json, subprocess, tempfile, os, wave
import numpy as np
FE, AN, TR, BLOP = sys.argv[1:5]
SR, FPS, NV = 48000, 30, 576
SONGS = [  # fichier, temps (s), instant du drop (s), temps de drop joues, couleur/blocs dans timeline
    dict(f=FE, B=60 / 110, D=52.452, n=7),
    dict(f=AN, B=60 / 95, D=94.14, n=6),
    dict(f=TR, B=60 / 90, D=97.709, n=6),
]
pieces = []                       # (fichier, debut, duree) dans l'ordre de la periode
for q, S in enumerate(SONGS):
    pieces.append((S["f"], S["D"], S["n"] * S["B"]))                      # drop du morceau q
    N = SONGS[(q + 1) % 3]; pieces.append((N["f"], N["D"] - 4 * N["B"], 4 * N["B"]))   # montee du suivant = tunnel
raw = sum(p[2] for p in pieces); PER = NV / FPS; k = PER / raw
print(f"periode brute {raw:.3f}s -> {PER:.3f}s (x{k:.4f})")
hits, tunnels, t = [], [], 0.0
for q, S in enumerate(SONGS):
    B = S["B"] * k
    for j in range(2 * S["n"]):
        hits.append(dict(t=round(t + j * B / 2, 5), dur=round(B / 2, 5), sec=q, i=j, note="A4", chord=""))
    t += S["n"] * B
    NB = SONGS[(q + 1) % 3]["B"] * k
    tunnels.append(dict(rim=round(t, 5), drop=round(t + 3 * NB, 5), exit=round(t + 4 * NB, 5))); t += 4 * NB
OFF = round(2 * SONGS[0]["B"] * k * FPS) / FPS            # la video commence 2 temps apres le drop de Fearless
plan = {0: [[1, 6, "ressort"], [7, 12, "booster"]], 1: [[1, 5, "verre"], [6, 10, "aimant"]], 2: [[1, 5, "glace"], [6, 10, "canon"]]}
json.dump(dict(loop=True, period=PER, offset=OFF, hits=hits, tunnels=tunnels, end=PER, plan=plan,
               sources=["Lost Sky - Fearless [NCS Release]", "Kraddy - Android", "Gioni - Trigger"]),
          open("timeline_medley.json", "w"), indent=1)

def load(path, ss=None, dur=None, tempo=None):
    tmp = tempfile.mktemp(suffix=".wav"); cmd = ["ffmpeg", "-v", "error", "-y"]
    if ss is not None: cmd += ["-ss", f"{ss:.4f}", "-t", f"{dur + 0.2:.4f}"]
    cmd += ["-i", path]
    if tempo: cmd += ["-af", f"atempo={tempo:.6f}"]
    subprocess.run(cmd + ["-ar", str(SR), "-ac", "2", tmp], check=True)
    w = wave.open(tmp); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2) / 32768; os.remove(tmp); return x
n = int(round(PER * SR)); out = np.zeros((n + SR, 2)); pos = 0.0
fd = int(0.008 * SR)
for f, ss, d in pieces:
    x = load(f, ss, d, 1 / k).copy(); m = int(round(d * k * SR))
    x = x[:m + fd]; x[:fd] *= np.linspace(0, 1, fd)[:, None]; x[-fd:] *= np.linspace(1, 0, fd)[:, None]
    a = int(round(pos * SR)); out[a:a + len(x)] += x; pos += d * k
loop = out[:n].copy(); loop[:fd] += out[n:n + fd]                     # raccord de boucle
# niveaux : chaque morceau a peu pres au meme volume
bl = load(BLOP); bl = bl / (np.abs(bl).max() + 1e-9)
for h in hits:
    a = int(round(h["t"] * SR)); m = min(len(bl), n - a); loop[a:a + m] += bl[:m] * 0.3
loop /= max(1.0, np.abs(loop).max() / 0.98)
loop = np.roll(loop, -int(round(OFF * SR)), axis=0)
w = wave.open("audio_medley.wav", "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((loop * 32767).astype(np.int16).tobytes()); w.close()
print(len(hits), "rebonds ; tunnels", [(round(x["rim"], 2), round(x["exit"], 2)) for x in tunnels], "; depart", OFF)
