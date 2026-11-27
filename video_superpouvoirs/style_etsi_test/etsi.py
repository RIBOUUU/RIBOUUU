import math, random, subprocess, wave, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H,FPS,DUR,S=1920,1080,30,5.0,2
N=int(FPS*DUR); GY=820
FK='/usr/share/fonts/opentype/inter/Inter-Black.otf'
HOOD=(232,108,52); HOOD_D=(190,80,38); YEL=(255,206,64); BLK=(14,14,18)
def ease(t): t=max(0,min(1,t)); return t*t*(3-2*t)
def back(t):
    t=max(0,min(1,t)); c=1.7; return 1+(c+1)*(t-1)**3+c*(t-1)**2
def P(p): return [(x*S,y*S) for x,y in p]
rng0=np.random.default_rng(0)

def base_bg():
    im=Image.new('RGB',(W*S,H*S)); d=ImageDraw.Draw(im)
    for y in range(H):
        if y<GY:
            k=y/GY; c=(int(22+14*k),int(58+22*k),int(76+18*k))
        else:
            k=(y-GY)/(H-GY); c=(int(70-25*k),int(48-18*k),int(38-14*k))
        d.line([(0,y*S),(W*S,y*S)],fill=c,width=S)
    # faint vertical light streaks
    for k in range(9):
        r=random.Random(k); x=r.uniform(0,W); w=r.uniform(30,90)
        ov=Image.new('L',(W*S,H*S),0); od=ImageDraw.Draw(ov); od.rectangle([x*S,0,(x+w)*S,GY*S],fill=18)
        im.paste((90,150,170),(0,0),ov.filter(ImageFilter.GaussianBlur(40*S)))
    d=ImageDraw.Draw(im)
    # buildings (muted flat vector)
    for i,(bx,bw,bh) in enumerate([(40,200,420),(270,150,300),(1450,220,470),(1700,170,330)]):
        col=(38,78,98) if i%2 else (44,88,110)
        d.rounded_rectangle([bx*S,(GY-bh)*S,(bx+bw)*S,GY*S],radius=10*S,fill=col)
        d.rectangle([bx*S,(GY-bh)*S,(bx+bw)*S,(GY-bh+14)*S],fill=(56,104,128))
        for wy in range(GY-bh+40,GY-40,60):
            for wx in range(bx+22,bx+bw-30,48):
                lit=random.Random(wx*7+wy).random()<0.45
                d.rounded_rectangle([wx*S,wy*S,(wx+24)*S,(wy+34)*S],radius=4*S,fill=(255,214,120) if lit else (30,60,76))
    # floor line glow
    d.rectangle([0,GY*S,W*S,(GY+6)*S],fill=(90,64,50))
    return im
BG=base_bg()
# vignette mask
yy,xx=np.mgrid[0:H,0:W]; vig=1-0.55*(((xx-W/2)/(W*0.62))**2+((yy-H*0.45)/(H*0.75))**2); vig=np.clip(vig,0.35,1)[...,None]

def limb(d,pts,w,col):
    d.line(P(pts),fill=col,width=int(w*S),joint='curve')
    for x,y in (pts[0],pts[-1]): r=w/2; d.ellipse([(x-r)*S,(y-r)*S,(x+r)*S,(y+r)*S],fill=col)

