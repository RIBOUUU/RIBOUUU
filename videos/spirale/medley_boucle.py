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
# ---------- chaque objet joue une NOTE de la melodie quand la bille le touche ----------
import librosa
def melodie(S, off=None, nb=None):
    """melodie (pyin, registre C4-C7) + basse (chroma grave) a chaque croche d'un passage du morceau"""
    off = S["D"] if off is None else off; nb = S["n"] if nb is None else nb
    d = nb * S["B"]; y, sr = librosa.load(S["f"], sr=22050, mono=True, offset=off, duration=d + 0.2)
    yh = librosa.effects.harmonic(y)
    f0, vo, _ = librosa.pyin(yh, fmin=260, fmax=2100, sr=sr, frame_length=2048, hop_length=256)
    tt = librosa.times_like(f0, sr=sr, hop_length=256)
    C = librosa.feature.chroma_cqt(y=yh, sr=sr, hop_length=256)
    Cb = np.abs(librosa.cqt(yh, sr=sr, hop_length=256, fmin=librosa.note_to_hz('C2'), n_bins=24))     # 2 octaves graves
    notes = []
    for j in range(2 * nb):
        t0 = j * S["B"] / 2; m = (tt >= t0) & (tt < t0 + S["B"] / 2)
        if not np.any(m): m = np.zeros_like(m); m[min(len(m) - 1, int(t0 * sr / 256))] = True
        fv = f0[m & vo]
        midi = int(round(np.median(librosa.hz_to_midi(fv)))) if len(fv) else 72 + int(np.argmax(C[:, m].mean(1)))
        while midi > 86: midi -= 12
        while midi < 64: midi += 12
        bass = 36 + int(np.argmax(Cb[:, m].mean(1))) % 12
        notes.append((midi, bass))
    return notes
MEL = [melodie(S) for S in SONGS]
print("melodies :", [[x[0] for x in m[:12]] for m in MEL])
sr_ = SR; rng = np.random.default_rng(1)
def env(n, att, dec): t = np.arange(n) / sr_; return np.minimum(1, t / att) * np.exp(-t / dec)
def marimba(f, d=1.2):     # bois (etageres)
    t = np.arange(int(d * sr_)) / sr_
    return (np.sin(2*np.pi*f*t)*np.exp(-t/0.45) + 0.25*np.sin(2*np.pi*3.93*f*t)*np.exp(-t/0.08) + 0.12*np.sin(2*np.pi*9.9*f*t)*np.exp(-t/0.02)) * np.minimum(1, t/0.002)
def cloche(f, d=2.0):      # cloche / vibraphone (cerceau, aimant)
    t = np.arange(int(d * sr_)) / sr_
    return (np.sin(2*np.pi*f*t)*np.exp(-t/1.0) + 0.4*np.sin(2*np.pi*2.76*f*t)*np.exp(-t/0.35) + 0.2*np.sin(2*np.pi*5.4*f*t)*np.exp(-t/0.12)) * np.minimum(1, t/0.002) * (1 + 0.15*np.sin(2*np.pi*5*t))
def porcelaine(f, d=1.4):  # « ding » de porcelaine (assiettes) + petit eclat
    t = np.arange(int(d * sr_)) / sr_
    return (np.sin(2*np.pi*2*f*t)*np.exp(-t/0.5) + 0.5*np.sin(2*np.pi*2*f*2.71*t)*np.exp(-t/0.2) + 0.3*np.sin(2*np.pi*2*f*5.2*t)*np.exp(-t/0.06)
            + rng.normal(0, 1, len(t))*np.exp(-t/0.015)*0.25) * np.minimum(1, t/0.001)
def pluck(f, d=1.0):       # corde pincee (trampoline)
    t = np.arange(int(d * sr_)) / sr_; s = sum(np.sin(2*np.pi*k*f*t)/k*np.exp(-t*(2.5+2.5*k)) for k in range(1, 10))
    return s * np.minimum(1, t/0.003) * (1 + 0.04*np.sin(2*np.pi*6*t))
