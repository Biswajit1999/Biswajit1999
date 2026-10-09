#!/usr/bin/env python3
"""DEEP SKY: render astronomy-inspired, reproducible model animations for a GitHub README.

Every plot is synthetic, deliberately idealised, and NEVER presented as real observational data.
Requires Pillow + numpy; has no web dependencies. Saves GIF and a static reduced-motion fallback.
"""
from __future__ import annotations
import math
import os
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = Path(os.environ.get('PROFILE_OUT', 'assets/profile-cinema'))
OUT.mkdir(parents=True, exist_ok=True)
W, H = 1320, 350
SCALED = 1
FONT_R = ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf']
FONT_B = ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf']
def font(sz, bold=False):
    for p in (FONT_B if bold else FONT_R):
        if Path(p).is_file(): return ImageFont.truetype(p,sz)
    return ImageFont.load_default()

def rgba(col, alpha=255): return tuple(col)+(alpha,)
C=(68,226,221); BLUE=(92,180,248); GOLD=(250,193,117)

# Established mathematical toy models: analytic transit, Gaussian absorption, Keplerian RV approximation.
X=np.linspace(0,1,360)
# planet/star radius ratio 0.09 -> 0.81% full-transit flux decrement.
DEPTH = .09**2
# Two smooth ingress/egress edges using hyperbolic tangent (illustrative, NOT limb-darkened).
window=.5*(np.tanh((X-.365)/.014)-np.tanh((X-.635)/.014))
transit=1.-DEPTH*window
# Reproducible Gaussian noise only for rendering -- not measured photometry.
noise=np.random.default_rng(1999).normal(0,.00020,size=len(X))
flux=transit+noise
# Wavelength axis: continuum-normalized toy stellar spectrum with fixed synthetic absorption lines.
lam=np.linspace(510.,530.,540)
centres=[512.8,516.7,518.35,524.5,527.55]
amps=[.22,.47,.30,.39,.18]
widths=[.15,.24,.12,.29,.20]
spectrum=np.ones_like(lam)
for center,depth,width in zip(centres,amps,widths):
    spectrum-=depth*np.exp(-.5*((lam-center)/width)**2)
# Simulated velocity: circular-orbit toy model, NOT a fit to actual data.
phase=np.linspace(0,1,340)
vel=2.6*np.sin(2*np.pi*phase+.4)

# Subtle real photographic texture from existing repository's hero preview, if present.
def backdrop():
    arr=np.zeros((H,W,3),dtype=np.uint8)
    y=np.arange(H)[:,None]
    x=np.arange(W)[None,:]
    arr[:,:,0]=np.clip(4+4*y/H,0,255)
    arr[:,:,1]=np.clip(13+8*y/H+2*np.sin(x/95),0,255)
    arr[:,:,2]=np.clip(27+18*y/H+4*np.cos(x/153),0,255)
    im=Image.fromarray(arr,'RGB').convert('RGBA')
    existing=OUT/'hero-preview.jpg'
    if existing.is_file():
        photo=Image.open(existing).convert('RGBA').resize((W,H),Image.Resampling.LANCZOS)
        photo=photo.filter(ImageFilter.GaussianBlur(15))
        im=Image.blend(im,photo,.13)
    d=ImageDraw.Draw(im,'RGBA')
    rng=np.random.default_rng(3502)
    for sx,sy,inten in zip(rng.integers(0,W,170),rng.integers(0,H,170),rng.integers(45,150,170)):
        d.ellipse((int(sx),int(sy),int(sx+1),int(sy+1)),fill=(170,210,255,int(inten)))
    d.rounded_rectangle((1,1,W-2,H-2),radius=17,outline=(36,109,140,165),width=2)
    d.text((28,15),'THE LIGHT REACHES EARTH. THE QUESTIONS BEGIN.',font=font(19,True),fill=(221,247,254,255))
    d.text((29,45),'THREE EXPLICIT TOY MODELS  /  NO LIVE OBSERVATIONS  /  NOT INSTRUMENT DATA',font=font(11),fill=(121,187,202,255))
    d.line((29,67,W-30,67),fill=(44,101,127,135),width=1)
    d.line((29,67,318,67),fill=(59,210,204,245),width=2)
    return im

