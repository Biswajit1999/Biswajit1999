#!/usr/bin/env python3
"""Render self-contained GitHub README visual assets; no runtime JS or website."""
import io, math, os, random, urllib.request
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
try:
 import cv2
except ImportError:
 cv2=None

OUT=Path(os.getenv('PROFILE_OUT','/mnt/data/profile_v3')); OUT.mkdir(parents=True,exist_ok=True)
HERE=Path(__file__).resolve().parent
W,H=1320,438
FONTS=['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf']
BOLDS=['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf']
def font(s,b=False):
 for p in (BOLDS if b else FONTS):
  if os.path.isfile(p):return ImageFont.truetype(p,s)
 return ImageFont.load_default()
def line_text(d,xy,text,size,col,b=False,spacing=0):
 if not spacing:d.text(xy,text,font=font(size,b),fill=col);return
 x,y=xy
 for letter in text:
  d.text((x,y),letter,font=font(size,b),fill=col)
  x+=d.textlength(letter,font=font(size,b))+spacing

def fractal_noise(seed,size=(1024,512)):
 rng=np.random.default_rng(seed);ww,hh=size
 ns=np.zeros((hh,ww),dtype=np.float32)
 for n,weight in [(5,1.0),(12,.53),(25,.28),(58,.13),(110,.065),(245,.024)]:
  noise=rng.random((max(2,round(hh*n/ww)),n)).astype(np.float32)
  if cv2 is not None: a=cv2.resize(noise,(ww,hh),interpolation=cv2.INTER_CUBIC)
  else:a=np.array(Image.fromarray((noise*255).astype('uint8')).resize((ww,hh),Image.Resampling.BICUBIC))/255.
  ns+=weight*a
 ns-=ns.min();ns/=max(float(ns.max()),1e-6)
 return ns

# Render a textured Earth-like research planet, not an observational image.
def globe(size=440):
 n=size; yy,xx=np.mgrid[0:n,0:n].astype(np.float32);cx=(n-1)/2;cy=cx
 X=(xx-cx)/(n*.472);Y=(yy-cy)/(n*.472);rad=X*X+Y*Y;inside=rad<=1
 Z=np.sqrt(np.maximum(0.,1-rad));lon=np.arctan2(X,Z)+1.6;lat=np.arcsin(np.clip(-Y,-1,1))
 ns=fractal_noise(83,(1024,512)); clouds=fractal_noise(123,(1024,512)); ww=1024;hh=512
 uu=np.mod(((lon/(2*math.pi))+.5)*ww,ww).astype(int);vv=np.clip(((0.5-lat/math.pi)*hh).astype(int),0,hh-1)
 terrain=ns[vv,uu];cb=clouds[vv,uu]
 # Prefer a photographic planetary surface when the build runner can retrieve it.
 tex=None
 if not os.environ.get('NO_REMOTE'):
  try:
   url='https://raw.githubusercontent.com/mrdoob/three.js/master/examples/textures/planets/earth_atmos_2048.jpg'
   req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
   with urllib.request.urlopen(req,timeout=14) as resp: payload=resp.read(6*1024*1024)
   photo=Image.open(io.BytesIO(payload)).convert('RGB').resize((ww,hh),Image.Resampling.LANCZOS)
   tex=np.asarray(photo,dtype=np.float32)[vv,uu]
   print('PLANET_TEXTURE source=three.js/examples/textures/planets/earth_atmos_2048.jpg',len(payload))
  except Exception as err:print('PLANET_TEXTURE fallback',type(err).__name__)
 
 ocean=terrain<.49
 # Southern/oceanic blue-green planet with sun-lit coastlines and cloud bands.
 rgb=np.zeros((n,n,3),dtype=np.float32)
 rgb[:,:,0]=np.where(ocean,9+28*terrain,27+70*terrain)
 rgb[:,:,1]=np.where(ocean,42+100*terrain,74+90*terrain)
 rgb[:,:,2]=np.where(ocean,95+102*terrain,57+76*terrain)
 ice=(np.abs(Y)>.80)&inside
 rgb[ice]=np.array([170,212,230])
 c=np.clip((cb-.63)*5.8,0,.65)*inside
 rgb=rgb*(1-c[:,:,None])+c[:,:,None]*np.array([228,243,252])
 light=np.clip(X*(-.43)+Y*(-.29)+Z*.83,-.4,1.)
 il=.14+.93*np.power(np.maximum(light,0),.74)
 if tex is not None:
  rgb=.82*tex+.18*rgb
 rgb*=il[:,:,None]
 # warm city glints on night-side continents (artistic representation)
 rng=np.random.default_rng(87)
 pts=rng.random((n,n))
 cities=(~ocean)&(pts>.997)&(light<.30)&inside
 rgb[cities]=[255,193,91]
 alpha=np.where(inside,255,0).astype(np.uint8)
 rgba=np.concatenate((np.clip(rgb,0,255).astype(np.uint8),alpha[:,:,None]),axis=2)
 planet=Image.fromarray(rgba,'RGBA')
 # atmospheric scatter at limb, softened.
 a=np.maximum(0,1-np.abs(np.sqrt(np.clip(rad,0,None))-.98)/.065)
 ring=np.zeros((n,n,4),dtype=np.uint8);ring[:,:,0]=35;ring[:,:,1]=180;ring[:,:,2]=247;ring[:,:,3]=(a*180).clip(0,255).astype('uint8')
 r=Image.fromarray(ring,'RGBA').filter(ImageFilter.GaussianBlur(5))
 r.alpha_composite(planet)
 return r
