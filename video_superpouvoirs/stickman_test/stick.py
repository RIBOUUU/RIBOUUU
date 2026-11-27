import math, random, subprocess, numpy as np, wave
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H,FPS,DUR=1920,1080,30,5.0; S=2  # supersample
N=int(FPS*DUR); GY=880
F='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def ease(t): t=max(0,min(1,t)); return t*t*(3-2*t)
def jit(seed,a=3):
    r=random.Random(seed); return lambda: r.uniform(-a,a)
def line(d,pts,w,col,j):
    pts=[(x+j(),y+j()) for x,y in pts]
    d.line([(x*S,y*S) for x,y in pts],fill=col,width=w*S,joint='curve')
    for x,y in (pts[0],pts[-1]): d.ellipse([(x-w/2)*S,(y-w/2)*S,(x+w/2)*S,(y+w/2)*S],fill=col)
def building(d,x,w,h,j):
    line(d,[(x,GY),(x,GY-h),(x+w,GY-h),(x+w,GY)],5,(40,40,40),j)
    for wy in range(int(GY-h+20),GY-30,40):
        for wx in range(int(x+15),int(x+w-25),35):
            d.rectangle([wx*S,wy*S,(wx+14)*S,(wy+20)*S],outline=(90,90,90),width=3*S)
for f in range(N):
    t=f/FPS; boil=f//3; j=jit(boil,2.2)
    shake=0
    if 3.3<t<3.7: shake=10*math.sin(t*90)
    if 4.0<t<4.5: shake=18*math.sin(t*70)*(4.5-t)*2
    im=Image.new('RGB',(W*S,H*S),(246,243,235)); d=ImageDraw.Draw(im)
    # paper grain lines
    # scene
    for bx,bw,bh in [(150,160,260),(340,120,200),(1420,180,300),(1630,140,220)]:
        building(d,bx+shake,bw,bh,j)
    line(d,[(0,GY),(W,GY)],6,(30,30,30),j)
    g=ease((t-1.4)/1.8)          # growth 0..1
    bend=ease((t-3.2)/0.6)       # knees
    fall=ease((t-3.9)/0.5)       # drop to knees
    h=190+g*560                  # body height
    cx=W/2+shake
    hip_y=GY-h*0.47*(1-0.45*fall)-0  # hips drop
    leg=h*0.47
    kx=leg*0.5*(0.15+0.6*bend)  # knees go outward
    knee_y=GY-leg*0.5*(1-0.5*fall)
    sh_y=hip_y-h*0.33; head_r=h*0.09; head_y=sh_y-head_r*1.15
    col=(15,15,15); w=int(7+g*9)
    # glow
    if 1.0<t<3.3:
        a=0.5+0.5*math.sin(t*14)
        glow=Image.new('L',(W*S,H*S),0); gd=ImageDraw.Draw(glow)
        gd.ellipse([(cx-h*0.35)*S,(head_y-head_r*2)*S,(cx+h*0.35)*S,GY*S],fill=int(150*a*min(1,(t-1)*3)))
        glow=glow.filter(ImageFilter.GaussianBlur(60*S))
        im.paste((90,170,255),(0,0),glow); d=ImageDraw.Draw(im)
    line(d,[(cx-h*0.12,GY),(cx-kx,knee_y),(cx,hip_y)],w,col,j)
    line(d,[(cx+h*0.12,GY),(cx+kx,knee_y),(cx,hip_y)],w,col,j)
    line(d,[(cx,hip_y),(cx,sh_y)],w,col,j)
    arm=h*0.3; up=1-bend
    line(d,[(cx,sh_y+h*0.03),(cx-arm*0.6,sh_y+arm*(0.2+0.5*bend)-arm*0.4*up),(cx-arm*0.9,sh_y-arm*0.5*up+arm*0.7*bend)],w,col,j)
    line(d,[(cx,sh_y+h*0.03),(cx+arm*0.6,sh_y+arm*(0.2+0.5*bend)-arm*0.4*up),(cx+arm*0.9,sh_y-arm*0.5*up+arm*0.7*bend)],w,col,j)
    r=head_r; hx,hy=cx+j(),head_y+j()
    d.ellipse([(hx-r)*S,(hy-r)*S,(hx+r)*S,(hy+r)*S],outline=col,width=w*S,fill=(246,243,235))
    # face: eyes
    ey=hy-r*0.1; es=max(3,r*0.12)
    if t>3.3:  # X eyes / shocked
        for sx in (-1,1):
            ex=hx+sx*r*0.38
            d.line([(ex-es)*S,(ey-es)*S,(ex+es)*S,(ey+es)*S],fill=col,width=int(w*0.6)*S)
            d.line([(ex-es)*S,(ey+es)*S,(ex+es)*S,(ey-es)*S],fill=col,width=int(w*0.6)*S)
        d.ellipse([(hx-r*0.18)*S,(hy+r*0.3)*S,(hx+r*0.18)*S,(hy+r*0.6)*S],outline=col,width=int(w*0.6)*S)
    else:
        for sx in (-1,1):
            ex=hx+sx*r*0.38; d.ellipse([(ex-es)*S,(ey-es)*S,(ex+es)*S,(ey+es)*S],fill=col)
        d.arc([(hx-r*0.4)*S,(hy+r*0.05)*S,(hx+r*0.4)*S,(hy+r*0.55)*S],20,160,fill=col,width=int(w*0.6)*S)
    # cracks on knees
    if t>3.35:
        rc=(220,30,30); 
        for sx in (-1,1):
            x0,y0=cx+sx*kx,knee_y
            pts=[(x0,y0)]
            rr=random.Random(sx+boil)
            for k in range(4): pts.append((pts[-1][0]+rr.uniform(-25,25),pts[-1][1]+rr.uniform(-30,30)))
            d.line([(x*S,y*S) for x,y in pts],fill=rc,width=5*S)
    # impact dust
    if t>4.0:
        p=ease((t-4.0)/0.8)
        for k in range(10):
            rr=random.Random(k); ang=rr.uniform(math.pi,2*math.pi); dist=p*rr.uniform(150,420)
            x=cx+math.cos(ang)*dist*1.6; y=GY+math.sin(ang)*dist*0.35; rad=(1-p*0.6)*rr.uniform(20,45)
            d.ellipse([(x-rad)*S,(y-rad)*S,(x+rad)*S,(y+rad)*S],outline=(120,110,100),width=4*S)
    im=im.resize((W,H),Image.LANCZOS); d=ImageDraw.Draw(im)
    # titles
    if t<2.6:
        a=min(1,t*3)
        f1=ImageFont.truetype(F,90); f2=ImageFont.truetype(F,64)
        d.text((W/2,90),'N° 5',font=f1,fill=(220,30,30),anchor='mm',stroke_width=4,stroke_fill=(246,243,235))
        d.text((W/2,180),'DEVENIR GÉANT',font=f2,fill=(15,15,15),anchor='mm')
    if 1.6<t<3.2:
        f3=ImageFont.truetype(F,72); d.text((W-330,420),'× 1 000',font=f3,fill=(220,30,30),anchor='mm')
        d.text((W-330,500),'de poids',font=ImageFont.truetype(F,44),fill=(15,15,15),anchor='mm')
    if t>3.35:
        sc=1+0.25*max(0,1-(t-3.35)*4)
        f4=ImageFont.truetype(F,int(130*sc)); d.text((300,380),'CRAC !',font=f4,fill=(220,30,30),anchor='mm',stroke_width=6,stroke_fill=(15,15,15))
    im.save(f'f_{f:04d}.png')