BACKGROUND=backdrop()
PANELS=[(26,91,437,315),(454,91,865,315),(882,91,1293,315)]

def path(draw,coords,color,width=2):
    # antialiased appearance via sub-pixel model curve sampled densely in screen space
    draw.line([(int(round(x)),int(round(y))) for x,y in coords],fill=rgba(color,240),width=width,joint='curve')

def plot_area(d,box,title,subtitle,color,xlabels,ylabels):
    x1,y1,x2,y2=box
    d.rounded_rectangle(box,radius=11,fill=(6,20,35,220),outline=rgba(color,104),width=1)
    d.rounded_rectangle((x1+15,y1+12,x1+148,y1+38),radius=4,fill=(17,45,59,220),outline=rgba(color,85),width=1)
    d.text((x1+24,y1+17),title,font=font(13,True),fill=rgba(color))
    d.text((x1+163,y1+17),subtitle,font=font(13,True),fill=(220,239,248,242))
    left=x1+49; right=x2-23; top=y1+61; bottom=y2-57
    for f in (0,.25,.5,.75,1):
        yy=bottom-f*(bottom-top)
        d.line((left,yy,right,yy),fill=(56,93,115,82),width=1)
    d.line((left,top,left,bottom),fill=(91,130,159,210),width=1)
    d.line((left,bottom,right,bottom),fill=(91,130,159,210),width=1)
    d.text((left-2,bottom+7),xlabels[0],font=font(10),fill=(130,168,191,255))
    d.text((right-45,bottom+7),xlabels[1],font=font(10),fill=(130,168,191,255))
    d.text((x1+7,top-5),ylabels[0],font=font(9),fill=(143,188,204,242))
    d.text((x1+7,bottom-10),ylabels[1],font=font(9),fill=(143,188,204,242))
    return left,top,right,bottom

def translucent_glow(line_points,color,base,r=3):
    layer=Image.new('RGBA',(W,H));ld=ImageDraw.Draw(layer,'RGBA')
    ld.line(line_points,fill=rgba(color,160),width=base+3)
    return layer.filter(ImageFilter.GaussianBlur(r))


def panel_1(img,d,index,frames):
    l,t,r,b=plot_area(d,PANELS[0],'01  /  TRANSIT','A SHADOW IN STARLIGHT',C,('EARLY','LATE'),('1.00','0.99'))
    x=lambda xx:l+xx*(r-l)
    y=lambda f:b-(f-.9895)/(.0109)*(b-t)
    clean=[(x(q),y(f)) for q,f in zip(X,transit)]
    data=[(x(q),y(f)) for q,f in zip(X,flux)]
    # Gently luminous theoretical model and measured-looking SYNTHETIC samples.
    img.alpha_composite(translucent_glow(clean,C,2))
    d.line(clean,fill=rgba(C,230),width=3,joint='curve')
    for i in range(0,len(data),10):
        sx,sy=data[i]
        d.ellipse((sx-1,sy-1,sx+1,sy+1),fill=(214,247,242,210))
    cursor=(index/(frames-1))
    xx=x(cursor)
    fy=1.-DEPTH*.5*(math.tanh((cursor-.365)/.014)-math.tanh((cursor-.635)/.014))
    cy=y(fy)
    d.line((xx,t,xx,b),fill=rgba(GOLD,146),width=1)
    d.ellipse((xx-4,cy-4,xx+4,cy+4),fill=rgba(GOLD),outline=(255,252,226,255),width=1)
    d.text((PANELS[0][0]+18,PANELS[0][3]-23),'Rp/R* = 0.09  ·  DEPTH = 0.81%  ·  SYNTHETIC',font=font(11),fill=(157,207,211,255))

