"""Timeline + audio pour la video 'spirale' (bille qui joue une melodie sur des blocs).

Usage : python3 build_audio.py [morceau]   -> timeline.json + audio.wav
Morceaux :
  grieg    : Grieg, 'Dans l'antre du roi de la montagne' (1876, domaine public)
  slapstick: compo originale, swing burlesque (dans l'esprit d'Oggy et les Cafards)
  heroine  : compo originale, pop heroique (dans l'esprit de Miraculous)
  lyoko    : compo originale, electro sombre (dans l'esprit de Code Lyoko)
  slapstick_boucle : le swing en boucle parfaite (20 s, la fin s'enchaine sur le debut)
  domino_valse : compo originale, valse mysterieuse au kalimba, en boucle (video domino.html)
Les trois dernieres sont des melodies ORIGINALES qui reprennent seulement un style
(tempo, gamme, rythme, instrument), pas les generiques eux-memes.

Notation : "E5" = une note ; "E5+E3" = plusieurs notes frappees ensemble (accord/basse).
Durees en croches ; chaque section = (transposition en demi-tons, duree d'une croche en s).
"""
import json, sys, wave
import numpy as np

SR = 48000         # 48 kHz : une boucle de 608 images = 950 paquets AAC de 1024 echantillons pile
T0 = 0.06            # premier impact quasi immediat : on entend le son des la 1re image
OUTRO = 1.6          # sortie sur le rail apres la derniere note

SONGS = {
    "grieg": dict(
        timbre="marimba", swing=False,
        theme=[("B4",1),("C#5",1),("D5",1),("E5",1),("F#5",1),("D5",1),("F#5",2),
               ("F5",1),("C#5",1),("F5",2),("E5",1),("C5",1),("E5",2),
               ("B4",1),("C#5",1),("D5",1),("E5",1),("F#5",1),("D5",1),("F#5",1),
               ("B5",1),("A5",1),("F#5",1),("D5",1),("F#5",1),("A5",2)],
        sections=[(0, 0.28), (0, 0.21)],
        finale=[("B5",1,0.17),("F#5",1,0.17),("D5",1,0.17),("B4",1,0.17),("F#4",2,0.20),("B4",5,0.30)],
    ),
    # Swing burlesque en re mineur : chromatismes, croches swinguees, basse qui marche.
    "slapstick": dict(
        timbre="xylo", swing=True,
        theme=[("D5+D3",1),("F5",1),("A5+A2",1),("G#5",1),("A5+D3",1),("F5",1),("D5+A2",2),
               ("C5+C3",1),("D5",1),("F5+G2",1),("E5",1),("F5+C3",1),("D5",1),("A4+G2",2),
               ("A#4+A#2",1),("D5",1),("G5+F2",1),("F#5",1),("G5+A#2",1),("A#5",1),("A5+F2",1),("G5",1),
               ("F5+A2",1),("E5",1),("D5+A2",1),("C#5",1),("D5+D3",4)],
        sections=[(0, 0.30), (0, 0.23)],
        finale=[("A5",1,0.15),("F5",1,0.15),("D5",1,0.15),("A4",1,0.15),("C#5",1,0.18),("D5+D3+A3",5,0.30)],
    ),
    # Version BOUCLE du swing : tempo constant, relance a la fin qui ramene au debut sans coupure.
    # 27 + 27 + 6 = 60 notes = 6 segments de 10 (les 6 styles font un tour complet).
    "slapstick_boucle": dict(
        timbre="xylo", swing=True, loop=True, loop_seconds=608 / 30,
        theme=None,   # reprend le theme de "slapstick" (voir plus bas)
        sections=[(0, 1), (0, 1)],
        finale=[("A4+A2",1,1),("C#5",1,1),("E5+A2",1,1),("G5",1,1),("F5+A2",1,1),("E5",1,1)],
    ),
    # Pop heroique en mi majeur : grands intervalles qui montent, syncopes, accords au debut des phrases.
    "heroine": dict(
        timbre="glock", swing=False,
        theme=[("E5+E3+B3",1),("G#5",1),("B5",2),("C#6+A3",1),("B5",1),("G#5",1),("E5",1),
               ("F#5+B2+F#3",1),("G#5",1),("A5",2),("G#5+B2",1),("F#5",1),("D#5",1),("B4",1),
               ("C#5+C#3+G#3",1),("E5",1),("A5",2),("G#5+A2",1),("E5",1),("F#5",1),("G#5",1),
               ("A5+A2+E3",1),("G#5",1),("F#5+B2",1),("D#5",1),("E5+E3+B3",4)],
        sections=[(0, 0.29), (0, 0.22)],
        finale=[("B5",1,0.15),("G#5",1,0.15),("E5",1,0.15),("B4",1,0.15),("D#5",1,0.18),("E5+E3+B3",5,0.30)],
    ),
    # Electro sombre en la mineur : arpeges continus de synthe, basse sur chaque mesure.
    # Valse mysterieuse en mi mineur (3/4), au kalimba : A A' B A + relance = 60 notes, en boucle.
    # Une basse sur le 1er temps de chaque mesure (6 croches).
    "domino_valse": dict(
        timbre="kalimba", swing=False, loop=True, loop_seconds=608 / 30,
        theme=[
            # A
            ("E5+E3",2),("G5",1),("B5",1),("E6+B2",2),("D#6",2),("B5",2),("F#5",2),
            ("G5+E3",2),("A5",1),("G5",1),("F#5+B2",2),("E5",4),("B4",2),
            # A'
            ("E5+E3",2),("G5",1),("B5",1),("E6+B2",2),("F#6",2),("E6",2),("B5",2),
            ("C6+C3",2),("B5",1),("A5",1),("F#5+D3",2),("G5",4),("B4",2),
            # B
            ("C6+A2",2),("B5",1),("A5",1),("E5",2),("A5+C3",2),("G5",2),("E5",2),
            ("F#5+B2",2),("E5",1),("D#5",1),("F#5",2),("B4+B2",6),
            # A
            ("E5+E3",2),("G5",1),("B5",1),("E6+B2",2),("D#6",2),("B5",2),("F#5",2),
            ("G5+E3",2),("A5",1),("G5",1),("F#5+B2",2),("E5",4),("B4",2),
            # relance (ramene au debut)
            ("B4+B2",2),("D#5",2),("F#5",2),("A5+B2",2),("G5",2),("F#5",2),
            ("E5+E3",2),("D#5",2),("B4+B2",8),
        ],
        sections=[(0, 1)],
        finale=[],
    ),
    "lyoko": dict(
        timbre="synth", swing=False,
        theme=[("A4+A2",1),("C5",1),("E5",1),("A5",1),("G5+A2",1),("E5",1),("C5",1),("E5",1),
               ("F4+F2",1),("A4",1),("C5",1),("F5",1),("E5+F2",1),("C5",1),("A4",1),("C5",1),
               ("G4+G2",1),("B4",1),("D5",1),("G5",1),("F5+G2",1),("D5",1),("B4",1),("D5",1),
               ("E5+E2",1),("G#5",1),("B5",1),("E6",1),("D6+E2",1),("B5",1),("G#5",2)],
        sections=[(0, 0.26), (0, 0.20)],
        finale=[("E6",1,0.14),("B5",1,0.14),("G#5",1,0.14),("E5",1,0.14),("B4",1,0.17),("A5+A2+E3",5,0.30)],
    ),
}

