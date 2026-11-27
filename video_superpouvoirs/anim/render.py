import sys, os, subprocess, math
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFilter
from engine import *
import scenes as SC

OUT = os.path.join(SC.HERE, 'out'); os.makedirs(OUT, exist_ok=True)


def frame_image(f):
    sec, T, fn, t0, t1 = SC.scene_at(f)
    c = C(bg(SC.BGS.get(fn, 'plain')))
    fn(c, T, T - t0)
    u = (T - t0) / max(0.01, t1 - t0)
    zoom = 1.0 + 0.035 * u
    edge = min(T - t0, t1 - T)
    dark = max(0.0, 1 - edge / 0.12) * 0.8
    if T < 0.13 and sec > 0: dark = max(dark, 0.9 * (1 - T / 0.13))
    im = finish(c.im, zoom, dark)
    if fn in SC.BLUR:
        b = SC.BLUR[fn](T)
        if b > 0.3: im = im.filter(ImageFilter.GaussianBlur(b))
    if sec == 6 and T > SC.NF[6] / FPS - 1.2:
        im = Image.blend(im, Image.new('RGB', im.size, (0, 0, 0)), min(1, (T - (SC.NF[6] / FPS - 1.2)) / 1.0))
    tg = f / FPS
    d = ImageDraw.Draw(im)
    for st, en, ch in SC.CAPS:
        if st <= tg < en:
            caption(d, ch, tg); break
    return im


def render_range(args):
    a, b, path = args
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                          '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p', '-tune', 'animation', path],
                         stdin=subprocess.PIPE)
    for f in range(a, b):
        p.stdin.write(frame_image(f).tobytes())
        if f % 300 == 0: print(path, f, flush=True)
    p.stdin.close(); p.wait()
    return path


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'sheet':
        frames = [int(v) for v in sys.argv[2].split(',')]
        ims = [frame_image(f).resize((640, 360)) for f in frames]
        cols = 3; rows = (len(ims) + cols - 1) // cols
        sheet = Image.new('RGB', (640 * cols, 360 * rows))
        for i, im in enumerate(ims): sheet.paste(im, ((i % cols) * 640, (i // cols) * 360))
        sheet.save(sys.argv[3])
    elif mode == 'full':
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 4
        a0 = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        b0 = int(sys.argv[4]) if len(sys.argv) > 4 else SC.TOTAL
        step = math.ceil((b0 - a0) / n)
        jobs = [(a0 + i * step, min(b0, a0 + (i + 1) * step), os.path.join(OUT, f'part_{a0 + i * step:05d}.mp4')) for i in range(n)]
        with Pool(n) as pool:
            for r in pool.imap_unordered(render_range, jobs): print('done', r, flush=True)