PLANET=globe(452)

def stars_and_back(w,h,seed=2026):
 y,x=np.mgrid[:h,:w]
 t=y/h;g=np.clip(1-(x/w)*.2,0,1)
 arr=np.empty((h,w,3),dtype=np.uint8)
 arr[:,:,0]=np.clip(3+10*t+5*np.sin(x/190)*t,0,255)
 arr[:,:,1]=np.clip(9+22*t+7*np.sin(x/181)*t,0,255)
 arr[:,:,2]=np.clip(22+34*t+11*np.cos(x/190)*t,0,255)
 im=Image.fromarray(arr,'RGB').convert('RGBA');d=ImageDraw.Draw(im,'RGBA')
 rng=random.Random(seed)
 for i in range(320):
  sx=rng.randrange(w);sy=rng.randrange(h);r=rng.choices([.7,1,1.5,2],[60,26,12,2])[0];a=rng.randrange(60,190)
  d.ellipse((sx-r,sy-r,sx+r,sy+r),fill=(181,219,255,a))
  if r>1.6:
   d.line((sx-4,sy,sx+4,sy),fill=(68,210,240,a//3))
 # subtle blue-depth cloud wisps
 for i in range(9):
  cx=rng.randrange(0,w);cy=rng.randrange(0,h)
  d.ellipse((cx-100,cy-40,cx+100,cy+40),fill=(15,79,128,5))
 return im

BASE=stars_and_back(W,H)
# Filmic horizon and optical equipment silhouette at bottom right
under=Image.new('RGBA',(W,H));dd=ImageDraw.Draw(under,'RGBA')
for i in range(16):
 z=H-5-i*6
 dd.line((770,z,1320,z),fill=(6,27,42,max(0,11-i//2)),width=7)
for j,(x,w,h) in enumerate([(815,64,21),(899,28,33),(1020,47,44),(1089,29,27),(1176,67,40),(1270,30,28)]):
 dd.rectangle((x,H-h-16,x+w,H),fill=(3,12,23,240))
 dd.rectangle((x+4,H-h-20,x+w-5,H-h-15),fill=(11,26,39,255))
 for y0 in range(H-h+3,H-10,12):
  for x0 in range(x+8,x+w-6,14):
   if (j+x0+y0)%3==0:dd.rectangle((x0,y0,x0+3,y0+3),fill=(248,169,73,105))
# dome and telescope shapes
for xx,yy,rr in [(954,366,62),(1216,366,48)]:
 dd.arc((xx-rr,yy-rr*.72,xx+rr,yy+rr*.72),180,360,fill=(57,106,121,200),width=3)
 dd.rectangle((xx-rr,yy,xx+rr,H),fill=(5,20,32,235))
BASE.alpha_composite(under)
planet_layer=Image.new('RGBA',(W,H));planet_layer.alpha_composite(PLANET,(827,-10))
# precompute glow behind planet
halo=Image.new('RGBA',(W,H));gd=ImageDraw.Draw(halo,'RGBA')
for r in range(275,218,-6):gd.ellipse((1053-r,215-r,1053+r,215+r),outline=(31,141,203,max(0,9-(275-r)//13)),width=7)
halo=halo.filter(ImageFilter.GaussianBlur(17));BASE.alpha_composite(halo)
BASE.alpha_composite(planet_layer)
# deep panel contrast on left
shadow=Image.new('RGBA',(W,H));ar=np.zeros((H,W,4),dtype=np.uint8)
ar[:,:,0]=2;ar[:,:,1]=8;ar[:,:,2]=20
x=np.arange(W,dtype=np.float32)
a=np.clip(240*(1-x/950),0,240);ar[:,:,3]=a.astype('uint8')[None,:]
shadow=Image.fromarray(ar,'RGBA');BASE.alpha_composite(shadow)

# Static labels + top header and instrument chrome
static=Image.new('RGBA',(W,H));d=ImageDraw.Draw(static,'RGBA')
d.rounded_rectangle((32,30,248,61),radius=7,fill=(14,52,67,160),outline=(39,173,200,120),width=1)
d.ellipse((46,40,56,50),fill=(71,247,214,255))
line_text(d,(68,38),'SIGNAL / ONLINE',14,(119,236,222,255),True,1.5)
d.line((32,76,688,76),fill=(33,101,133,170),width=2)
d.line((33,76,160,76),fill=(77,240,221,255),width=3)
line_text(d,(29,91),'BISWAJIT',86,(240,251,255,255),True,2)
line_text(d,(33,186),'JANA',92,(71,227,220,255),True,6)
line_text(d,(39,305),'ASTROPHYSICS  /  INSTRUMENTATION',19,(209,237,248,255),True,1.0)
line_text(d,(39,335),'Precision RV · Exoplanets · Feedback Control',16,(159,203,221,255))
for x0,x1,label in [(39,220,'RESEARCH SYSTEMS'),(233,410,'OPTICAL METROLOGY'),(423,613,'SCIENTIFIC SOFTWARE')]:
 d.rounded_rectangle((x0,382,x1,411),radius=8,fill=(17,42,64,187),outline=(46,145,175,180),width=1)
 line_text(d,(x0+13,391),label,11,(164,231,246,255),True)
# visual scan markers & orbit glyphs at right
for r in [157,203,244]: d.ellipse((1053-r,215-r,1053+r,215+r),outline=(62,173,211,65),width=2)
d.arc((861,-2,1254,432),230,336,fill=(134,225,251,160),width=3)
for i in range(7):
 yy=72+i*28
 d.line((1213,yy,1276,yy),fill=(24,142,176,100),width=1)
 d.line((1222,yy,1244+(i%3)*12,yy),fill=(81,226,237,210),width=2)
line_text(d,(1186,25),'EPRV / 2026',13,(125,205,220,255),True)
d.line((0,H-17,W,H-17),fill=(41,103,133,90),width=1)
BASE.alpha_composite(static)

def dynamic_frame(i,n):
 im=BASE.copy();layer=Image.new('RGBA',(W,H));d=ImageDraw.Draw(layer,'RGBA')
 theta=2*math.pi*i/n
 cx,cy=1053,215
 # transparent wedge, radar scan line
 r=241
 wedge=[(cx,cy)]
 for k in range(33):
  a=theta-math.pi/5+(math.pi/5)*k/32
  wedge.append((cx+r*math.cos(a),cy+r*math.sin(a)))
 d.polygon(wedge,fill=(20,224,183,10))
 ex=cx+r*math.cos(theta);ey=cy+r*math.sin(theta)
 d.line((cx,cy,ex,ey),fill=(78,248,221,130),width=2)
 # ranging ticks at different radii
 for rr in (160,202,240):
  tx=cx+rr*math.cos(theta);ty=cy+rr*math.sin(theta)
  d.ellipse((tx-3,ty-3,tx+3,ty+3),fill=(117,248,228,200))
 # Lissajous spectrum miniature lower right
 ox,oy=813,392
 d.rounded_rectangle((788,366,1300,413),radius=9,fill=(4,20,34,160),outline=(43,129,151,155))
 line_text(d,(800,374),'CLOSED-LOOP TELEMETRY  /  LIVE SIGNAL',10,(148,225,231,230),True)
 p=[]
 for k in range(465):
  z=k/465
  val=(math.sin(z*12*math.pi+theta*2)*.44+math.sin(z*34*math.pi-theta*.7)*.11+math.sin(z*4*math.pi+theta)*.23)
  p.append((800+k,397-11*val))
 d.line(p,fill=(100,238,212,210),width=2,joint='curve')
 # moving optical data probe
 px=800+((i*9)%465);d.line((px,386,px,409),fill=(120,229,248,100),width=1)
 # tiny operation bit
 d.ellipse((237,43,247,53),fill=(69,228,212,60+i%4*30))
 im.alpha_composite(layer)
 return im.convert('RGB')

def render_hero():
 n=26
 frames=[]
 for i in range(n):
  frames.append(dynamic_frame(i,n))
  if i==8:frames[-1].save(OUT/'hero-preview.jpg',quality=92,optimize=True)
 out=OUT/'research-radar-cinematic.gif'
 # Individual palettes with frame-delta optimizations.
 frames[0].save(out,save_all=True,append_images=frames[1:],duration=120,loop=0,optimize=False,disposal=2,colors=128)
 print('HERO',out,out.stat().st_size)

# Visual cards: repository-derived evidence where available. Assets saved locally and never presented as raw measurements.
PROJECTS=[
 {'slug':'exohspec','title':'EXOhSPEC','desc':'INSTRUMENT STABILITY','slugText':'THERMAL + ACTIVE OPTICS','url':'https://raw.githubusercontent.com/Biswajit1999/Master-Thesis-2024/main/figures/06_nine_panel_stacked.png','tone':(54,229,208)},
 {'slug':'finding-earth','title':'FINDING EARTH 2.0','desc':'EXOPLANET CANDIDATE SCREENING','slugText':'CATALOGUES + UNCERTAINTY','url':'https://raw.githubusercontent.com/Biswajit1999/finding-earth-2/main/docs/images/hero.webp','tone':(83,189,251)},
 {'slug':'precision-rv','title':'PRECISION RV','desc':'INSTRUMENT LANDSCAPE','slugText':'SPECTROGRAPHS + CALIBRATION','url':'https://raw.githubusercontent.com/Biswajit1999/eprv-spectrograph-landscape/main/website/public/figures/Precision%20RV%20spectrograph%20github.png','tone':(255,183,113)},
 {'slug':'nasadiya','title':'NASADIYA LIGHTCONE','desc':'COSMIC STRUCTURE + TIME','slugText':'OBSERVED SURVEY DATA','url':'https://raw.githubusercontent.com/Biswajit1999/NASADIYA-LIGHTCONE/main/assets/nasadiya-lightcone-banner.png','tone':(185,165,255)}
]

def load_remote(p):
 if os.environ.get('NO_REMOTE'):return None
 try:
  req=urllib.request.Request(p['url'],headers={'User-Agent':'ResearchProfileRenderer/2026'})
  with urllib.request.urlopen(req,timeout=18) as resp: raw=resp.read(8*1024*1024)
  src=Image.open(io.BytesIO(raw)).convert('RGB');print('SOURCE',p['slug'],src.size);return src
 except Exception as e:print('Source unavailable',p['slug'],type(e).__name__,str(e)[:100]);return None

def card_fallback(slug):
 w,h=720,355; im=stars_and_back(w,h,seed=sum(map(ord,slug)));d=ImageDraw.Draw(im,'RGBA')
 if slug=='exohspec':
  # stylised optical bench and echelle spectrum
  d.polygon([(44,221),(396,170),(652,266),(310,321)],fill=(20,40,53,255),outline=(83,134,163,255))
  for k in range(5):
   x=110+105*k;d.ellipse((x-24,185,x+24,234),fill=(23,39,55,255),outline=(115,178,207,240),width=4)
  for i in range(60):
   x=175+6*i;y=210+math.sin(i/8)*20
   d.line((x,y,x+10,y-4),fill=((42+i*4)%255,90+(i*6)%164,255-i*3,230),width=2)
 elif slug=='finding-earth':
  planet=PLANET.resize((365,365));im.alpha_composite(planet,(350,-65))
 elif slug=='precision-rv':
  for i in range(12):
   yy=100+i*15;col=[(76,219,241,195),(154,146,255,190),(255,173,90,210)][i%3]
   d.arc((110,yy-45,695,yy+38),160,350,fill=col,width=3)
  for i in range(21):
   xx=135+i*22;d.line((xx,70,xx,304),fill=(110,210,232,30+(i%4)*20),width=1)
 else:
  for i in range(13):
   x=65+i*24
   d.line((80,185,x+370,185-(i-6)*14),fill=(94+(i*4),164,244,100),width=2)
  for i in range(250):
   xx=random.Random(i).randrange(50,600);yy=random.Random(i*9).randrange(60,310)
   d.ellipse((xx,yy,xx+1,yy+1),fill=(147,217,249,200))
 return im

def render_card(p):
 ww,hh=720,355
 src=load_remote(p)
 if src:
  # Crop centre and preserve as much of the scientific art as possible.
  s=max(ww/src.width,hh/src.height);sz=(math.ceil(src.width*s),math.ceil(src.height*s))
  src=src.resize(sz,Image.Resampling.LANCZOS)
  x=max(0,(sz[0]-ww)//2);y=max(0,(sz[1]-hh)//2)
  im=src.crop((x,y,x+ww,y+hh)).convert('RGBA')
  im=ImageEnhance.Color(im).enhance(.93)
  im=Image.blend(im,Image.new('RGBA',(ww,hh),(5,14,29,255)),.16)
 else: im=card_fallback(p['slug'])
 shade=Image.new('RGBA',(ww,hh));r=np.zeros((hh,ww,4),dtype=np.uint8)
 r[:,:,:3]=[2,10,23];r[:,:,3]=np.linspace(0,244,hh,dtype='uint8')[:,None]
 shade=Image.fromarray(r,'RGBA');im.alpha_composite(shade)
 d=ImageDraw.Draw(im,'RGBA');t=p['tone']
 d.line((18,18,ww-18,18),fill=(*t,120),width=2)
 d.line((18,18,18,50),fill=(*t,110),width=2)
 d.line((ww-18,hh-50,ww-18,hh-18),fill=(*t,110),width=2)
 d.line((18,hh-18,ww-18,hh-18),fill=(*t,110),width=2)
 d.rounded_rectangle((25,29,220,57),radius=6,fill=(6,23,40,190),outline=(*t,110),width=1)
 line_text(d,(38,36),'RESEARCH NODE  /  0'+str(PROJECTS.index(p)+1),11,t,True,1)
 line_text(d,(30,247),p['title'],36,(244,250,255,255),True)
 line_text(d,(32,292),p['desc'],13,t,True,1.3)
 line_text(d,(32,318),p['slugText'],12,(184,210,222,255))
 d.ellipse((ww-70,hh-84,ww-29,hh-43),outline=(*t,222),width=2)
 d.line((ww-58,hh-64,ww-40,hh-64),fill=(*t,255),width=2)
 d.line((ww-46,hh-70,ww-40,hh-64),fill=(*t,255),width=2)
 d.line((ww-46,hh-58,ww-40,hh-64),fill=(*t,255),width=2)
 path=OUT/(p['slug']+'-research.jpg');im.convert('RGB').save(path,quality=90,optimize=True,subsampling=0)
 print('CARD',path,path.stat().st_size)

if __name__=='__main__':
 render_hero()
 for p in PROJECTS:render_card(p)
