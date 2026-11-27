import math, random, subprocess, wave, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H,FPS,DUR,S=1920,1080,30,5.0,2
N=int(FPS*DUR); GY=900
FB='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
OUT=(43,33,64); SKIN=(255,206,160); SHIRT=(255,110,64); PANTS=(60,90,200); SHOE=(250,250,250); HAIR=(70,45,35)
def ease(t): t=max(0,min(1,t)); return t*t*(3-2*t)
def back(t):
    t=max(0,min(1,t)); c=1.9; return 1+(c+1)*(t-1)**3+c*(t-1)**2
def P(p): return [(x*S,y*S) for x,y in p]
def blob(d,box,fill,ow=6):
    x0,y0,x1,y1=box
    d.ellipse([(x0-ow)*S,(y0-ow)*S,(x1+ow)*S,(y1+ow)*S],fill=OUT)
    d.ellipse([x0*S,y0*S,x1*S,y1*S],fill=fill)
def limb(d,pts,w,fill):
    for col,ww in ((OUT,w+12),(fill,w)):
        d.line(P(pts),fill=col,width=int(ww*S),joint='curve')
        for x,y in (pts[0],pts[-1]): r=ww/2; d.ellipse([(x-r)*S,(y-r)*S,(x+r)*S,(y+r)*S],fill=col)
def rrect(d,box,r,fill,ow=6):
    x0,y0,x1,y1=box
    d.rounded_rectangle([(x0-ow)*S,(y0-ow)*S,(x1+ow)*S,(y1+ow)*S],radius=(r+ow)*S,fill=OUT)
    d.rounded_rectangle([x0*S,y0*S,x1*S,y1*S],radius=r*S,fill=fill)
def star(cx,cy,r1,r2,n=10,rot=0):
    return [(cx+(r1 if i%2==0 else r2)*math.cos(rot+i*math.pi/n*1), cy+(r1 if i%2==0 else r2)*math.sin(rot+i*math.pi/n)) for i in range(2*n)]

# static background
def background(shake):
    im=Image.new('RGB',(W*S,H*S)); d=ImageDraw.Draw(im)
    for y in range(GY):
        k=y/GY; d.line([(0,y*S),(W*S,y*S)],fill=(int(110+90*k),int(190+40*k),int(255-10*k)),width=S)
    d.ellipse([1600*S,90*S,1760*S,250*S],fill=(255,220,90))
    for cx,cy,sc in [(300,180,1),(900,120,0.8),(1350,230,1.1)]:
        for dx,dy,r in [(0,0,55),(60,-20,65),(125,0,55),(60,20,50)]:
            d.ellipse([(cx+dx*sc-r*sc)*S,(cy+dy*sc-r*sc)*S,(cx+dx*sc+r*sc)*S,(cy+dy*sc+r*sc)*S],fill=(255,255,255))
    cols=[(255,170,180),(255,214,110),(140,210,170),(170,160,240),(255,150,110),(120,200,240)]
    for i,(bx,bw,bh) in enumerate([(60,170,330),(250,140,250),(1450,190,360),(1660,150,270),(1830,120,200)]):
        x=bx+shake
        rrect(d,(x,GY-bh,x+bw,GY+10),14,cols[i%6])
        for wy in range(GY-bh+30,GY-50,55):
            for wx in range(int(x+20),int(x+bw-40),45):
                d.rounded_rectangle([wx*S,wy*S,(wx+26)*S,(wy+32)*S],radius=5*S,fill=(255,250,220),outline=OUT,width=3*S)
    d.rectangle([0,GY*S,W*S,H*S],fill=(120,200,90))
    d.line([(0,GY*S),(W*S,GY*S)],fill=OUT,width=7*S)
    for k in range(40):
        r=random.Random(k); x=r.uniform(0,W); y=r.uniform(GY+25,H-10)
        d.line([(x*S,y*S),((x+8)*S,(y-14)*S)],fill=(90,170,70),width=4*S)
    return im