def character(d,cx,s,t,knee,armup,mood,blink,trem,fall):
    def L(x,y): return (cx+x*s+trem*math.sin(t*90)*(y/300), GY-y*s)
    hip=150*(1-0.5*knee)
    kx=14+40*knee
    for sx in (-1,1):   # thin black legs + shoes
        limb(d,[L(sx*20,10),L(sx*kx,hip*0.5),L(sx*12,hip)],11*s,BLK)
        x,y=L(sx*26,6); d.rounded_rectangle([(x-24*s)*S,(y-12*s)*S,(x+22*s)*S,(y+8*s)*S],radius=8*S,fill=(50,50,58))
        d.rectangle([(x-24*s)*S,(y+2*s)*S,(x+22*s)*S,(y+8*s)*S],fill=(220,220,225))
    # hoodie body
    top=hip+150
    body=[L(-46,top),L(46,top),L(52,hip+8),L(-52,hip+8)]
    d.polygon(P(body),fill=HOOD)
    d.rounded_rectangle(P([L(-52,hip+22),L(52,hip-2)]),radius=int(10*s*S),fill=HOOD_D)  # waistband
    px0,py0=L(-28,hip+70); px1,py1=L(28,hip+36)
    d.rounded_rectangle([px0*S,py0*S,px1*S,py1*S],radius=int(10*s*S),fill=HOOD_D)  # pocket
    for sx in (-1,1):  # drawstrings
        a=L(sx*12,top-4); b=L(sx*14,top-58); limb(d,[a,b],4*s,(245,240,230))
    # hood collar
    hx0,hy0=L(-50,top+22); hx1,hy1=L(50,top-26)
    d.ellipse([hx0*S,hy0*S,hx1*S,hy1*S],fill=HOOD_D)
    # arms (sleeves) + black hands
    for sx in (-1,1):
        a=armup
        sh=L(sx*44,top-12); el=L(sx*(70+8*a),top-70+110*a); ha=L(sx*(66-4*a),top-130+230*a)
        limb(d,[sh,el,ha],24*s,HOOD)
        r=12*s; d.ellipse([(ha[0]-r)*S,(ha[1]-r)*S,(ha[0]+r)*S,(ha[1]+r)*S],fill=BLK)
    # neck + head
    nx,ny=L(0,top+6); d.rectangle([(nx-8*s)*S,(ny-14*s)*S,(nx+8*s)*S,ny*S],fill=BLK)
    hx,hy=L(0,top+68); r=62*s
    d.ellipse([(hx-r)*S,(hy-r)*S,(hx+r)*S,(hy+r)*S],fill=BLK)
    # hair: dark-red swoop
    d.chord([(hx-r*0.95)*S,(hy-r*1.08)*S,(hx+r*0.95)*S,(hy-r*0.2)*S],190,350,fill=(120,40,36))
    d.ellipse([(hx+r*0.15)*S,(hy-r*1.15)*S,(hx+r*0.75)*S,(hy-r*0.7)*S],fill=(120,40,36))
    # eyes
    for sx in (-1,1):
        ex,ey=hx+sx*24*s,hy-2*s; er=(17 if mood!='shock' else 22)*s
        if mood=='hurt':
            w=int(5*s*S); k=11*s
            d.line([(ex-k)*S,(ey-k)*S,(ex+k)*S,(ey+k)*S],fill='white',width=w); d.line([(ex-k)*S,(ey+k)*S,(ex+k)*S,(ey-k)*S],fill='white',width=w)
            continue
        if blink: d.line([(ex-er)*S,ey*S,(ex+er)*S,ey*S],fill='white',width=int(5*s*S)); continue
        d.ellipse([(ex-er)*S,(ey-er)*S,(ex+er)*S,(ey+er)*S],fill='white')
        pr=(8 if mood!='shock' else 6)*s; d.ellipse([(ex-pr+3*s)*S,(ey-pr+2*s)*S,(ex+pr+3*s)*S,(ey+pr+2*s)*S],fill=BLK)
        if mood in('worry','shock'):  # slanted brows
            d.line([(ex-16*s)*S,(ey-er-8*s+sx*(-6)*s)*S,(ex+16*s)*S,(ey-er-8*s+sx*6*s)*S],fill='white',width=int(5*s*S))
    my=hy+30*s
    if mood=='happy': d.arc([(hx-14*s)*S,(my-14*s)*S,(hx+14*s)*S,(my+6*s)*S],20,160,fill='white',width=int(5*s*S))
    elif mood=='worry': d.arc([(hx-12*s)*S,(my-2*s)*S,(hx+12*s)*S,(my+14*s)*S],200,340,fill='white',width=int(5*s*S))
    elif mood=='shock': d.ellipse([(hx-8*s)*S,(my-6*s)*S,(hx+8*s)*S,(my+12*s)*S],outline='white',width=int(4*s*S))
    else:
        pts=[(hx-16*s+i*6*s,my+(4*s if i%2 else -2*s)) for i in range(6)]; d.line(P(pts),fill='white',width=int(4*s*S))
    return hx,hy,r

