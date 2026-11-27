import json, os, glob, subprocess, random, math
import numpy as np, librosa, soundfile as sf, pyloudnorm as pyln
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from concurrent.futures import ThreadPoolExecutor

W, H, FPS, X, TAIL = 1920, 1080, 30, 0.6, 0.8
os.makedirs('build', exist_ok=True)
random.seed(7)

def font(size, bold=True):
    for p in ['/usr/share/fonts/truetype/noto/NotoSans-Black.ttf', '/usr/share/fonts/truetype/noto/NotoSans-ExtraBold.ttf',
              '/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf', '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf',
              '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf']:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

P = {0: [302, 346, 413], 1: [289, 347, 352, 387], 2: [241, 417, 334, 575], 3: [255, 269, 401, 530],
     4: [337, 439, 368, 378], 5: [210, 463, 313, 542], 6: [352, 291, 282, 257, 357]}
SHOTS = {0: [['A1', 'A2'], ['A3'], ['A4']],
         1: [['G1', 'G2'], ['G4'], ['G5', 'G6', 'G7'], ['G8']],
         2: [['V1', 'V2'], ['V3', 'V4'], ['V5'], ['V7', 'V8']],
         3: [['S1'], ['S2'], ['S4', 'S5'], ['S6', 'S7']],
         4: [['E2', 'E1'], ['E4'], ['E5', 'E6'], ['E7']],
         5: [['T1'], ['T3', 'T4'], ['T5'], ['T7', 'T8']],
         6: [['F1', 'F2'], ['F3'], ['F5'], ['F6'], ['F7']]}
TITLES = {1: ('N° 5', 'DEVENIR GÉANT'), 2: ('N° 4', 'VOLER'), 3: ('N° 3', 'LA SUPER-VITESSE'),
          4: ('N° 2', "CONTRÔLER L'ÉLECTRICITÉ"), 5: ('N° 1', 'LA TÉLÉPORTATION'), 6: ('', 'LE PIÈGE PARIS → LYON')}

# ---------- timing ----------
def analyse(s):
    y, sr = librosa.load(f'aud/a{s}.mp3', sr=22050)
    dur = len(y) / sr; hop = 256
    rms = librosa.feature.rms(y=y, frame_length=1024, hop_length=hop)[0]
    thr = max(np.percentile(rms, 15) * 1.5, rms.max() * 0.02)
    sil = rms < thr; gaps = []; i = 0; n = len(sil)
    while i < n:
        if sil[i]:
            j = i
            while j < n and sil[j]: j += 1
            a, b = i * hop / sr, j * hop / sr
            if b - a > 0.25 and a > 0.5 and b < dur - 0.3: gaps.append((a, b))
            i = j
        else: i += 1
    L = P[s]; cum = np.cumsum(L)[:-1] / sum(L) * dur; bounds = []
    for c in cum:
        cand = [g for g in gaps if abs((g[0] + g[1]) / 2 - c) < dur * 0.12]
        if cand:
            g = max(cand, key=lambda g: (g[1] - g[0]) - 0.15 * abs((g[0] + g[1]) / 2 - c))
            bounds.append((g[0] + g[1]) / 2)
        else: bounds.append(float(c))
    return dur, bounds

timing = {}
for s in range(7):
    dur, b = analyse(s)
    nf = int(round((dur + TAIL) * FPS)); L = nf / FPS
    edges = [0.0] + b + [L]
    shots = []
    for p, imgs in enumerate(SHOTS[s]):
        a, e = edges[p], edges[p + 1]; k = len(imgs)
        for j, im in enumerate(imgs):
            shots.append([im, a + (e - a) * j / k, a + (e - a) * (j + 1) / k])
    # snap to frames
    fr = [int(round(x[1] * FPS)) for x in shots] + [nf]
    timing[s] = {'dur': dur, 'nf': nf, 'bounds': b, 'shots': [(shots[i][0], fr[i + 1] - fr[i]) for i in range(len(shots))]}
json.dump(timing, open('build/timing.json', 'w'), indent=1)

# ---------- overlays ----------
def title_png(s, num, txt):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    band = Image.new('L', (W, H), 0); bd = ImageDraw.Draw(band)
    for yy in range(H):
        a = max(0, 1 - abs(yy - 560) / 330); bd.line([(0, yy), (W, yy)], fill=int(170 * a ** 1.4))
    im.paste((0, 0, 0, 255), (0, 0), band)
    d = ImageDraw.Draw(im)
    if num:
        f1 = font(230); w = d.textlength(num, font=f1)
        d.text(((W - w) / 2, 300), num, font=f1, fill=(235, 40, 40, 255), stroke_width=6, stroke_fill=(0, 0, 0, 255))
        y2 = 600
    else:
        y2 = 480
    size = 110
    while True:
        f2 = font(size); w = d.textlength(txt, font=f2)
        if w < W - 160 or size < 50: break
        size -= 6
    d.text(((W - w) / 2, y2), txt, font=f2, fill=(255, 255, 255, 255), stroke_width=5, stroke_fill=(0, 0, 0, 255))
    d.rectangle([(W / 2 - 120, y2 + size + 40), (W / 2 + 120, y2 + size + 48)], fill=(235, 40, 40, 255))
    im.save(f'build/title{s}.png')

