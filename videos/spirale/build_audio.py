"""Timeline + audio pour la video 'spirale' (bille qui joue une melodie sur des paves).
Melodie : Grieg, 'Dans l'antre du roi de la montagne' (1876, domaine public).
Usage : python3 build_audio.py  -> timeline.json + audio.wav
"""
import json, wave
import numpy as np

SR = 44100
UNIT = 0.32          # duree d'une croche (s) : meme cadence que l'original
T0 = 1.2             # premier impact (apres l'arrivee sur le rail)
OUTRO = 1.4          # sortie sur le rail apres la derniere note

# (note, duree en croches) - transpose une octave au-dessus pour un timbre brillant
MELODY = [
    ("B4",1),("C#5",1),("D5",1),("E5",1),("F#5",1),("D5",1),("F#5",2),
    ("F5",1),("C#5",1),("F5",2),
    ("E5",1),("C5",1),("E5",2),
    ("B4",1),("C#5",1),("D5",1),("E5",1),("F#5",1),("D5",1),("F#5",1),
    ("B5",1),("A5",1),("F#5",1),("D5",1),("F#5",1),("A5",4),
]
NAMES = {"C":0,"C#":1,"D":2,"D#":3,"E":4,"F":5,"F#":6,"G":7,"G#":8,"A":9,"A#":10,"B":11}

def freq(n):
    name, octv = n[:-1], int(n[-1])
    midi = 12 * (octv + 1) + NAMES[name]
    return 440.0 * 2 ** ((midi - 69) / 12)

# --- timeline ---
hits, t = [], T0
for n, d in MELODY:
    hits.append({"t": round(t, 4), "note": n, "dur": round(d * UNIT, 4)})
    t += d * UNIT
end = hits[-1]["t"] + hits[-1]["dur"] + OUTRO
json.dump({"hits": hits, "end": round(end, 3), "t0": T0}, open("timeline.json", "w"), indent=1)

# --- synthese marimba / verre ---
total = int((end + 0.6) * SR)
L = np.zeros(total); R = np.zeros(total)
rng = np.random.default_rng(7)

def strike(f, dur_ring=2.2):
    tt = np.arange(int(dur_ring * SR)) / SR
    att = np.minimum(1, tt / 0.002)
    s = (1.00 * np.sin(2*np.pi*f*tt) * np.exp(-tt/0.55)
         + 0.20 * np.sin(2*np.pi*2.0*f*tt) * np.exp(-tt/0.30)
         + 0.30 * np.sin(2*np.pi*3.93*f*tt) * np.exp(-tt/0.12)
         + 0.10 * np.sin(2*np.pi*9.9*f*tt) * np.exp(-tt/0.04))
    click = rng.normal(0, 1, len(tt)) * np.exp(-tt/0.004) * 0.15
    return (s + click) * att

for i, h in enumerate(hits):
    s = strike(freq(h["note"]))
    a = int(h["t"] * SR)
    pan = 0.5 + 0.25 * np.sin(i * 0.9)           # leger mouvement stereo
    n = min(len(s), total - a)
    L[a:a+n] += s[:n] * (1 - pan) * 1.2
    R[a:a+n] += s[:n] * pan * 1.2

# roulement de la bille sur le rail (intro + outro) : bruit filtre tres discret
def roll(t1, t2, gain=0.05):
    a, b = int(t1*SR), int(t2*SR)
    nz = rng.normal(0, 1, b - a)
    k = np.ones(40) / 40
    nz = np.convolve(nz, k, mode="same")
    env = np.sin(np.linspace(0, np.pi, b - a)) ** 0.5
    L[a:b] += nz * env * gain; R[a:b] += nz * env * gain
roll(0.0, T0 - 0.35)
roll(hits[-1]["t"] + hits[-1]["dur"], end)

# reverb : convolution avec une reponse impulsionnelle synthetique
ir_t = np.arange(int(1.8 * SR)) / SR
def ir():
    x = rng.normal(0, 1, len(ir_t)) * np.exp(-ir_t / 0.45)
    x[:int(0.012*SR)] = 0
    return x / np.sqrt((x**2).sum())
def conv(x, h):
    n = len(x) + len(h)
    N = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(h, N), N)[:len(x)]
L = L + 0.35 * conv(L, ir()); R = R + 0.35 * conv(R, ir())

m = max(np.abs(L).max(), np.abs(R).max())
st = (np.stack([L, R], 1) / m * 0.89 * 32767).astype(np.int16)
w = wave.open("audio.wav", "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(st.tobytes()); w.close()
print(f"{len(hits)} notes, fin {end:.2f}s")