def tom(f, d=0.9):         # tambour accorde (gant de boxe)
    t = np.arange(int(d * sr_)) / sr_; ff = f/2*(1 + 0.3*np.exp(-t/0.03))
    return (np.sin(2*np.pi*np.cumsum(ff)/sr_)*np.exp(-t/0.25) + 0.4*np.sin(2*np.pi*f*t)*np.exp(-t/0.3) + rng.normal(0, 1, len(t))*np.exp(-t/0.01)*0.3)
def flute(f, d=0.9):       # souffle doux (ventilateur)
    t = np.arange(int(d * sr_)) / sr_; e = np.minimum(1, t/0.03)*np.exp(-t/0.35)
    return (np.sin(2*np.pi*f*t) + 0.2*np.sin(4*np.pi*f*t) + rng.normal(0, 1, len(t))*0.05) * e
INSTR = {"normal": marimba, "ressort": pluck, "vrille": cloche, "verre": porcelaine, "bumper": tom, "aimant": cloche, "ventilo": flute}
def type_of(h):
    for d_, f_, ty in plan.get(h["sec"], []):
        if d_ <= h["i"] <= f_: return ty
    return "normal"
notes_bus = np.zeros((n, 2))
for h in hits:
    midi, bass = MEL[h["sec"]][h["i"]]; f = 440 * 2 ** ((midi - 69) / 12); ty = type_of(h)
    x = INSTR[ty](f); x = x / (np.abs(x).max() + 1e-9)
    xb = marimba(440 * 2 ** ((bass - 69) / 12), 1.0); xb = 0.45 * xb / (np.abs(xb).max() + 1e-9)       # la basse, jouee par le meme choc
    m_ = max(len(x), len(xb)); x = np.pad(x, (0, m_ - len(x))) + np.pad(xb, (0, m_ - len(xb)))
    a = int(round(h["t"] * SR)); idx = (np.arange(len(x)) + a) % n; pan = 0.5 + 0.3 * np.sin(h["i"] * 1.3)
    np.add.at(notes_bus[:, 0], idx, x * np.sqrt(1 - pan)); np.add.at(notes_bus[:, 1], idx, x * np.sqrt(pan))
for q, T_ in enumerate(tunnels):
    N = SONGS[(q + 1) % 3]; L = T_["exit"] - T_["rim"]; nb = TUNB
    mel = melodie(N, N["be"] - TUNB * N["B"], nb); step = N["B"] * k / 2
    for j, (midi, bass) in enumerate(mel):
        tj = T_["rim"] + j * step
        if tj >= T_["exit"] - 1e-3: break
        x = cloche(440 * 2 ** ((midi - 69) / 12), 1.2); x = (0.5 + 0.5 * j / len(mel)) * x / (np.abs(x).max() + 1e-9)   # de plus en plus fort
        a = int(round(tj * SR)); idx = (np.arange(len(x)) + a) % n
        np.add.at(notes_bus[:, 0], idx, x * 0.6); np.add.at(notes_bus[:, 1], idx, x * 0.6)
notes_bus /= np.abs(notes_bus).max() + 1e-9
loop = notes_bus.copy()                     # SEULS les objets font la musique (plus de morceau en fond)
# petite reverb pour lier les notes
ir = np.random.default_rng(2).normal(0, 1, int(1.2 * SR)) * np.exp(-np.arange(int(1.2 * SR)) / SR / 0.35); ir[:int(0.01 * SR)] = 0; ir /= np.sqrt((ir ** 2).sum())
for c in (0, 1):
    M = 1 << (2 * n).bit_length(); y_ = np.fft.irfft(np.fft.rfft(loop[:, c], M) * np.fft.rfft(ir, M), M)
    rv = y_[:n].copy(); rv[:len(y_) - n] += y_[n:2 * n][:n] if False else 0; loop[:, c] += 0.25 * rv
loop /= max(1.0, np.abs(loop).max() / 0.98)
loop = np.roll(loop, -int(round(OFF * SR)), axis=0)
w = wave.open("audio_medley.wav", "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((loop * 32767).astype(np.int16).tobytes()); w.close()
print(len(hits), "rebonds ; tunnels", [(round(x["rim"], 2), round(x["exit"], 2)) for x in tunnels], "; depart", OFF)