for s, (n, t) in TITLES.items(): title_png(s, n, t)

def cta_png():
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    grad = Image.new('L', (W, H), 0); gd = ImageDraw.Draw(grad)
    for yy in range(600, H): gd.line([(0, yy), (W, yy)], fill=int(200 * (yy - 600) / (H - 600)))
    im.paste((0, 0, 0, 255), (0, 0), grad)
    f = font(62); t = 'Quel pouvoir prendrais-tu quand même ?'
    d.text(((W - d.textlength(t, font=f)) / 2, 800), t, font=f, fill='white', stroke_width=3, stroke_fill='black')
    f = font(44); t = 'Dis-le en commentaire'
    d.text(((W - d.textlength(t, font=f)) / 2, 890), t, font=f, fill=(230, 230, 230, 255), stroke_width=2, stroke_fill='black')
    bx, by, bw, bh = W - 470, 70, 400, 110
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=22, fill=(220, 30, 30, 255))
    f = font(52); t = 'ABONNE-TOI'
    d.text((bx + (bw - d.textlength(t, font=f)) / 2, by + 20), t, font=f, fill='white')
    im.save('build/cta.png')
cta_png()

# ---------- video per section ----------
MOVES = ['in', 'out', 'lr', 'rl', 'in2', 'up']
def move_expr(kind, N):
    t = f'(on/{N})'
    if kind == 'in':  return f"1.0+0.12*{t}", '0.5', '0.5'
    if kind == 'in2': return f"1.04+0.14*{t}", '0.35', '0.45'
    if kind == 'out': return f"1.16-0.12*{t}", '0.5', '0.5'
    if kind == 'lr':  return '1.14', f'{t}', '0.5'
    if kind == 'rl':  return '1.14', f'(1-{t})', '0.5'
    if kind == 'up':  return '1.14', '0.5', f'(1-{t})'

def render_section(s):
    tm = timing[s]; shots = tm['shots']; n = len(shots)
    args = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error']
    fl = []; lens = []
    for i, (im, f) in enumerate(shots):
        d = f / FPS; Lc = d + (X if i < n - 1 else 0); N = int(round(Lc * FPS)); lens.append(d)
        args += ['-i', f'img/{im}.jpg']
        z, px, py = move_expr(MOVES[(s * 3 + i) % len(MOVES)], N)
        fl.append(f"[{i}:v]scale=5120:2880:flags=lanczos,zoompan=z='{z}':x='(iw-iw/zoom)*{px}':y='(ih-ih/zoom)*{py}'"
                  f":d={N}:s={W}x{H}:fps={FPS},setsar=1,format=yuv420p,trim=end_frame={N},setpts=PTS-STARTPTS[v{i}]")
    cur = 'v0'; acc = 0.0
    for i in range(1, n):
        acc += lens[i - 1]
        fl.append(f"[{cur}][v{i}]xfade=transition=fade:duration={X}:offset={acc:.3f}[x{i}]"); cur = f'x{i}'
    k = n
    if s in TITLES:
        args += ['-loop', '1', '-t', '4.6', '-i', f'build/title{s}.png']
        fl.append(f"[{k}:v]format=rgba,fade=in:st=0.15:d=0.45:alpha=1,fade=out:st=3.8:d=0.7:alpha=1[t]")
        fl.append(f"[{cur}][t]overlay=0:0:eof_action=pass[o]"); cur = 'o'; k += 1
    if s == 6:
        st = tm['bounds'][3] + 1.0; ln = tm['nf'] / FPS - st
        args += ['-loop', '1', '-t', f'{tm["nf"] / FPS:.3f}', '-i', 'build/cta.png']
        fl.append(f"[{k}:v]format=rgba,fade=in:st={st:.2f}:d=0.8:alpha=1[c]")
        fl.append(f"[{cur}][c]overlay=0:0:eof_action=pass[o2]"); cur = 'o2'; k += 1
    fl.append(f"[{cur}]eq=contrast=1.06:saturation=1.08,vignette=PI/5,format=yuv420p,trim=end_frame={tm['nf']}[out]")
    args += ['-filter_complex', ';'.join(fl), '-map', '[out]', '-r', str(FPS), '-c:v', 'libx264', '-preset', 'fast',
             '-crf', '19', '-pix_fmt', 'yuv420p', f'build/sec{s}.mp4']
    r = subprocess.run(args, capture_output=True, text=True)
    return s, r.returncode, r.stderr[-1500:]

