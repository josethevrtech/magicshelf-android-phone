"""Original thin-bezel phone, authored for an uncropped 720×1600 display.
DPH2 geometry in metres. No third-party model assets are used.
"""
from pathlib import Path
import math,struct,json
import cairo
base=Path(__file__).resolve().parents[1]
out=base/'assets/android-phone';out.mkdir(parents=True,exist_ok=True)
# sRGB material colors. Alpha is the renderer's emission mask.
materials=[('graphite',(.14,.17,.20),.32,.85),('chamfer',(.48,.53,.57),.24,.95),
 ('glass',(.015,.019,.024),.12,.05),('back',(.075,.093,.108),.48,.25),
 ('lens',(.016,.040,.065),.12,.35),('trim',(.28,.34,.39),.24,.85),
 ('home',(.63,.80,.82),.40,.05)]
groups=[[] for _ in materials]
def triangle(a,b,c,material):
 u=[b[k]-a[k] for k in range(3)];v=[c[k]-a[k] for k in range(3)]
 n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
 length=math.sqrt(sum(t*t for t in n)) or 1;n=[t/length for t in n]
 groups[material].extend((*p,*n,.5,.5) for p in (a,b,c))
def ring(w,h,r,z,x=0,y=0):
 points=[]
 for cx,cy,start in [(w-r,h-r,0),(-w+r,h-r,90),(-w+r,-h+r,180),(w-r,-h+r,270)]:
  for i in range(17):
   a=math.radians(start+90*i/16);points.append((x+cx+r*math.cos(a),y+cy+r*math.sin(a),z))
 return points

def join(a,b,m):
 for i in range(len(a)):
  j=(i+1)%len(a);triangle(a[i],a[j],b[j],m);triangle(a[i],b[j],b[i],m)
def face(a,m,reverse=False):
 center=tuple(sum(p[k] for p in a)/len(a) for k in range(3))
 for i in range(len(a)):
  b,c=a[i],a[(i+1)%len(a)]
  triangle(center,c,b,m) if reverse else triangle(center,b,c,m)
# Continuous bevels and a dark, slightly metallic frame.
back=ring(.0377,.0867,.0085,-.0042)
backbevel=ring(.0385,.0875,.0093,-.0034)
frontbevel=ring(.0385,.0875,.0093,.0033)
front=ring(.0377,.0867,.0085,.0041)
face(back,3,True);join(back,backbevel,1);join(backbevel,frontbevel,0);join(frontbevel,front,1);face(front,2)
# Keep glass rectangular at the active screen: no pixels lost to rounded corners.
# The settings button is entirely below Android's own navigation bar.
face(ring(.0115,.00085,.0008,.00432,y=-.0827),6)
face(ring(.006,.00055,.0005,.00432,y=.0832),0)
face(ring(.00135,.00135,.00135,.00433,x=.012,y=.0832),4)
# Camera bump and lens rings, visible when the device is turned over.
a=ring(.011,.021,.005,-.00421,x=-.021,y=.056)
b=ring(.0105,.0205,.0045,-.0057,x=-.021,y=.056)
join(b,a,0);face(b,3,True)
for y in [.046,.066]:
 outer=ring(.0067,.0067,.0067,-.0058,x=-.021,y=y)
 inner=ring(.0057,.0057,.0057,-.0061,x=-.021,y=y)
 join(inner,outer,5);face(inner,4,True)
 face(ring(.0021,.0021,.0021,-.00611,x=-.022,y=y+.0007),2,True)
# Edge buttons, authored as small beveled bars.
for x,y,h in [(.0385,.025,.009),(-.0385,.034,.014)]:
 sign=1 if x>0 else -1
 corners=[(x,y-h,-.0018),(x+sign*.001,y-h,-.0018),(x+sign*.001,y+h,-.0018),(x,y+h,-.0018)]
 cap=[(px,py,.0018) for px,py,_ in corners];join(corners,cap,0);face(cap,1)
with (out/'device.mesh').open('wb') as f:
 f.write(b'DPH2');f.write(struct.pack('<II',len(groups),sum(map(len,groups))))
 first=0
 for group,(_,_,rough,metal) in zip(groups,materials):
  f.write(struct.pack('<IIff',first,len(group),rough,metal));first+=len(group)
 for group in groups:
  for vertex in group:f.write(struct.pack('<8f',*vertex))
for i,(name,color,rough,metal) in enumerate(materials):
 (out/f'body-{i}.rgba').write_bytes(struct.pack('<II',1,1)+bytes([round(v*255) for v in color]+[0]))
(out/'model-info.json').write_text(json.dumps({'name':'Android Phone','author':'Original geometry for this installation','screen':[720,1600],'body_mm':[77,175,8.4],'triangles':sum(map(len,groups))//3},indent=2)+'\n')
# Vector-drawn taskbar icon: a simple phone silhouette matching this device.
s=cairo.ImageSurface(cairo.FORMAT_ARGB32,256,256);c=cairo.Context(s)
def rounded(x,y,w,h,r,color):
 c.new_sub_path()
 for xx,yy,start in [(x+w-r,y+r,-90),(x+w-r,y+h-r,0),(x+r,y+h-r,90),(x+r,y+r,180)]:
  c.arc(xx,yy,r,math.radians(start),math.radians(start+90))
 c.close_path();c.set_source_rgb(*color);c.fill()
rounded(69,12,118,232,23,(.61,.69,.75));rounded(74,17,108,222,19,(.08,.11,.14))
rounded(82,31,92,184,5,(.13,.53,.57))
c.set_source_rgb(.60,.89,.86);c.set_line_width(5)
for yy in [73,99,125]:c.move_to(99,yy);c.line_to(157,yy);c.stroke()
rounded(111,224,34,4,2,(.72,.88,.89))
s.write_to_png(str(base/'android-phone-icon.png'))
print('Android Phone:',sum(map(len,groups))//3,'triangles')
