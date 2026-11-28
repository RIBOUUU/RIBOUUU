import sys, os
sys.argv = ['x', 'none']
import friendzone as F
from friendzone import SH, E, C, character, YEL, WHITE, RED
c = C(SH.vbg('rose', floor=True))
c.glow(540, 1250, 520, 520, (255, 110, 170), 0.45)
c.text(540, 230, 'POURQUOI SE', 120, WHITE, stroke=12)
c.text(540, 380, 'FAIRE', 120, WHITE, stroke=12)
c.text(540, 545, 'FRIENDZONE', 150, YEL, stroke=12)
c.text(540, 700, "À L'ÉCOLE ?", 120, WHITE, stroke=12)
character(c, 290, SH.FLOOR, 2.1, dict(F.SON, mood='ko', look=(5, 0)), 1.0)
character(c, 800, SH.FLOOR, 2.05, dict(F.CRUSH, mood='happy2', arms=('down', 'wave'), look=(-5, 0)), 1.0)
E.bubble(c, "T'es comme un frère !", 700, 900, 1.0, 50, tail=1)
F.broken(c, 520, 1250, 90, 0.6)
im = E.finish(c.im, 1.0, 0.0)
im.save('out/miniature_friendzone.jpg', quality=92)