def caption(d,words,t0,t,y=900,size=86):
    # words: list of (text, yellow?) ; pop-in word by word
    f=ImageFont.truetype(FK,size); gap=24
    ws=[d.textlength(w,font=f) for w,_ in words]; tot=sum(ws)+gap*(len(ws)-1); x=W/2-tot/2
    for i,((w,yel),wl) in enumerate(zip(words,ws)):
        p=back((t-t0-i*0.12)/0.18)
        if p<=0: x+=wl+gap; continue
        fs=ImageFont.truetype(FK,max(8,int(size*(0.6+0.4*min(p,1.2)))))
        d.text((x+wl/2,y),w,font=fs,fill=YEL if yel else (245,245,240),anchor='mm',stroke_width=7,stroke_fill=(10,12,16))
        x+=wl+gap
def bubble(d,txt,x,y,p):
    if p<=0: return
    f=ImageFont.truetype(FK,int(48*min(1,p))); tw=d.textlength(txt,font=f)
    d.rounded_rectangle([x-tw/2-34,y-48,x+tw/2+34,y+48],radius=48,fill=(232,234,236))
    d.polygon([(x-30,y+40),(x+10,y+40),(x-45,y+85)],fill=(232,234,236))
    d.text((x,y),txt,font=f,fill=(55,60,66),anchor='mm')

for f in range(N):
    t=f/FPS
    shake=0
    if 3.4<t<3.7: shake=10*math.sin(t*95)
    if 4.0<t<4.6: shake=20*math.sin(t*70)*(4.6-t)*1.6
    im=BG.copy() if shake==0 else BG.transform(BG.size,Image.AFFINE,(1,0,-shake*S,0,1,0))
    d=ImageDraw.Draw(im)
    g=back((t-1.3)/1.4); s=0.8+g*0.88
    knee=min(1,ease((t-3.4)/0.4)+0.5*ease((t-3.95)/0.35))
    armup=(1-ease((t-3.3)/0.4)) if t>1.3 else 0.0
    mood='happy'
    if t>2.7: mood='worry'
    if t>3.15: mood='shock'
    if t>3.45: mood='hurt'
    blink=0.75<t<0.83
    trem=5 if 2.9<t<3.4 else 0
    cx=W/2+shake
    # back glow
    gl=Image.new('L',(W*S,H*S),0); gd=ImageDraw.Draw(gl)
    a=0.45+ (0.4*(0.6+0.4*math.sin(t*10)) if 1.0<t<3.0 else 0)
    gd.ellipse([(cx-260*s)*S,(GY-470*s)*S,(cx+260*s)*S,(GY+40)*S],fill=int(120*a))
    im.paste((70,190,210) if 1.0<t<3.0 else (60,130,150),(0,0),gl.filter(ImageFilter.GaussianBlur(70*S))); d=ImageDraw.Draw(im)
    # floor shadow
    d.ellipse([(cx-110*s)*S,(GY-10*s)*S,(cx+110*s)*S,(GY+14*s)*S],fill=(40,28,22))
    if 1.0<t<3.0:
        for k in range(10):
            r=random.Random(k*13+int(t*8)); x=cx+r.uniform(-220,220)*s; y=GY-r.uniform(30,420)*s; rr=r.uniform(3,7)
            d.ellipse([(x-rr)*S,(y-rr)*S,(x+rr)*S,(y+rr)*S],fill=(160,240,255))
    hx,hy,hr=character(d,cx,s,t,knee,armup,mood,blink,trem,0)
    if t>3.42:  # glowing red cracks at knees
        for sx in (-1,1):
            x0,y0=cx+sx*(14+40*knee)*s,GY-150*(1-0.5*knee)*0.5*s
            rr=random.Random(sx); pts=[(x0,y0)]
            for k in range(5): pts.append((pts[-1][0]+rr.uniform(-18,18)*s/2,pts[-1][1]+rr.uniform(-22,22)*s/2))
            ov=Image.new('L',(W*S,H*S),0); ImageDraw.Draw(ov).line(P(pts),fill=255,width=int(10*S))
            im.paste((255,70,50),(0,0),ov.filter(ImageFilter.GaussianBlur(8*S))); d=ImageDraw.Draw(im)
            d.line(P(pts),fill=(255,200,170),width=int(3*S))
    if t>4.0:
        p=ease((t-4.0)/0.9)
        for k in range(12):
            r=random.Random(k); side=-1 if k%2 else 1; dist=p*r.uniform(160,480)
            x=cx+side*dist; y=GY-8-p*r.uniform(10,70); rad=(1-p*0.5)*r.uniform(25,55)
            d.ellipse([(x-rad)*S,(y-rad)*S,(x+rad)*S,(y+rad)*S],fill=(96,74,60))
    im=im.resize((W,H),Image.LANCZOS)
    arr=np.asarray(im).astype(np.float32)*vig
    arr+=np.random.default_rng(f).normal(0,5,arr.shape[:2])[...,None]
    im=Image.fromarray(np.clip(arr,0,255).astype(np.uint8)); d=ImageDraw.Draw(im)
    if t<1.3: caption(d,[('TU',0),('DEVIENS',0),('GÉANT',1)],0.15,t)
    elif t<2.7: caption(d,[('×10',1),('EN',0),('TAILLE…',0)],1.35,t) if t<2.0 else caption(d,[('×1 000',1),('EN',0),('POIDS',1)],2.0,t)
    elif t<3.4: caption(d,[('ET',0),('TES',0),('OS…',1)],2.7,t)
    else: caption(d,[('ILS',0),('CÈDENT',1)],3.45,t)
    if 2.75<t<3.4: bubble(d,'Euh…',hx-300,max(110,hy-110),back((t-2.75)/0.25))
    if t>3.45: bubble(d,'AÏE !',hx-300,max(110,hy-120),back((t-3.45)/0.2))
    im.save(f'f_{f:04d}.png')