NAMES = {"C":0,"C#":1,"D":2,"D#":3,"E":4,"F":5,"F#":6,"G":7,"G#":8,"A":9,"A#":10,"B":11}
NOTE_NAMES = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
midi_of = lambda n: 12 * (int(n[-1]) + 1) + NAMES[n[:-1]]
name_of = lambda m: NOTE_NAMES[m % 12] + str(m // 12 - 1)
freq = lambda n: 440.0 * 2 ** ((midi_of(n) - 69) / 12)
transpose = lambda chord, tr: "+".join(name_of(midi_of(n) + tr) for n in chord.split("+"))

SONGS["slapstick_boucle"]["theme"] = SONGS["slapstick"]["theme"]
song_name = sys.argv[1] if len(sys.argv) > 1 else "grieg"
song = SONGS[song_name]
LOOP = song.get("loop", False)
if LOOP:
    T0 = 0.0                                   # la boucle commence pile sur une note

# --- sequence (note, duree en s), avec swing optionnel (croches longue-courte) ---
SEQ = []
for tr, unit in song["sections"]:
    pos = 0
    for n, d in song["theme"]:
        dd = d
        if song["swing"] and d == 1:
            dd = 1.3 if pos % 2 == 0 else 0.7
        SEQ.append((transpose(n, tr), dd * unit)); pos += d
pos = 0
for n, d, u in song["finale"]:
    dd = d
    if song["swing"] and d == 1:
        dd = 1.3 if pos % 2 == 0 else 0.7
    SEQ.append((n, dd * u)); pos += d
if LOOP:   # on cale la duree totale exactement sur loop_seconds (nombre entier d'images)
    k = song["loop_seconds"] / sum(d for _, d in SEQ)
    SEQ = [(n, d * k) for n, d in SEQ]

hits, t = [], T0
for n, d in SEQ:
    hits.append({"t": round(t, 4), "note": n, "dur": round(d, 4)})
    t += d
end = song["loop_seconds"] if LOOP else hits[-1]["t"] + hits[-1]["dur"] + OUTRO
# boucle : la video et le son demarrent entre la 5e et la 6e note (milieu de phrase, temps faible),
# pour que le raccord ne tombe ni sur une coupe ni sur le debut du theme
OFFSET = round((hits[4]["t"] + hits[5]["t"]) / 2, 4) if LOOP else 0.0
json.dump({"song": song_name, "loop": LOOP, "offset": OFFSET, "hits": hits, "end": round(end, 4), "t0": T0}, open("timeline.json", "w"), indent=1)

# --- synthese ---
total = int((end + (4.5 if LOOP else 0.6)) * SR)
L = np.zeros(total); Rch = np.zeros(total)
rng = np.random.default_rng(7)
sin = lambda f, tt: np.sin(2 * np.pi * f * tt)

def strike(f, timbre):
    tt = np.arange(int(2.4 * SR)) / SR
    att = np.minimum(1, tt / 0.002)
    if timbre == "marimba":
        s = (sin(f, tt) * np.exp(-tt/0.55) + 0.20 * sin(2*f, tt) * np.exp(-tt/0.30)
             + 0.30 * sin(3.93*f, tt) * np.exp(-tt/0.12) + 0.10 * sin(9.9*f, tt) * np.exp(-tt/0.04))
        click = 0.15
    elif timbre == "xylo":      # bois sec et brillant, tres percussif
        s = (sin(f, tt) * np.exp(-tt/0.22) + 0.45 * sin(3.0*f, tt) * np.exp(-tt/0.09)
             + 0.15 * sin(6.1*f, tt) * np.exp(-tt/0.03))
        click = 0.3
    elif timbre == "glock":     # cloche claire qui resonne longtemps
        s = (sin(f, tt) * np.exp(-tt/1.1) + 0.35 * sin(2.76*f, tt) * np.exp(-tt/0.5)
             + 0.2 * sin(5.4*f, tt) * np.exp(-tt/0.2) + 0.08 * sin(8.93*f, tt) * np.exp(-tt/0.08))
        click = 0.1
    elif timbre == "kalimba":   # lame metallique pincee + petit "clac" de domino
        s = (sin(f, tt) * np.exp(-tt/0.9) + 0.22 * sin(2.0*f, tt) * np.exp(-tt/0.35)
             + 0.18 * sin(5.9*f, tt) * np.exp(-tt/0.05))
        click = 0.45
    else:                       # synth : dent de scie filtree qui se ferme (pluck electro)
        s = np.zeros_like(tt)
        for k in range(1, 14):
            for det in (0.997, 1.003):
                s += sin(k * f * det, tt) / k * np.exp(-tt * (4 + 2.2 * k)) * 0.5
        s *= 0.9
        click = 0.05
    noise = rng.normal(0, 1, len(tt)) * np.exp(-tt/0.004) * click
    return (s + noise) * att

for i, h in enumerate(hits):
    a = int(h["t"] * SR)
    for j, n in enumerate(h["note"].split("+")):
        f = freq(n)
        gain = 1.2 if j == 0 else (0.75 if f < 200 else 0.5)    # melodie devant, basse/accord derriere
        s = strike(f, song["timbre"]) * gain
        pan = 0.5 + 0.25 * np.sin(i * 0.9) if j == 0 else 0.5
        k = min(len(s), total - a)
        L[a:a+k] += s[:k] * (1 - pan); Rch[a:a+k] += s[:k] * pan

def roll(t1, t2, gain=0.05):      # roulement de la bille sur le rail de sortie
    a, b = int(t1*SR), int(t2*SR)
    nz = np.convolve(rng.normal(0, 1, b - a), np.ones(40) / 40, mode="same")
    env = np.sin(np.linspace(0, np.pi, b - a)) ** 0.5
    L[a:b] += nz * env * gain; Rch[a:b] += nz * env * gain
if not LOOP:
    roll(hits[-1]["t"] + 0.45, end)

ir_t = np.arange(int(1.8 * SR)) / SR
def ir():
    x = rng.normal(0, 1, len(ir_t)) * np.exp(-ir_t / 0.45)
    x[:int(0.012*SR)] = 0
    return x / np.sqrt((x**2).sum())
def conv(x, h):
    n = len(x) + len(h); N = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(h, N), N)[:len(x)]
wet = 0.25 if song["timbre"] == "synth" else 0.35
L = L + wet * conv(L, ir()); Rch = Rch + wet * conv(Rch, ir())

if LOOP:   # boucle : la queue du son (resonance + reverb) se replie sur le debut
    n = int(round(end * SR))
    for ch in (L, Rch):
        tail = ch[n:].copy()
        ch[:len(tail)] += tail
    L, Rch = L[:n], Rch[:n]
    k0 = int(round(OFFSET * SR))
    L, Rch = np.roll(L, -k0), np.roll(Rch, -k0)
m = max(np.abs(L).max(), np.abs(Rch).max())
st = (np.stack([L, Rch], 1) / m * 0.89 * 32767).astype(np.int16)
w = wave.open("audio.wav", "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(st.tobytes()); w.close()
print(f"{song_name}: {len(hits)} notes, fin {end:.2f}s")
