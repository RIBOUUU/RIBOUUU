import sys, subprocess, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

AUDIO, OUT = sys.argv[1], sys.argv[2]
W, H, FPS, DUR = 540, 960, 30, 15
SR = 22050

# --- Audio analysis: low-band (kick/808) energy per video frame ---
pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", AUDIO, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                     capture_output=True).stdout
y = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
hop = SR // FPS
n = len(y) // hop
freqs = np.fft.rfftfreq(2048, 1 / SR)
band = (freqs > 30) & (freqs < 150)
low = np.array([np.abs(np.fft.rfft(np.pad(y[i*hop:i*hop+2048], (0, 2048)))[:1025][band]).sum()
                for i in range(n - 1)])
low /= low.max()
sec = low[:len(low)//FPS*FPS].reshape(-1, FPS).mean(1)
start = max(0, int(np.argmax(sec > 0.6 * sec.max())) - 4)   # 4 s before the beat gets heavy
env = low[start*FPS:(start+DUR)*FPS]
env = env / (env.max() + 1e-9)
# kick = local peak above rolling mean
kicks = [i for i in range(2, len(env)-2)
         if env[i] == env[i-2:i+3].max() and env[i] > 0.55 and env[i] > 1.3 * env[max(0,i-15):i].mean()]

# --- Heart geometry ---
cx, cy, S = W/2, H*0.45, 11
ts = np.linspace(0, 2*np.pi, 240, endpoint=False)
hx = 16*np.sin(ts)**3
hy = -(13*np.cos(ts) - 5*np.cos(2*ts) - 2*np.cos(3*ts) - np.cos(4*ts))
K = 24
random.seed(3)
wedges = []
for k in range(K):
    idx = list(range(k*10, k*10+11))
    pts = [(hx[i % 240], hy[i % 240]) for i in idx]
    mx = np.mean([p[0] for p in pts]); my = np.mean([p[1] for p in pts])
    wedges.append(dict(pts=pts, dir=(mx, my), vx=mx*0.15+random.uniform(-1, 1),
                       vy=my*0.1-random.uniform(2, 5), rot=random.uniform(-6, 6)))
crack_order = random.sample(range(K), K)

try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 34)
except OSError:
    font = ImageFont.load_default()

SHATTER = (DUR - 2.5) * FPS
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                       "-r", str(FPS), "-i", "-", "-ss", str(start), "-t", str(DUR), "-i", AUDIO,
                       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-c:a", "aac", "-shortest", OUT],
                      stdin=subprocess.PIPE)

pulse, ncracks = 0.0, 0
for f in range(DUR*FPS):
    e = env[f] if f < len(env) else 0
    if f in kicks:
        pulse = 1.0
        ncracks = min(K, ncracks + 1)
    pulse *= 0.82
    scale = S * (1 + 0.12*pulse)

    img = Image.new("RGB", (W, H), (8, 4, 10))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gd, d = ImageDraw.Draw(glow), ImageDraw.Draw(img)
    t_sh = max(0, f - SHATTER)

    for k, wd in enumerate(wedges):
        ox = wd["vx"]*t_sh*0.6
        oy = wd["vy"]*t_sh*0.6 + 0.5*0.9*t_sh**2 * 0.6
        a = math.radians(wd["rot"]*t_sh*0.5)
        poly = [(0.0, 0.0)] + wd["pts"]
        pts = []
        for px, py in poly:
            rx = px*math.cos(a) - py*math.sin(a); ry = px*math.sin(a) + py*math.cos(a)
            pts.append((cx + rx*scale + ox, cy + ry*scale + oy))
        r = int(170 + 85*pulse)
        fade = max(0, 1 - t_sh/60)
        col = (int(r*fade), int(10*fade), int(30*fade))
        gd.polygon(pts, fill=col)
        d.polygon(pts, fill=col)

    # cracks: wedge borders revealed one per kick, white-hot
    for j in range(ncracks if t_sh == 0 else 0):
        k = crack_order[j]
        px, py = wedges[k]["pts"][0]
        steps = 6
        prev = (cx, cy)
        random.seed(k)
        for s in range(1, steps+1):
            q = (cx + px*scale*s/steps + random.uniform(-6, 6), cy + py*scale*s/steps + random.uniform(-6, 6))
            d.line([prev, q], fill=(255, 230, 235), width=2)
            prev = q

    img = Image.blend(img, Image.composite(glow.filter(ImageFilter.GaussianBlur(28)), img,
                                           Image.new("L", (W, H), 255)), 0.0)
    img = Image.fromarray(np.clip(np.asarray(img, np.int16) +
                                  np.asarray(glow.filter(ImageFilter.GaussianBlur(30)), np.int16)*0.9, 0, 255).astype(np.uint8))

    # audio bar at bottom
    bw = int(W*0.6*e)
    ImageDraw.Draw(img).rectangle([W/2-bw/2, H-120, W/2+bw/2, H-116], fill=(200, 40, 70))
    txt = "elle est partie." if f > SHATTER + 15 else ""
    if txt:
        al = min(1, (f - SHATTER - 15)/20)
        ImageDraw.Draw(img).text((W/2, H*0.78), txt, font=font, anchor="mm", fill=(int(230*al),)*3)
    ff.stdin.write(img.tobytes())

ff.stdin.close(); ff.wait()
print("start", start, "kicks", len(kicks))
