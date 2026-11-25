import sys, subprocess, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

AUDIO, OUT = sys.argv[1], sys.argv[2]
W, H, FPS, DUR, SR = 540, 960, 30, 15, 22050

# --- Audio: low-band (kick/808) energy per frame ---
pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", AUDIO, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                     capture_output=True).stdout
y = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
hop = SR // FPS
freqs = np.fft.rfftfreq(2048, 1 / SR)
band = (freqs > 30) & (freqs < 150)
low = np.array([np.abs(np.fft.rfft(np.pad(y[i*hop:i*hop+2048], (0, 2048)))[:1025][band]).sum()
                for i in range(len(y)//hop - 1)])
low /= low.max()
sec = low[:len(low)//FPS*FPS].reshape(-1, FPS).mean(1)
start = max(0, int(np.argmax(sec > 0.6 * sec.max())) - 4)
env = low[start*FPS:(start+DUR)*FPS]; env = env / (env.max() + 1e-9)
kicks = [i for i in range(2, len(env)-2)
         if env[i] == env[i-2:i+3].max() and env[i] > 0.5 and env[i] > 1.25 * env[max(0, i-15):i].mean()]

# --- Poses (facing right, hip = origin, y down) ---
J = ["hip", "neck", "head", "fel", "fha", "bel", "bha", "fkn", "ffo", "bkn", "bfo"]
P = {
 "idle":  [(0,0),(0,-60),(0,-82),(18,-45),(30,-64),(-8,-42),(10,-60),(12,26),(20,56),(-12,26),(-22,56)],
 "punch": [(4,0),(12,-58),(16,-79),(38,-58),(66,-62),(-12,-40),(4,-56),(16,26),(28,56),(-16,26),(-30,56)],
 "kick":  [(0,0),(-12,-57),(-18,-78),(8,-48),(22,-62),(-26,-44),(-40,-28),(32,-8),(66,-30),(-4,28),(-8,56)],
 "hit":   [(-4,0),(-16,-55),(-28,-72),(-4,-48),(12,-36),(-26,-46),(-38,-58),(8,26),(16,56),(-14,26),(-26,56)],
 "ko":    [(0,52),(-60,52),(-80,49),(-45,44),(-30,50),(-50,57),(-36,57),(25,48),(56,52),(25,55),(56,56)],
 "win":   [(0,0),(0,-60),(0,-82),(16,-80),(22,-108),(-16,-80),(-22,-108),(12,26),(20,56),(-12,26),(-22,56)],
}
P = {k: np.array(v, float) for k, v in P.items()}
BONES = [("hip","neck"),("neck","fel"),("fel","fha"),("neck","bel"),("bel","bha"),
         ("hip","fkn"),("fkn","ffo"),("hip","bkn"),("bkn","bfo")]
JI = {n: i for i, n in enumerate(J)}

# --- Choreography from kicks ---
random.seed(7)
FINISH = max([k for k in kicks if k < (DUR-3.5)*FPS] or [int((DUR-3.5)*FPS)])
events = []  # (frame, attacker, move)
att, combo = 0, 0
for i, k in enumerate(kicks):
    if k > FINISH: break
    if k == FINISH:
        events.append((k, att, "kick", True)); break
    move = "kick" if combo == 2 else "punch"
    events.append((k, att, move, False))
    combo += 1
    if combo == 3: att, combo = 1 - att, 0
winner = events[-1][1] if events else 0

def strike_w(d):  # weight of strike pose at frame offset d from the hit
    if -3 <= d <= 0: return (d + 3) / 3
    if 0 < d <= 9: return max(0, 1 - d / 9)
    return 0.0

try:
    big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
except OSError:
    big = ImageFont.load_default()

GROUND, S = H * 0.66, 2.2
xs = [W/2 - 85, W/2 + 85]; vx = [0.0, 0.0]
COL = [(60, 220, 255), (255, 60, 90)]
ko_fly = None; shake = 0.0; sparks = []; flash = 0.0

ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                       "-r", str(FPS), "-i", "-", "-ss", str(start), "-t", str(DUR), "-i", AUDIO,
                       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-c:a", "aac", "-shortest", OUT],
                      stdin=subprocess.PIPE)

for f in range(DUR * FPS):
    e = env[f] if f < len(env) else 0
    poses = [P["idle"].copy(), P["idle"].copy()]
    lift = [0.0, 0.0]
    for (k, a, mv, fin) in events:
        d = f - k
        w = strike_w(d)
        if w > 0:
            poses[a] = poses[a] + (P[mv] - poses[a]) * w
            if d >= 0: poses[1-a] = poses[1-a] + (P["hit"] - poses[1-a]) * w
        if d == 0:  # impact
            vx[1-a] += (1 if a == 0 else -1) * (34 if fin else 14)
            shake, flash = (16 if fin else 7), (1.0 if fin else 0.5)
            hand = "ffo" if mv == "kick" else "fha"
            sgn = 1 if a == 0 else -1
            hx, hy = xs[a] + sgn * P[mv][JI[hand]][0] * S, GROUND - 56*S + P[mv][JI[hand]][1] * S
            for _ in range(28 if fin else 12):
                ang, sp = random.uniform(0, 2*math.pi), random.uniform(4, 16 if fin else 10)
                sparks.append([hx, hy, math.cos(ang)*sp, math.sin(ang)*sp, 1.0])
            if fin: ko_fly = [f, 1 - a]

    # movement: knockback then walk back to fighting distance
    for i in range(2):
        xs[i] += vx[i]; vx[i] *= 0.75
    if ko_fly is None:
        gap = xs[1] - xs[0]
        xs[0] += (gap - 170) * 0.06; xs[1] -= (gap - 170) * 0.06
        mid = (xs[0] + xs[1]) / 2; xs[0] += (W/2 - mid) * 0.05; xs[1] += (W/2 - mid) * 0.05
    else:
        lo = ko_fly[1]; t = f - ko_fly[0]
        if t < 14:
            lift[lo] = -4 * 60 * (t/14) * (1 - t/14) * S
            poses[lo] = P["hit"] + (P["ko"] - P["hit"]) * (t/14)
        else:
            poses[lo] = P["ko"]
        if t > 18:
            poses[1-lo] = P["idle"] + (P["win"] - P["idle"]) * min(1, (t-18)/8)
    for i in range(2): xs[i] = min(W - 150, max(150, xs[i]))

    bounce = 5 * e
    shake *= 0.8; flash *= 0.8
    sx, sy = random.uniform(-shake, shake), random.uniform(-shake, shake)

    bg = int(10 + 25 * flash)
    img = Image.new("RGB", (W, H), (bg, bg//2 + 4, bg + 8))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    d, gd = ImageDraw.Draw(img), ImageDraw.Draw(glow)
    gy = GROUND + 4 + sy
    d.line([(0, gy), (W, gy)], fill=(60, 50, 80), width=3)

    for i in range(2):
        sgn = 1 if i == 0 else -1
        hipy = GROUND - 56*S + 56*S + bounce + lift[i]
        pts = {n: (xs[i] + sgn * poses[i][JI[n]][0] * S + sx,
                   hipy - 56*S + poses[i][JI[n]][1] * S + sy + 0 * S) for n in J}
        # shift so feet touch ground in standing poses
        for dr in (gd, d):
            wdt = 14 if dr is gd else 7
            for a_, b_ in BONES:
                dr.line([pts[a_], pts[b_]], fill=COL[i], width=wdt)
            hx, hy = pts["head"]
            r = 15 * S / 2.2 * 1.2
            dr.ellipse([hx-r, hy-r, hx+r, hy+r], fill=COL[i])

    for s in sparks:
        s[0] += s[2]; s[1] += s[3]; s[3] += 0.6; s[4] -= 0.06
        if s[4] > 0:
            c = (255, int(200*s[4]+55), int(120*s[4]))
            gd.line([(s[0]+sx, s[1]+sy), (s[0]-s[2]+sx, s[1]-s[3]+sy)], fill=c, width=4)
            d.line([(s[0]+sx, s[1]+sy), (s[0]-s[2]+sx, s[1]-s[3]+sy)], fill=c, width=2)
    sparks = [s for s in sparks if s[4] > 0]

    arr = np.asarray(img, np.int16) + np.asarray(glow.filter(ImageFilter.GaussianBlur(14)), np.int16) * 0.8
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    if ko_fly and f - ko_fly[0] > 6:
        t = f - ko_fly[0] - 6
        sc = max(1.0, 2.2 - t * 0.15)
        txt = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
        ImageDraw.Draw(txt).text((W/2, 130), "K.O.", font=big, anchor="mm", fill=(255, 220, 60, 255),
                                 stroke_width=6, stroke_fill=(120, 0, 20, 255))
        txt = txt.resize((int(W*sc), int(260*sc)))
        img.paste(txt, (int(W/2 - W*sc/2), int(H*0.2 - 130*sc)), txt)
    ff.stdin.write(img.tobytes())

ff.stdin.close(); ff.wait()
print("start", start, "hits", len(events), "finish", FINISH)
