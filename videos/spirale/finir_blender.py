"""Finition des images Blender : halo lumineux (bloom) puis montage MP4 avec le son.
Usage : python3 finir_blender.py <dossier_png> <audio.wav> <sortie.mp4>
"""
import sys, os, glob, subprocess, tempfile
import numpy as np
from PIL import Image, ImageFilter

src, audio, out = sys.argv[1:4]
tmp = tempfile.mkdtemp()
files = sorted(glob.glob(os.path.join(src, "*.png")))
for k, f in enumerate(files):
    im = Image.open(f).convert("RGB")
    if im.size != (1080, 1920): im = im.resize((1080, 1920), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32) / 255
    lum = a.max(axis=2, keepdims=True)
    bright = np.clip((lum - 0.55) / 0.45, 0, 1) * a            # seulement les zones tres lumineuses
    b = Image.fromarray((bright * 255).astype(np.uint8))
    glow = sum(np.asarray(b.filter(ImageFilter.GaussianBlur(r))).astype(np.float32) / 255 * w
               for r, w in ((8, 0.6), (24, 0.5), (60, 0.4)))
    res = 1 - (1 - a) * (1 - np.clip(glow, 0, 1))              # melange "ecran" : doux, sans bruler
    h, w_ = res.shape[:2]                                       # leger vignettage
    yy, xx = np.mgrid[0:h, 0:w_]
    v = 1 - 0.22 * (((xx - w_ / 2) / (w_ / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / 2
    res = res * v[..., None]
    Image.fromarray((np.clip(res, 0, 1) * 255).astype(np.uint8)).save(os.path.join(tmp, f"{k:04d}.png"))
dur = len(files) / 30
subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "30", "-i", os.path.join(tmp, "%04d.png"), "-i", audio,
                "-af", f"atrim=0:{dur},afade=t=out:st={max(0, dur - 0.4)}:d=0.4", "-c:v", "libx264", "-preset", "slow",
                "-crf", "16", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
print("ok", out, len(files), "images")