def panel_2(img,d,index,frames):
    l,t,r,b=plot_area(d,PANELS[1],'02  /  SPECTRUM','ABSORPTION FEATURES',BLUE,('510 nm','530 nm'),('1.0','0.5'))
    x=lambda a:l+(a-510)/20*(r-l)
    y=lambda f:b-(f-.40)/(.66)*(b-t)
    pts=[(x(a),y(f)) for a,f in zip(lam,spectrum)]
    img.alpha_composite(translucent_glow(pts,BLUE,2))
    d.line(pts,fill=rgba(BLUE,235),width=2,joint='curve')
    # sweeping guide/probe only; no exaggerated Doppler shift implying measured RV precision
    probe=510.+20.*index/(frames-1)
    xx=x(probe)
    d.line((xx,t,xx,b),fill=(175,224,251,165),width=1)
    cy=y(float(np.interp(probe,lam,spectrum)))
    d.ellipse((xx-3,cy-3,xx+3,cy+3),fill=(255,226,177,245))
    d.text((PANELS[1][0]+18,PANELS[1][3]-23),'CONTINUUM-NORMALISED  ·  FIVE GAUSSIAN LINES',font=font(11),fill=(157,207,211,255))

def panel_3(img,d,index,frames):
    l,t,r,b=plot_area(d,PANELS[2],'03  /  DOPPLER','STELLAR RADIAL VELOCITY',GOLD,('0 cycles','1 cycle'),('+3','-3'))
    x=lambda a:l+a*(r-l)
    y=lambda v:b-(v+3.2)/6.4*(b-t)
    d.line((l,y(0),r,y(0)),fill=(153,187,205,90),width=1)
    pts=[(x(a),y(v)) for a,v in zip(phase,vel)]
    img.alpha_composite(translucent_glow(pts,GOLD,2))
    d.line(pts,fill=rgba(GOLD,241),width=3,joint='curve')
    cursor=index/(frames-1)
    xx=x(cursor); v=2.6*math.sin(2*math.pi*cursor+.4);cy=y(v)
    d.line((xx,t,xx,b),fill=rgba(C,135),width=1)
    d.ellipse((xx-4,cy-4,xx+4,cy+4),fill=(255,241,217,255),outline=rgba(GOLD),width=2)
    d.text((PANELS[2][0]+18,PANELS[2][3]-23),'K = 2.6 m/s  ·  CIRCULAR-ORBIT MODEL',font=font(11),fill=(157,207,211,255))

def draw_frame(index,frames):
    im=BACKGROUND.copy()
    d=ImageDraw.Draw(im,'RGBA')
    for fn in (panel_1,panel_2,panel_3):
        fn(im,d,index,frames)
    d.text((30,332),'A TRANSIT CHANGES BRIGHTNESS',font=font(10,True),fill=rgba(C,225))
    d.text((480,332),'ATOMS IMPRINT ABSORPTION LINES',font=font(10,True),fill=rgba(BLUE,225))
    d.text((910,332),'ORBITING PLANETS MOVE THEIR STARS',font=font(10,True),fill=rgba(GOLD,225))
    return im.convert('RGB')

def main():
    frames=36
    still=draw_frame(17,frames)
    still.save(OUT/'deep-sky-telemetry.jpg',quality=85,optimize=True,subsampling=2)
    imgs=[draw_frame(i,frames) for i in range(frames)]
    dst=OUT/'deep-sky-telemetry.gif'
    imgs[0].save(dst,save_all=True,append_images=imgs[1:],duration=125,loop=0,optimize=True,disposal=2,colors=96)
    with Image.open(dst) as im:
        assert im.n_frames>=30,im.n_frames
        assert im.size==(W,H)
        assert im.info.get('loop')==0
    print(f'DEEP_SKY_TELEMETRY {dst} ({dst.stat().st_size:,} bytes, {frames} frames)')
    print(f'DEEP_SKY_STILL {OUT/"deep-sky-telemetry.jpg"}')

if __name__=='__main__': main()