# audio
SR=44100; n=int(SR*DUR); a=np.zeros(n); tt=np.arange(n)/SR; rng=np.random.default_rng(1)
def put(sig,at): i=int(at*SR); a[i:i+len(sig)]+=sig[:n-i]
L=int(1.8*SR); x=np.arange(L)/SR
whoosh=np.sin(2*np.pi*(80+220*x/1.8)*x)*np.hanning(L)*0.25+np.convolve(rng.standard_normal(L),np.ones(40)/40,'same')*np.hanning(L)*0.8
put(whoosh,1.4)
c=int(0.25*SR); put(rng.standard_normal(c)*np.exp(-np.arange(c)/SR*30)*0.7,3.35)
c=int(0.18*SR); put(rng.standard_normal(c)*np.exp(-np.arange(c)/SR*35)*0.5,3.5)
b=int(1.2*SR); xb=np.arange(b)/SR; put(np.sin(2*np.pi*(45+40*np.exp(-xb*10))*xb)*np.exp(-xb*3)*0.9,4.0)
a=a/np.abs(a).max()*0.9
with wave.open('sfx.wav','w') as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((a*32767).astype(np.int16).tobytes())
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','30','-i','f_%04d.png','-i','sfx.wav','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-shortest','-movflags','+faststart','test_stickman_5s.mp4'],check=True)
print('ok')
