"""Boucle qui enchaine les drops de 3 morceaux, relies par les tunnels :
  Lost Sky - Fearless (110 BPM)  ->  Kraddy - Android (95 BPM)  ->  Gioni - Trigger (90 BPM)  -> (boucle)
Chaque tunnel = les 4 derniers temps de la montee du morceau suivant ; la bille sort du tube pile sur son drop.
Rebonds sur chaque croche du drop. Au moins 10 s par morceau ; le morceau qui finit baisse progressivement pendant le tunnel (fondu),
pendant que la montee du suivant arrive : jamais de blanc. Duree = multiple de 16 images (boucle AAC parfaite).

Usage : python3 medley_boucle.py <fearless.mp3> <android.mp3> <trigger.mp3> <blop.mp3>
        -> timeline_medley.json + audio_medley.wav
"""
import sys, json, subprocess, tempfile, os, wave
import numpy as np
FE, AN, TR, BLOP = sys.argv[1:5]
SR, FPS = 48000, 30
SONGS = [  # fichier, duree d'un temps, instant du drop, temps de drop joues, fin de la montee utilisee pour le tunnel
    dict(f=FE, B=60 / 110, D=52.452, n=18, be=52.452),
    dict(f=AN, B=60 / 95, D=94.14, n=16, be=90.6),       # Android : silence de 3 s avant le drop -> on prend la montee juste avant
    dict(f=TR, B=60 / 90, D=97.709, n=15, be=97.709),
]
TUNB = 4                                                 # duree d'un tunnel en temps du morceau suivant
raw = sum(S["n"] * S["B"] + TUNB * S["B"] for S in SONGS)
NV = int(round(raw * FPS / 16)) * 16; PER = NV / FPS; k = PER / raw
print(f"periode brute {raw:.3f}s -> {PER:.3f}s ({NV} images, x{k:.4f})")
hits, tunnels, t, segs = [], [], 0.0, []
for q, S in enumerate(SONGS):
    B = S["B"] * k; segs.append(t)
    for j in range(2 * S["n"]):
        hits.append(dict(t=round(t + j * B / 2, 5), dur=round(B / 2, 5), sec=q, i=j, note="A4", chord=""))
    t += S["n"] * B
    NB = SONGS[(q + 1) % 3]["B"] * k
    tunnels.append(dict(rim=round(t, 5), drop=round(t + (TUNB - 1) * NB, 5), exit=round(t + TUNB * NB, 5))); t += TUNB * NB
OFF = round(2 * SONGS[0]["B"] * k * FPS) / FPS            # la video commence 2 temps apres le drop de Fearless
plan = {0: [[1, 17, "ressort"], [18, 34, "vrille"]], 1: [[1, 15, "verre"], [16, 30, "bumper"]], 2: [[1, 14, "aimant"], [15, 28, "ventilo"]]}
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
n = int(round(PER * SR)); out = np.zeros((n + 2 * SR, 2))
def place(x, t0):
    a = int(round(t0 * SR)) % n
    m = len(x); idx = (np.arange(m) + a) % n; np.add.at(out, idx, x)        # enroule sur la boucle
for q, S in enumerate(SONGS):
    N = SONGS[(q + 1) % 3]; tun = tunnels[q]; L = tun["exit"] - tun["rim"]
    # drop du morceau q, qui continue pendant le tunnel suivant en baissant progressivement
    d = S["n"] * S["B"] + TUNB * N["B"] * 1.0
    x = load(S["f"], S["D"], d, 1 / k)[:int(round((tun["exit"] - segs[q]) * SR))].copy()
    m0 = int(round((tun["rim"] - segs[q]) * SR)); m1 = len(x)
    g = np.ones(m1); g[m0:] = np.linspace(1, 0, m1 - m0) ** 0.9
    fi = int(0.008 * SR); g[:fi] *= np.linspace(0, 1, fi)
    place(x * g[:, None], segs[q])
    # montee du morceau suivant pendant le tunnel : elle arrive en fondu
    y = load(N["f"], N["be"] - TUNB * N["B"], TUNB * N["B"], 1 / k)[:int(round(L * SR))].copy()
    g = np.clip(np.arange(len(y)) / (0.6 * len(y)), 0, 1) ** 1.3; fo = int(0.01 * SR); g[-fo:] *= np.linspace(1, 0, fo)
    place(y * g[:, None], tun["rim"])
loop = out[:n].copy()
# niveaux : chaque morceau a peu pres au meme volume
bl = load(BLOP); bl = bl / (np.abs(bl).max() + 1e-9)
for h in hits:
    a = int(round(h["t"] * SR)); m = min(len(bl), n - a); loop[a:a + m] += bl[:m] * 0.3
loop /= max(1.0, np.abs(loop).max() / 0.98)
loop = np.roll(loop, -int(round(OFF * SR)), axis=0)
w = wave.open("audio_medley.wav", "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((loop * 32767).astype(np.int16).tobytes()); w.close()
print(len(hits), "rebonds ; tunnels", [(round(x["rim"], 2), round(x["exit"], 2)) for x in tunnels], "; depart", OFF)