SR=44100; n=int(SR*DUR); a=np.zeros(n); rng=np.random.default_rng(2); tt=np.arange(n)/SR
a+=0.10*(np.sin(2*np.pi*55*tt)+0.6*np.sin(2*np.pi*82.4*tt))*(0.7+0.3*np.sin(2*np.pi*0.3*tt))  # low drone
def put(sig,at): i=int(at*SR); a[i:i+len(sig)]+=sig[:max(0,n-i)]
L=int(1.4*SR); x=np.arange(L)/SR
put((np.sin(2*np.pi*(120+500*x**1.6)*x)*0.4+np.convolve(rng.standard_normal(L),np.ones(30)/30,'same')*0.6)*np.hanning(L),1.3)
for k,t0 in enumerate([0.15,0.27,0.39,1.35,1.47,2.0,2.12,2.24,2.7,2.82,2.94,3.45,3.57]):
    x=np.arange(int(0.06*SR))/SR; put(np.sin(2*np.pi*900*x)*np.exp(-x*60)*0.25,t0)  # word pops
x=np.arange(int(0.12*SR))/SR; put(np.sin(2*np.pi*(500+800*x/0.12)*x)*np.hanning(len(x))*0.3,2.75)
c=int(0.3*SR); put(rng.standard_normal(c)*np.exp(-np.arange(c)/SR*25)*0.9,3.42)
x=np.arange(int(1.0*SR))/SR; put(np.sin(2*np.pi*(50+60*np.exp(-x*12))*x)*np.exp(-x*3.5)*1.1,4.0)
a=a/np.abs(a).max()*0.9
with wave.open('sfx.wav','w') as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((a*32767).astype(np.int16).tobytes())
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','30','-i','f_%04d.png','-i','sfx.wav','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-shortest','-movflags','+faststart','test_style_etsi_5s.mp4'],check=True)
print('ok')
