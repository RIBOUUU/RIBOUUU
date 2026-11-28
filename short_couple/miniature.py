import sys
import couple as K
from couple import SH, E, C, YEL, WHITE, RED
c = C(SH.vbg('purple'))
c.glow(540, 1300, 520, 420, (255, 110, 170), 0.35)
c.text(540, 230, 'POURQUOI', 130, WHITE, stroke=12)
c.text(540, 390, "T'ES NUL", 150, YEL, stroke=12)
c.text(540, 550, 'EN COUPLE ?', 130, WHITE, stroke=12)
K.in_bed(c, 1.0, dict(K.HIM, mood='happy', look=(2, 6), arms=('hold', 'hold')),
         dict(K.HER, mood='worry', look=(-7, 0)), gap=70, top=1450)
K.phone_small(c, 330, 1330, 0.9)
E.bubble(c, 'Il préfère son tel ?', 760, 760, 1.0, 50, tail=1)
im = E.finish(c.im, 1.0, 0.0)
im.save('out/miniature_couple.jpg', quality=92)
