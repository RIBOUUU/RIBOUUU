"""Post-production YouTube : accroche (aperçu de la fin), textes d'accroche et d'appel à l'action,
encodage aux recommandations YouTube, miniatures.
Usage : python3 finaliser.py combat_base_1080p60.mp4
"""
import sys, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = sys.argv[1]
OUT = "COMBAT_FINAL_YouTube_1080x1920_60fps.mp4"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
TF, T_SSJ, DUR = 31.8, 28.5, 34.0          # instants clés de la finale (sortis du moteur)
T0, T1 = TF + 0.75, TF + 2.05               # aperçu : le rayon perce la garde et tout explose

# Réglages vidéo : H.264 High, progressif, 1080x1920, 60 i/s, débit élevé, BT.709, lecture rapide (faststart)
VENC = ["-c:v", "libx264", "-preset", "slow", "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", "60",
        "-crf", "16", "-maxrate", "30M", "-bufsize", "60M", "-g", "30", "-bf", "2", "-coder", "1",
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-movflags", "+faststart"]
AENC = ["-c:a", "aac", "-b:a", "384k", "-ar", "48000", "-ac", "2"]

def txt(text, y, size, start, end, color="white", border="black"):
    """Texte qui apparaît en fondu entre start et end (secondes)."""
    a = f"if(lt(t,{start}),0,if(lt(t,{start}+0.15),(t-{start})/0.15,if(lt(t,{end}-0.2),1,max(0,({end}-t)/0.2))))"
    return (f"drawtext=fontfile={FONT}:text='{text}':fontsize={size}:fontcolor={color}:borderw={size//12}:bordercolor={border}"
            f":x=(w-text_w)/2:y={y}:alpha='{a}'")

teaser_txt = txt("À LA FIN...", 300, 96, 0.0, T1 - T0 + 0.1, "white")
hook_txt = ",".join([txt("QUI VA GAGNER ?", 300, 104, 0.05, 2.4, "white")])
cta_txt = ",".join([txt("LA SUITE ?", 1340, 92, DUR - 2.0, DUR + 1, "white"),
                    txt("ABONNE-TOI ↓", 1460, 104, DUR - 1.8, DUR + 1, "#FFD84A")])

fc = (f"[0:v]trim={T0}:{T1},setpts=PTS-STARTPTS,{teaser_txt},"
      f"fade=t=out:st={T1 - T0 - 0.12}:d=0.12:color=white[tv];"
      f"[0:a]atrim={T0}:{T1},asetpts=PTS-STARTPTS,afade=t=out:st={T1 - T0 - 0.1}:d=0.1[ta];"
      f"[0:v]setpts=PTS-STARTPTS,fade=t=in:st=0:d=0.12:color=white,{hook_txt},{cta_txt}[mv];"
      f"[0:a]asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.05[ma];"
      f"[tv][ta][mv][ma]concat=n=2:v=1:a=1[v][a]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", BASE, "-filter_complex", fc, "-map", "[v]", "-map", "[a]", *VENC, *AENC, OUT], check=True)

# ---------- miniatures ----------
def grab(t, path):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", BASE, "-frames:v", "1", path], check=True)
    return Image.open(path).convert("RGB")
def title(img, lines, y0, size, colors):
    d = ImageDraw.Draw(img); f = ImageFont.truetype(FONT, size); y = y0
    for line, col in zip(lines, colors):
        d.text((img.width/2, y), line, font=f, anchor="mm", fill=col, stroke_width=size//10, stroke_fill=(0, 0, 0)); y += int(size*1.15)
    return img

ssj = grab(T_SSJ + 0.35, "_ssj.png"); beam = grab(TF + 0.5, "_beam.png")
title(ssj.copy(), ["IL SE TRANSFORME", "EN PLEIN COMBAT"], 330, 92, [(255, 255, 255), (255, 216, 74)]).save("miniature_verticale_1080x1920.jpg", quality=95)
wide = Image.new("RGB", (1280, 720))
bg = beam.resize((1280, int(1280*beam.height/beam.width))).crop((0, 600, 1280, 1320)).filter(ImageFilter.GaussianBlur(6))
wide.paste(bg, (0, 0))
fg = ssj.crop((0, 380, 1080, 1540)).resize((620, 666))
wide.paste(fg, (660, 54))
title(wide, ["LE COMBAT", "ULTIME"], 250, 120, [(255, 255, 255), (255, 216, 74)])
wide.save("miniature_1280x720.jpg", quality=95)
print("ok :", OUT)
