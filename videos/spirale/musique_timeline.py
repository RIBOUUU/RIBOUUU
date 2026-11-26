"""Calendrier de la spirale en boucle calque sur une musique fournie (mp3/wav).

Prend un passage de la musique (debut, fin, instant du drop en secondes dans le morceau), le cale sur
une duree d'un nombre entier d'images multiple de 16 (boucle audio/video parfaite en AAC 48 kHz),
detecte les attaques (onsets) pour les rebonds de la bille, place le tunnel juste avant le drop.

Usage : python3 musique_timeline.py <musique> <debut> <fin> <drop> <nom>
  -> timeline_<nom>.json + audio_<nom>.wav
"""
import sys, json, subprocess, wave, tempfile, os
import numpy as np
import librosa

src, A0, A1, TD, NAME = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
SR, FPS = 48000, 30
NV = int(round((A1 - A0) * FPS / 16)) * 16           # nombre d'images de la boucle
PER = NV / FPS; k = PER / (A1 - A0)                   # facteur d'etirement (tres proche de 1)
print(f"boucle {A1 - A0:.3f}s -> {PER:.3f}s ({NV} images), etirement x{k:.4f}")

tmp = tempfile.mkdtemp(); raw = os.path.join(tmp, "seg.wav")
pad = 0.5                                             # un peu de marge pour le fondu du raccord
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(A0), "-t", str(A1 - A0 + pad), "-i", src,
                "-af", f"atempo={1 / k:.6f}", "-ar", str(SR), "-ac", "2", raw], check=True)
w = wave.open(raw); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2).astype(np.float64) / 32768
n = int(round(PER * SR)); x = x[:n + int(0.05 * SR)]
# raccord : les 40 ms qui suivent la fin sont fondues sur le debut
fd = int(0.04 * SR); ramp = np.linspace(0, 1, fd)[:, None]
loop = x[:n].copy(); loop[:fd] = loop[:fd] * ramp + x[n:n + fd] * (1 - ramp)

# --- attaques (onsets) et temps
mono = librosa.to_mono(loop.T.astype(np.float32)); m22 = librosa.resample(mono, orig_sr=SR, target_sr=22050)
env = librosa.onset.onset_strength(y=m22, sr=22050)
on = librosa.onset.onset_detect(onset_envelope=env, sr=22050, units="time", backtrack=False, delta=0.12)
_, bfr = librosa.beat.beat_track(onset_envelope=env, sr=22050)
beats = list(librosa.frames_to_time(bfr, sr=22050))
strength = {round(t, 3): env[librosa.time_to_frames(t, sr=22050)] for t in on}

EXIT = (TD - A0) * k; RIM = EXIT - 1.9; DROP = EXIT - 0.5
hits = [0.0]
for t in sorted(on):
    if t - hits[-1] >= 0.17 and t < PER - 0.17 and not (RIM - 0.17 < t < EXIT + 0.17): hits.append(t)
hits = sorted(set([round(h, 4) for h in hits] + [round(EXIT, 4)]))
hits = [h for h in hits if not (RIM - 0.17 < h < EXIT - 1e-6)]
rows = []
for i, t in enumerate(hits):
    nxt = hits[i + 1] if i + 1 < len(hits) else PER
    if t < RIM < nxt + 1e-6: nxt = RIM
    rows.append(dict(t=round(t, 4), dur=round(nxt - t, 4), sec=0 if t < EXIT - 1e-6 else 1, note="A4", chord=""))
OFF = round(max(0.0, EXIT - 4.0) * FPS) / FPS
json.dump(dict(period=PER, offset=OFF, hits=rows, tunnel=dict(rim=round(RIM, 4), drop=round(DROP, 4), exit=round(EXIT, 4)),
               kicks=[round(b, 4) for b in beats], boom=round(EXIT, 4), source=os.path.basename(src), extrait=[A0, A1]),
          open(f"timeline_{NAME}.json", "w"), indent=1)
out = np.roll(loop, -int(round(OFF * SR)), axis=0)
st = (np.clip(out, -1, 1) * 32767).astype(np.int16)
w = wave.open(f"audio_{NAME}.wav", "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(st.tobytes()); w.close()
print(f"{len(rows)} rebonds ; tunnel {RIM:.2f}-{EXIT:.2f} ; depart video a {OFF:.2f}s ; {len(beats)} temps")