def character(d,cx,s,t,knee,armup,squash,mood,blink,tremble):
    # local coords: feet at y=0, up negative screen; unit height ~260
    def L(x,y): return (cx+x*s+tremble*math.sin(t*80)*(y/260), GY-y*s*squash)
    hip=110*(1-0.45*knee); 
    kx=18+38*knee
    # legs
    for sx in (-1,1):
        limb(d,[L(sx*28,8),L(sx*kx,hip*0.5+6),L(sx*16,hip)],26*s,PANTS)
        x,y=L(sx*34,6); rrect(d,(x-26*s,y-18*s,x+26*s,y+8*s),10*s,SHOE,6)
    # arms
    for sx in (-1,1):
        a=armup
        sh=L(sx*42,hip+95)
        el=L(sx*(70+10*a),hip+95-40+90*a)
        ha=L(sx*(80-5*a),hip+95-75+180*a)
        limb(d,[sh,el,ha],20*s,SKIN)
        r=17*s; blob(d,(ha[0]-r,ha[1]-r,ha[0]+r,ha[1]+r),SKIN,6)
    # body
    x0,y0=L(-50,hip+110); x1,y1=L(50,hip-8)
    rrect(d,(x0,y0,x1,y1),36*s,SHIRT,7)
    # head
    hx,hy=L(0,hip+175); r=70*s
    blob(d,(hx-r,hy-r,hx+r,hy+r),SKIN,7)
    # hair tuft
    for k,(dx,dy) in enumerate([(-25,-62),(0,-75),(25,-62)]):
        d.ellipse([(hx+dx*s-22*s)*S,(hy+dy*s-22*s)*S,(hx+dx*s+22*s)*S,(hy+dy*s+22*s)*S],fill=HAIR)
    # eyes
    for sx in (-1,1):
        ex,ey=hx+sx*26*s,hy-8*s
        er=(22 if mood!='shock' else 28)*s
        if mood=='hurt':
            w=5*s
            d.line([(ex-14*s)*S,(ey-14*s)*S,(ex+14*s)*S,(ey+14*s)*S],fill=OUT,width=int(w*S))
            d.line([(ex-14*s)*S,(ey+14*s)*S,(ex+14*s)*S,(ey-14*s)*S],fill=OUT,width=int(w*S))
            continue
        if blink:
            d.line([(ex-er)*S,ey*S,(ex+er)*S,ey*S],fill=OUT,width=int(6*s*S)); continue
        blob(d,(ex-er*0.8,ey-er,ex+er*0.8,ey+er),(255,255,255),4*s)
        pr=(10 if mood!='shock' else 7)*s
        d.ellipse([(ex-pr+2*s)*S,(ey-pr+3*s)*S,(ex+pr+2*s)*S,(ey+pr+3*s)*S],fill=OUT)
        d.ellipse([(ex-pr*0.3+5*s)*S,(ey-pr*0.3)*S,(ex+pr*0.3+5*s)*S,(ey+pr*0.3+0)*S],fill=(255,255,255))
    # cheeks
    for sx in (-1,1):
        cx2=hx+sx*45*s; cy2=hy+22*s
        d.ellipse([(cx2-12*s)*S,(cy2-7*s)*S,(cx2+12*s)*S,(cy2+7*s)*S],fill=(255,150,150))
    # mouth
    my=hy+30*s
    if mood=='happy':
        d.chord([(hx-26*s)*S,(my-22*s)*S,(hx+26*s)*S,(my+18*s)*S],0,180,fill=(150,40,60),outline=OUT,width=int(5*s*S))
    elif mood=='shock':
        d.ellipse([(hx-12*s)*S,(my-8*s)*S,(hx+12*s)*S,(my+20*s)*S],fill=(150,40,60),outline=OUT,width=int(5*s*S))
    else:
        pts=[(hx-24*s+i*8*s,my+(6*s if i%2 else -2*s)) for i in range(7)]
        d.line(P(pts),fill=OUT,width=int(5*s*S))
    return (hx,hy,r)