with ThreadPoolExecutor(4) as ex:
    for s, rc, err in ex.map(render_section, range(7)):
        print('section', s, 'rc', rc, err)

# ---------- audio ----------
SR = 44100
voice = []; starts = []; t0 = 0
for s in range(7):
    y, _ = librosa.load(f'aud/a{s}.mp3', sr=SR, mono=True)
    total = int(round(timing[s]['nf'] / FPS * SR))
    seg = np.zeros(total, dtype=np.float32); seg[:min(len(y), total)] = y[:total]
    starts.append(t0); t0 += total; voice.append(seg)
voice = np.concatenate(voice); N = len(voice)
meter = pyln.Meter(SR)
voice = pyln.normalize.loudness(voice, meter.integrated_loudness(voice), -16.0)

t = np.arange(N) / SR
rng = np.random.default_rng(3)
drone = np.zeros(N)
for f0, a, lfo in [(55, 1.0, 0.05), (82.41, 0.6, 0.07), (110, 0.45, 0.03), (164.81, 0.25, 0.09), (220, 0.12, 0.11)]:
    drone += a * (0.6 + 0.4 * np.sin(2 * np.pi * lfo * t + rng.uniform(0, 6))) * np.sin(2 * np.pi * f0 * t + 0.3 * np.sin(2 * np.pi * 0.2 * t))
noise = rng.standard_normal(N)
alpha = 0.02; lp = np.zeros(N); acc = 0.0
# simple one-pole lowpass via cumulative filter (vectorised approx)
from scipy.signal import lfilter
lp = lfilter([alpha], [1, alpha - 1], noise)
drone += 0.8 * lp / (np.abs(lp).max() + 1e-9)
env = np.minimum(1, t / 4) * np.minimum(1, (t[-1] - t) / 5)
music = (drone * env).astype(np.float32)
music = pyln.normalize.loudness(music, meter.integrated_loudness(music), -33.0)

sfx = np.zeros(N, dtype=np.float32)
def add(sig, at):
    i = int(at * SR); j = min(N, i + len(sig))
    if i < N and j > i: sfx[i:j] += sig[:j - i]
tt = np.arange(int(1.6 * SR)) / SR
boom = (np.sin(2 * np.pi * (48 + 30 * np.exp(-tt * 8)) * tt) * np.exp(-tt * 3.2)).astype(np.float32)
wl = int(0.9 * SR); wn = rng.standard_normal(wl)
whoosh = lfilter([0.08], [1, -0.92], wn) * np.hanning(wl) ** 1.5
whoosh = (whoosh / np.abs(whoosh).max()).astype(np.float32)
for s in range(1, 7):
    at = starts[s] / SR
    add(0.35 * whoosh, max(0, at - 0.75)); add(0.55 * boom, at)
add(0.5 * boom, 0.0)
mix = voice + music + 0.5 * sfx
pk = np.abs(mix).max()
if pk > 0.95: mix = mix * 0.95 / pk
sf.write('build/mix.wav', mix, SR, subtype='PCM_16')

with open('build/list.txt', 'w') as f:
    for s in range(7): f.write(f"file 'sec{s}.mp4'\n")
out = os.environ.get('OUT', 'out'); os.makedirs(out, exist_ok=True)
r = subprocess.run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', 'build/list.txt',
                    '-i', 'build/mix.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                    '-shortest', '-movflags', '+faststart', f'{out}/super_pouvoirs_mortels.mp4'], capture_output=True, text=True)
print('mux', r.returncode, r.stderr[-800:])

# ---------- thumbnail ----------
im = Image.open('img/E2.jpg').convert('RGB').resize((1280, 720), Image.LANCZOS)
arr = np.asarray(im).astype(np.float32)
g = (0.35 + 0.65 * np.linspace(0, 1, 1280) ** 0.8)[None, :, None]
im = Image.fromarray(np.clip(arr * g, 0, 255).astype(np.uint8))
d = ImageDraw.Draw(im)
f1 = font(150); f2 = font(120)
d.text((60, 150), 'TU MEURS', font=f1, fill=(255, 255, 255), stroke_width=8, stroke_fill=(0, 0, 0))
d.text((60, 330), 'EN 10 S', font=f2, fill=(255, 210, 0), stroke_width=8, stroke_fill=(0, 0, 0))
d.rounded_rectangle([60, 520, 520, 600], radius=14, fill=(220, 30, 30))
d.text((85, 528), '5 SUPER-POUVOIRS', font=font(50), fill='white')
im.save(f'{out}/miniature.jpg', quality=92)
print('done')
