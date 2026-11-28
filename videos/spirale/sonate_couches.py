"""Exemple AUDIO : la Sonate au clair de lune qui se construit petit a petit (scenario « La melodie de la rue »).
L'enregistrement est separe en 3 voix par bandes de frequences complementaires (basse / triolets / melodie) :
leur somme redonne EXACTEMENT l'enregistrement. Chaque voix entre au moment ou il active les objets du scenario.
Usage : python3 sonate_couches.py <sonate.mp3>  -> sonate_construction.wav (60 s) + sonate_voix_*.wav
"""
import sys, subprocess, tempfile, os, wave, json
import numpy as np
SR = 48000; START, DUR = 2.6, 60.0                      # la 1re note tombe a ~0,5 s de la video
tmp = tempfile.mktemp(suffix=".wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(START), "-t", str(DUR + 1), "-i", sys.argv[1], "-ar", str(SR), "-ac", "2", tmp], check=True)
w = wave.open(tmp); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2).astype(np.float64) / 32768; os.remove(tmp)
n = int(DUR * SR); x = x[:n]

# --- separation en 3 voix (STFT, masques doux dont la somme vaut 1 -> reconstruction exacte)
N, HOPS = 8192, 2048; win = np.hanning(N + 1)[:-1]
fq = np.fft.rfftfreq(N, 1 / SR)
def soft(f, fc, oct_=0.18): return 1 / (1 + (f / fc) ** (1 / oct_ * 0.6))
F1, F2 = 165.0, 395.0                                    # entre C#3 et F#3 ; entre F#4 et G#4
m_bas = soft(fq, F1); m_haut = 1 - soft(fq, F2); m_mid = 1 - m_bas - m_haut
MASKS = {"basse": m_bas, "triolets": np.clip(m_mid, 0, 1), "melodie": m_haut}
def split(sig):
    pad = np.pad(sig, (N, N)); out = {k: np.zeros(len(pad)) for k in MASKS}; norm = np.zeros(len(pad))
    for a in range(0, len(pad) - N, HOPS):
        Xf = np.fft.rfft(pad[a:a + N] * win)
        for k, m in MASKS.items(): out[k][a:a + N] += np.fft.irfft(Xf * m, N) * win
        norm[a:a + N] += win ** 2
    return {k: (v / np.maximum(norm, 1e-6))[N:N + len(sig)] for k, v in out.items()}
voix = {k: np.zeros((n, 2)) for k in MASKS}
for c in (0, 1):
    for k, v in split(x[:, c]).items(): voix[k][:, c] = v
err = np.abs(sum(voix.values()) - x).max(); print(f"reconstruction : erreur max {err:.5f} (somme des 3 voix = original)")

# --- entrees des voix selon le scenario (chaque activation ouvre un peu plus la voix)
t = np.arange(n) / SR
def marches(times, levels):                              # niveau qui monte par paliers doux a chaque activation
    g = np.zeros(n)
    for tt, lv in zip(times, levels): g = np.maximum(g, lv * np.clip((t - tt) / 0.25, 0, 1))
    return g
pas_paves = np.arange(8.0, 14.0, 0.94)                    # scene 2 : les paves -> premiers triolets, timides
pas_pieton = np.arange(18.0, 24.0, 0.94)                  # scene 4 : passage pieton -> accompagnement complet
g_tri = marches(list(pas_paves) + list(pas_pieton), [0.12 + 0.05 * i for i in range(len(pas_paves))] + [0.45 + 0.09 * i for i in range(len(pas_pieton))])
g_tri = np.minimum(g_tri, 1.0)
lamp = np.arange(24.0, 30.0, 1.4)                         # scene 5 : lampadaires + flaques -> la melodie
g_mel = np.minimum(marches(list(lamp), [0.35 + 0.17 * i for i in range(len(lamp))]), 1.0)
g_bas = np.ones(n)                                        # scene 1 : les plaques d'egout -> la basse (des le debut)
fin = np.clip((DUR - t) / 4.0, 0, 1)                      # scene 8 : tout s'eteint doucement
mix = voix["basse"] * g_bas[:, None] + voix["triolets"] * g_tri[:, None] + voix["melodie"] * g_mel[:, None]
mix *= fin[:, None]
def save(name, y):
    y = y / max(1e-9, np.abs(y).max()) * 0.95
    o = wave.open(name, "wb"); o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR); o.writeframes((y * 32767).astype(np.int16).tobytes()); o.close()
save("sonate_construction.wav", mix)
for k, v in voix.items(): save(f"sonate_voix_{k}.wav", v[:int(15 * SR)])
print("ok")