frames=[]
for f in range(N):
    t=f/FPS
    shake=0
    if 3.4<t<3.7: shake=12*math.sin(t*95)
    if 4.0<t<4.6: shake=22*math.sin(t*70)*(4.6-t)*1.6
    im=background(shake); d=ImageDraw.Draw(im)
    g=back((t-1.4)/1.5); s=0.85+g*1.42
    antic=ease((t-1.05)/0.3)*(1-ease((t-1.35)/0.1))
    squash=1-0.12*antic + 0.06*math.sin(max(0,t-1.4)*20)*max(0,1-(t-1.4)*2)
    bob=0.02*math.sin(t*6) if t<1 else 0
    knee=ease((t-3.4)/0.4)
    fall=ease((t-3.95)/0.35)
    knee=min(1,knee+fall*0.6)
    armup=1-ease((t-3.3)/0.4) if t>1.4 else ease((t-0.4)/0.4)*0.3
    mood='happy'
    if t>2.9: mood='shock'
    if t>3.45: mood='hurt'
    blink=0.62<t<0.7
    trem=6 if 2.95<t<3.4 else 0
    cx=W/2+shake
    # glow + sparkles
    if 1.0<t<3.0:
        a=min(1,(t-1)*3)*(0.6+0.4*math.sin(t*12))
        glow=Image.new('L',(W*S,H*S),0); gd=ImageDraw.Draw(glow)
        gd.ellipse([(cx-170*s)*S,(GY-330*s)*S,(cx+170*s)*S,(GY+20)*S],fill=int(170*a))
        glow=glow.filter(ImageFilter.GaussianBlur(50*S)); im.paste((120,220,255),(0,0),glow); d=ImageDraw.Draw(im)
        for k in range(8):
            r=random.Random(k*7+int(t*6)); x=cx+r.uniform(-190,190)*s; y=GY-r.uniform(20,340)*s; rr=r.uniform(10,22)
            d.polygon(P(star(x,y,rr,rr*0.35,4,t*3)),fill=(255,255,180))
    hx,hy,hr=character(d,cx,s,t,knee,armup,squash*(1+bob),mood,blink,trem)
    # sweat
    if 2.95<t<3.45:
        for k,(dx,dy) in enumerate([(1.05,-0.6),(-1.1,-0.4)]):
            x=hx+dx*hr; y=hy+dy*hr+((t*120+k*20)%30)
            d.polygon(P([(x,y-26),(x-14,y+6),(x+14,y+6)]),fill=(150,210,255),outline=OUT)
            d.ellipse([(x-14)*S,(y-8)*S,(x+14)*S,(y+18)*S],fill=(150,210,255),outline=OUT,width=3*S)
    # dizzy stars
    if t>4.2:
        for k in range(3):
            ang=t*5+k*2.09; x=hx+math.cos(ang)*hr*1.3; y=hy-hr*1.05+math.sin(ang)*hr*0.3
            d.polygon(P(star(x,y,26,11,5,ang)),fill=(255,220,60),outline=OUT,width=3*S)
    # dust
    if t>4.0:
        p=ease((t-4.0)/0.9)
        for k in range(12):
            r=random.Random(k); side=-1 if k%2 else 1; dist=p*r.uniform(200,520)
            x=cx+side*dist; y=GY-10-p*r.uniform(10,90); rad=(1-p*0.5)*r.uniform(35,70)
            d.ellipse([(x-rad)*S,(y-rad)*S,(x+rad)*S,(y+rad)*S],fill=(235,225,200),outline=OUT,width=4*S)
    im=im.resize((W,H),Image.LANCZOS); d=ImageDraw.Draw(im)
    # title card
    if t<2.4:
        a=min(1,t*4); y=-60+160*ease(t*3)
        d.rounded_rectangle([W/2-360,y-75,W/2+360,y+75],radius=40,fill=(255,255,255),outline=OUT,width=7)
        d.text((W/2-235,y),'N°5',font=ImageFont.truetype(FB,82),fill=(235,60,70),anchor='mm')
        d.text((W/2+85,y),'DEVENIR GÉANT',font=ImageFont.truetype(FB,44),fill=OUT,anchor='mm')
    # x1000 bubble
    if 1.9<t<3.35:
        p=back((t-1.9)/0.3); bx,by=1480,470
        d.ellipse([bx-150*p,by-95*p,bx+150*p,by+95*p],fill=(255,240,90),outline=OUT,width=7)
        if p>0.6:
            d.text((bx,by-15),'× 1 000',font=ImageFont.truetype(FB,64),fill=(235,60,70),anchor='mm',stroke_width=3,stroke_fill=OUT)
            d.text((bx,by+42),'de poids !',font=ImageFont.truetype(FB,36),fill=OUT,anchor='mm')
    # CRAC burst
    if t>3.42:
        p=back((t-3.42)/0.25); bx,by=380,430
        d.polygon(star(bx,by,230*p,140*p,12,0.2),fill=(255,230,60),outline=OUT,width=8)
        if p>0.5:
            d.text((bx,by),'CRAC !',font=ImageFont.truetype(FB,int(96*min(p,1.15))),fill=(235,50,60),anchor='mm',stroke_width=6,stroke_fill=OUT)
    im.save(f'f_{f:04d}.png')

SR=44100; n=int(SR*DUR); a=np.zeros(n); rng=np.random.default_rng(2)
def put(sig,at): i=int(at*SR); a[i:i+len(sig)]+=sig[:max(0,n-i)]
x=np.arange(int(0.12*SR))/SR; put(np.sin(2*np.pi*(600+2400*x/0.12)*x)*np.hanning(len(x))*0.4,1.05)  # boing up
L=int(1.5*SR); x=np.arange(L)/SR
put((np.sin(2*np.pi*(180+700*x**1.5)*x)*0.35+np.sin(2*np.pi*(360+1400*x**1.5)*x)*0.15)*np.hanning(L),1.4)  # rising zip
for k,tt in enumerate([1.5,1.8,2.1,2.4]):
    x=np.arange(int(0.15*SR))/SR; put(np.sin(2*np.pi*(1800+k*300)*x)*np.exp(-x*25)*0.2,tt)  # sparkles
x=np.arange(int(0.35*SR))/SR; put(np.sin(2*np.pi*(700-300*x)*x+8*np.sin(2*np.pi*14*x))*np.hanning(len(x))*0.3,2.95)  # gulp wobble
c=int(0.3*SR); put(rng.standard_normal(c)*np.exp(-np.arange(c)/SR*25)*0.8,3.42)
x=np.arange(int(1.0*SR))/SR; put(np.sin(2*np.pi*(55+60*np.exp(-x*12))*x)*np.exp(-x*3.5)*1.0,4.0)
x=np.arange(int(0.9*SR))/SR; put(np.sin(2*np.pi*(1400+300*np.sin(2*np.pi*6*x))*x)*np.exp(-x*3)*0.12,4.2)  # dizzy tweets
a=a/np.abs(a).max()*0.9
with wave.open('sfx.wav','w') as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((a*32767).astype(np.int16).tobytes())
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','30','-i','f_%04d.png','-i','sfx.wav','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-shortest','-movflags','+faststart','test_cartoon_5s.mp4'],check=True)
print('ok')
