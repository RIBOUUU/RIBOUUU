"""Montage final avec un MUR D'ECUSSONS en fond (images RGBA de Blender rendues avec fond transparent).

Le mur est une tuile verticale sans couture qui monte d'exactement une hauteur de tuile par boucle :
la video reste une boucle parfaite. Le mur s'eclaire au drop et pulse sur les temps.
Usage : python3 finir_fond.py <dossier_png> <timeline.json> <audio.wav> <dossier_ecussons> <sortie.mp4>
"""
import sys, os, glob, json, math, random, subprocess, tempfile
import numpy as np
from PIL import Image, ImageFilter

src, tlp, audio, pdir, out = sys.argv[1:6]
TL = json.load(open(tlp)); PER, OFF, EXIT = TL["period"], TL["offset"], TL["tunnel"]["exit"]
KICKS = [k for k in TL["kicks"] if k >= EXIT]
W, H = 1080, 1920
rnd = random.Random(3)

# --- mur en planches de bois sombre (tuile H x W, raccord vertical parfait)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
plank = 160
wall = np.zeros((H, W, 3), np.float32)
base = np.array([0.20, 0.11, 0.055])
row = (yy // plank).astype(int)
shade = np.array([0.85 + 0.3 * rnd.random() for _ in range(H // plank + 1)])[row]
grain = 0.5 + 0.5 * np.sin(xx / 9.0 + 3 * np.sin(yy / 37.0 + row * 1.7) + row * 2.3)
wall = base * (0.75 + 0.35 * grain)[..., None] * shade[..., None]
gap = (yy % plank) < 5
wall[gap] *= 0.35
img = Image.fromarray((np.clip(wall, 0, 1) * 255).astype(np.uint8)).convert("RGBA")

# --- ecussons : places au hasard sans trop se chevaucher, avec ombre portee, en raccord vertical
pats = [Image.open(f).convert("RGBA") for f in sorted(glob.glob(os.path.join(pdir, "*.png")))]
placed = []
order = list(range(len(pats))) * 2; rnd.shuffle(order)
for idx in order:
    p = pats[idx]; sc_ = rnd.uniform(1.25, 1.7)
    p = p.resize((int(p.width * sc_), int(p.height * sc_)), Image.LANCZOS).rotate(rnd.uniform(-18, 18), expand=True, resample=Image.BICUBIC)
    for _ in range(200):
        x = rnd.randint(-40, W - p.width + 40); y = rnd.randint(0, H - 1)
        c = (x + p.width / 2, y + p.height / 2); rr = 0.36 * (p.width + p.height) / 2
        ok = all(min(abs(c[1] - q[1]), H - abs(c[1] - q[1])) ** 2 + (c[0] - q[0]) ** 2 > (rr + q[2]) ** 2 for q in placed)
        if ok: break
    else: continue
    placed.append((c[0], c[1], rr))
    sh = Image.new("RGBA", p.size, (0, 0, 0, 0)); sh.putalpha(p.getchannel("A").point(lambda v: int(v * 0.6)))
    sh = sh.filter(ImageFilter.GaussianBlur(10))
    for dy in (-H, 0, H):                                   # copie en haut/bas : tuile sans couture
        tmpc = Image.new("RGBA", (W, H), (0, 0, 0, 0)); tmpc.paste(sh, (x + 12, y + dy + 16), sh); img = Image.alpha_composite(img, tmpc)
        tmpc = Image.new("RGBA", (W, H), (0, 0, 0, 0)); tmpc.paste(p, (x, y + dy), p); img = Image.alpha_composite(img, tmpc)
wall = np.asarray(img.convert("RGB").filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32) / 255
wall = np.concatenate([wall, wall], axis=0)                 # pour le defilement
Image.fromarray((wall[:H] * 255).astype(np.uint8)).save(os.path.join(os.path.dirname(out) or ".", "mur_apercu.jpg"))

def light(tl):                                              # eclairage du mur : s'eclaire au drop, pulse sur les temps
    v = 0.32
    s = (tl - EXIT) % PER
    v += 0.35 * math.exp(-s / 0.6)
    for k in KICKS:
        d = (tl - k) % PER
        if d < 0.5: v += 0.10 * math.exp(-d / 0.12)
    return v

tmp = tempfile.mkdtemp()
files = sorted(glob.glob(os.path.join(src, "*.png"))); NV = len(files)
yv, xv = np.mgrid[0:H, 0:W]
vig = (1 - 0.30 * (((xv - W / 2) / (W / 2)) ** 2 + ((yv - H / 2) / (H / 2)) ** 2) / 2)[..., None]
for f, path in enumerate(files):
    fg = Image.open(path).convert("RGBA")
    if fg.size != (W, H): fg = fg.resize((W, H), Image.LANCZOS)
    a = np.asarray(fg).astype(np.float32) / 255; rgb, al = a[..., :3], a[..., 3:]
    tl = (OFF + f / 30) % PER
    off = int(round(H * f / NV)) % H                      # le mur monte d'une tuile par boucle
    bgw = wall[H - off: 2 * H - off] if off else wall[:H]
    comp = rgb * al + bgw * light(tl) * (1 - al)
    # halo (bloom) calcule sur le premier plan seulement
    lum = (rgb * al).max(axis=2, keepdims=True)
    bright = np.clip((lum - 0.55) / 0.45, 0, 1) * rgb * al
    b = Image.fromarray((bright * 255).astype(np.uint8))
    glow = sum(np.asarray(b.filter(ImageFilter.GaussianBlur(r))).astype(np.float32) / 255 * w for r, w in ((8, 0.6), (24, 0.5), (60, 0.4)))
    res = 1 - (1 - comp) * (1 - np.clip(glow, 0, 1))
    Image.fromarray((np.clip(res * vig, 0, 1) * 255).astype(np.uint8)).save(os.path.join(tmp, f"{f:04d}.png"))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "30", "-i", os.path.join(tmp, "%04d.png"), "-i", audio,
                "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                "-shortest", "-movflags", "+faststart", out], check=True)
print("ok", out, NV, "images")
