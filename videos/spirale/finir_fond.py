"""Montage final : MUR BLANC derriere la spirale (images RGBA de Blender, fond transparent) et, a certains
moments, UN seul ecusson qui surgit en grand (un de chaque personnage), cale sur les temps de la musique.
Au drop : le drapeau pirate en tres grand sur des rayons dores. Tout depend du temps de boucle -> boucle parfaite.

Usage : python3 finir_fond.py <dossier_png> <timeline.json> <audio.wav> <dossier_ecussons> <sortie.mp4> [apercu.jpg]
"""
import sys, os, glob, json, math, subprocess, tempfile
import numpy as np
from PIL import Image, ImageFilter

src, tlp, audio, pdir, out = sys.argv[1:6]
TL = json.load(open(tlp)); PER, OFF, EXIT = TL["period"], TL["offset"], TL["tunnel"]["exit"]
BEATS = TL["kicks"]
W, H = 1080, 1920

def P(i): return Image.open(os.path.join(pdir, f"p{i:02d}.png")).convert("RGBA")
jr = P(2); jr = jr.crop((jr.width // 2 - 10, 0, jr.width, jr.height))        # le drapeau (sans le chapeau)
near = lambda t: min(BEATS, key=lambda b: abs(b - t))
# (image, instant, position x, y du centre, hauteur en px, inclinaison)
SHOW = [(P(12), near(0.7), 0.30, 0.40, 1000, -6), (P(16), near(2.9), 0.70, 0.55, 1050, 5),
        (P(10), near(5.0), 0.28, 0.50, 1050, 4), (P(0), near(7.1), 0.72, 0.42, 1000, -5),
        (P(9), near(9.0), 0.50, 0.35, 780, 0), (jr, EXIT, 0.50, 0.45, 900, 0),
        (P(6), near(13.6), 0.30, 0.52, 1000, 6), (P(14), near(15.6), 0.70, 0.48, 1080, -4)]
HOLD = {id(SHOW[5][0]): 2.0}

# --- mur blanc legerement texture (enduit) + vignettage doux
rng = np.random.default_rng(2)
nz = Image.fromarray((rng.random((H // 4, W // 4)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(6))
nz = np.asarray(nz).astype(np.float32) / 255
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
v = 1 - 0.28 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 2
wall = np.stack([0.95, 0.94, 0.91])[None, None, :] * (0.96 + 0.06 * nz)[..., None] * v[..., None]
ang = np.arctan2(yy - H * 0.45, xx - W / 2)

def ease_pop(u):        # surgit avec un petit rebond
    if u < 0: return 0.0
    if u < 0.22: x = u / 0.22; return 1.12 * (1 - (1 - x) ** 3)
    if u < 0.36: x = (u - 0.22) / 0.14; return 1.12 - 0.12 * x
    return 1.0

cache = {}
def scaled(img, h, rot):
    key = (id(img), h, round(rot, 1))
    if key not in cache:
        k = h / img.height; im = img.resize((max(1, int(img.width * k)), max(1, int(h))), Image.LANCZOS)
        im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sh.putalpha(im.getchannel("A").point(lambda a: int(a * 0.35)))
        cache[key] = (im, sh.filter(ImageFilter.GaussianBlur(14)))
        if len(cache) > 400: cache.pop(next(iter(cache)))
    return cache[key]

def background(tl):
    img = Image.fromarray((np.clip(wall, 0, 1) * 255).astype(np.uint8)).convert("RGBA")
    # rayons dores au drop
    s = (tl - EXIT) % PER
    if s < 2.4:
        a = min(1, s / 0.12) * (1 - max(0, s - 1.6) / 0.8)
        rays = (np.sin(14 * (ang + 0.35 * s)) > 0.25).astype(np.float32) * a * 0.55
        col = np.array([1.0, 0.78, 0.30])
        base = np.asarray(img).astype(np.float32)[..., :3] / 255
        base = base * (1 - rays[..., None]) + col * rays[..., None]
        img = Image.fromarray((base * 255).astype(np.uint8)).convert("RGBA")
    for p, t0, cx, cy, hh, rot in SHOW:
        hold = HOLD.get(id(p), 1.6); d = (tl - t0) % PER
        if d > hold + 0.35: continue
        u = d / hold
        sc = ease_pop(u) * (1 + 0.05 * u)
        alpha = 1.0 if d < hold else max(0.0, 1 - (d - hold) / 0.35)
        if sc <= 0.02 or alpha <= 0: continue
        im, sh = scaled(p, int(hh * sc / 4) * 4, rot + 3 * math.sin(d * 2))
        if alpha < 1:
            im = im.copy(); im.putalpha(im.getchannel("A").point(lambda q: int(q * alpha)))
            sh = sh.copy(); sh.putalpha(sh.getchannel("A").point(lambda q: int(q * alpha)))
        x = int(cx * W - im.width / 2); y = int(cy * H - im.height / 2)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); layer.paste(sh, (x + 18, y + 26), sh); layer.paste(im, (x, y), im)
        img = Image.alpha_composite(img, layer)
    return np.asarray(img.convert("RGB").filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255

# --- trainee lumineuse derriere la bille (positions exportees de Blender : EXPORT_BILLE)
TR = json.load(open(os.environ["TRAINEE"])) if os.environ.get("TRAINEE") else None
from PIL import ImageDraw
def trail_layer(fi):
    """trainee de petites billes : la bille seme des perles qui restent en place puis s'eteignent"""
    d = TR["frames"][fi]; M = np.array(d["cam"]); k = TR["lens"] / TR["sensor"] * H
    pts = np.array(d["past"]); n = len(pts); NF = len(TR["frames"])
    g0 = int(round((OFF * 30 + fi) * 2))                  # indice global des perles (60 par seconde)
    rgbI = Image.new("RGB", (W, H), (0, 0, 0)); aI = Image.new("L", (W, H), 0)
    dr, da = ImageDraw.Draw(rgbI), ImageDraw.Draw(aI)
    for j in range(n - 1, 1, -1):
        g = (g0 - j) % (NF * 2); rg = np.random.default_rng(g)
        if rg.random() < 0.25: continue                    # quelques trous : des perles, pas un trait
        off = (rg.random(3) - 0.5) * 0.45
        x, y, z = M[:3, :3] @ (pts[j] + off) + M[:3, 3]
        if z > -0.5: continue
        u = j / n; px = W / 2 + k * x / -z; py = H / 2 - k * y / -z
        r = k * TR["br"] / -z * (0.22 + 0.3 * rg.random()) * (1 - u) ** 0.5
        if r < 0.8: continue
        al = int(255 * min(1, (1 - u) * 1.4))
        col = np.array(TR["frames"][(fi - j // 2) % NF]["col"])          # couleur de la bille quand la perle est nee
        c1 = tuple(int(255 * min(1, v * 0.85 + 0.1)) for v in col); c2 = tuple(int(255 * min(1, v * 0.4 + 0.6)) for v in col)
        dr.ellipse((px - r, py - r, px + r, py + r), fill=c1); da.ellipse((px - r, py - r, px + r, py + r), fill=al)
        h = r * 0.45; dr.ellipse((px - r * 0.35 - h, py - r * 0.35 - h, px - r * 0.35 + h, py - r * 0.35 + h), fill=c2)
    rgb = np.asarray(rgbI.filter(ImageFilter.GaussianBlur(0.7))).astype(np.float32) / 255
    a = np.asarray(aI.filter(ImageFilter.GaussianBlur(0.7))).astype(np.float32)[..., None] / 255
    return rgb, a

files = sorted(glob.glob(os.path.join(src, "*.png")))
if len(sys.argv) > 6:            # apercu : quelques images seulement
    files = files[:]
tmp = tempfile.mkdtemp()
for f, path in enumerate(files):
    fi = int(os.path.basename(path)[:4])
    fg = Image.open(path).convert("RGBA")
    if fg.size != (W, H): fg = fg.resize((W, H), Image.LANCZOS)
    a = np.asarray(fg).astype(np.float32) / 255; rgb, al = a[..., :3], a[..., 3:]
    tl = (OFF + fi / 30) % PER
    bgi = background(tl)
    if TR is not None:
        trgb, ta = trail_layer(fi); bgi = bgi * (1 - ta) + trgb * ta
    comp = rgb * al + bgi * (1 - al)
    lum = (rgb * al).max(axis=2, keepdims=True)
    bright = np.clip((lum - 0.55) / 0.45, 0, 1) * rgb * al
    if TR is not None: bright = np.maximum(bright, trgb * ta * (1 - al) * 0.9)
    b = Image.fromarray((bright * 255).astype(np.uint8))
    glow = sum(np.asarray(b.filter(ImageFilter.GaussianBlur(r))).astype(np.float32) / 255 * w for r, w in ((8, 0.6), (24, 0.5), (60, 0.4)))
    res = 1 - (1 - comp) * (1 - np.clip(glow, 0, 1))
    Image.fromarray((np.clip(res, 0, 1) * 255).astype(np.uint8)).save(os.path.join(tmp, f"{f:04d}.png"))
if len(sys.argv) > 6:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(tmp, "%04d.png"), "-vf", f"scale=360:640,tile={len(files)}x1",
                    "-frames:v", "1", sys.argv[6]], check=True)
    sys.exit(0)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "30", "-i", os.path.join(tmp, "%04d.png"), "-i", audio,
                "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                "-shortest", "-movflags", "+faststart", out], check=True)
print("ok", out, len(files), "images")
