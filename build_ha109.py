"""Photo-guided HA109 projector reconstruction. Internal units: millimetres."""
import math, pickle
from pathlib import Path
import numpy as np
import trimesh
import manifold3d as mf

ROOT=Path('/workspace'); OUT=ROOT/'ha109-3d'; OUT.mkdir(exist_ok=True)
scene=trimesh.Scene(); items=[]
def mat(name,c,m=0,r=.35): return trimesh.visual.material.PBRMaterial(name=name,baseColorFactor=c,metallicFactor=m,roughnessFactor=r)
BODY=mat('Lavender pearl housing',[190,179,229,255],.015,.31)
TOP=mat('Gloss lavender lid',[218,206,246,255],.0,.14)
STAND=mat('Powder coated lavender stand',[205,192,235,255],.035,.32)
TRAY=mat('Stand tray satin inset',[202,203,220,255],.045,.40)
BLACK=mat('Charcoal glass and recess',[13,14,18,255],.02,.18)
HOLE=mat('Deep internal shadow',[4,5,8,255],0,.68)
SILVER=mat('Machined aluminium',[165,171,189,255],.86,.25)
LENS=mat('Multicoated projector glass',[26,26,68,255],.25,.065)
VIOLET=mat('Violet cyan optical coating',[76,28,132,255],.32,.08)
CYAN=mat('Cyan optical coating',[15,125,154,255],.27,.09)
SEAM=mat('Housing seam',[117,120,142,255],.05,.55)
PATTERN=mat('Top lid pearl pattern',[221,220,243,255],.0,.22)
HILITE=mat('Lens softbox highlight',[203,220,244,255],.05,.07)

def rr(w,h,r,n=18):
 pts=[]
 for cx,cy,start in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
  for t in np.linspace(start,start+90,n,endpoint=False):
   a=math.radians(t); pts.append((cx+r*math.cos(a),cy+r*math.sin(a)))
 return np.array(pts)
def prism(w,h,r,d,axis='z',pos=(0,0,0)):
 m=mf.CrossSection([rr(w,h,r)]).extrude(d).translate((0,0,-d/2))
 if axis=='x': m=m.rotate((0,90,0))
 if axis=='y': m=m.rotate((-90,0,0))
 return m.translate(pos)
def disc(rad,depth,pos,axis='z',inner=0,segments=96):
 m=mf.Manifold.cylinder(depth,rad,rad,segments,True)
 if inner: m=m-mf.Manifold.cylinder(depth+2,inner,inner,segments,True)
 if axis=='x': m=m.rotate((0,90,0))
 if axis=='y': m=m.rotate((-90,0,0))
 return m.translate(pos)
def rounded_prism(w,h,r,d,b=1.5):
 layers=[]; b=min(b,d/2-.01)
 for t in np.linspace(0,math.pi/2,7):
  inset=b*(1-math.sin(t)); z=-d/2+b*(1-math.cos(t)); layers.append((z,inset))
 for t in np.linspace(math.pi/2,0,7):
  inset=b*(1-math.sin(t)); z=d/2-b*(1-math.cos(t)); layers.append((z,inset))
 outline=[rr(w-2*i,h-2*i,max(r-i,.1),18) for _,i in layers]; n=len(outline[0]); v=[]
 for (z,_),p in zip(layers,outline): v.extend([(x,y,z) for x,y in p])
 f=[]
 for k in range(len(layers)-1):
  for i in range(n): j=(i+1)%n; a=k*n+i; c=k*n+j; f += [(a,c,c+n),(a,c+n,a+n)]
 v += [(0,0,-d/2),(0,0,d/2)]; lo=len(v)-2; hi=len(v)-1
 for i in range(n):
  j=(i+1)%n; f += [(lo,j,i),(hi,(len(layers)-1)*n+i,(len(layers)-1)*n+j)]
 mesh=trimesh.Trimesh(v,f,process=True); mesh.fix_normals(); return mf.Manifold(mf.Mesh(np.asarray(mesh.vertices,np.float32),np.asarray(mesh.faces,np.uint32)))
def add(name,m,material):
 if isinstance(m,mf.Manifold):
  mm=m.to_mesh(); mesh=trimesh.Trimesh(mm.vert_properties[:,:3],mm.tri_verts,process=True)
 else: mesh=m
 assert len(mesh.faces)>0, name
 mesh.fix_normals(); mesh=trimesh.graph.smooth_shade(mesh,angle=math.radians(38)); mesh.visual=trimesh.visual.TextureVisuals(material=material); mesh.vertices/=1000
 scene.add_geometry(mesh,node_name=name,geom_name=name); items.append((name,mesh,np.eye(4)))

def sector_mesh(cx,cy,r0,r1,a0,a1,z,plane='xy',segments=64):
 """Thin annular sector used for lid reliefs and optical reflections."""
 ang=np.linspace(math.radians(a0),math.radians(a1),segments); v=[]
 for r in (r0,r1):
  for a in ang:
   p=(cx+r*math.cos(a),cy+r*math.sin(a))
   v.append((p[0],p[1],z) if plane=='xy' else (p[0],z,p[1]))
 f=[]
 for i in range(segments-1): f += [(i,i+1,segments+i+1),(i,segments+i+1,segments+i)]
 return trimesh.Trimesh(v,f,process=False)

# Low tray stand: rounded base, recessed inner platform and twin pivot arms.
base=rounded_prism(314,246,22,12,2.2).rotate((-90,0,0)).translate((0,6,0)); add('STAND / rounded base',base,STAND)
tray=rounded_prism(299,231,18,1.0,.45).rotate((-90,0,0)).translate((0,12,0)); add('Stand inset tray',tray,STAND)
def bezier(a,b,c,d):
 return [(1-t)**3*np.array(a)+3*(1-t)**2*t*np.array(b)+3*(1-t)*t*t*np.array(c)+t**3*np.array(d) for t in np.linspace(0,1,18,endpoint=False)]
for side in (-1,1):
 # Local horizontal coordinate is -Z: top semicircle, raked stem, curved heel.
 # Tangent semicircular head; straight raked sides and two concave root fillets.
 a=math.radians(158); left=(19*math.cos(a),165+19*math.sin(a))
 a=math.radians(-22); right=(19*math.cos(a),165+19*math.sin(a))
 poly=bezier((-89,11.8),(-81,11.8),(-79,17),(-75,27))
 poly+=bezier((-75,27),(-56,75),(-37,123),left)
 poly += [(19*math.cos(t),165+19*math.sin(t)) for t in np.linspace(math.radians(158),math.radians(-22),96,endpoint=False)]
 poly+=bezier(right,(0,115),(-21,67),(-36,30))
 poly+=bezier((-36,30),(-41,17),(-32,11.8),(-21,11.8))
 poly=np.array(poly)
 profile=mf.CrossSection([poly[::-1]])
 # Rounded edge across arm thickness using overlapping eased profile layers.
 layers=[]
 for t in np.linspace(0,math.pi/2,12):
  inset=.85*(1-math.cos(t));depth=4.7+1.7*math.sin(t)
  layers.append(profile.offset(-inset,circular_segments=64).extrude(depth).translate((0,0,-depth/2)))
 arm=mf.Manifold.batch_boolean(layers,mf.OpType.Add).rotate((0,90,0)).translate((side*149,0,0))
 pocket=disc(16.5,1.4,(side*152.1,165,0),'x')
 arm=arm-pocket
 arm=arm.scale((1,1,1/1.2))
 add('Pivot arm rounded head and curved heel '+str(side),arm,STAND)
 add('Pivot axle '+str(side),disc(12.5,6,(side*144,165,0),'x'),STAND)
 cap=rounded_prism(31.8,31.8,15.9,.7,.28).rotate((0,90,0)).translate((side*151.6,165,0)).scale((1,1,1/1.2))
 add('Pivot flush inset cap '+str(side),cap,STAND)

# Main body with real perforations. Body centre Y=170, front +Z.
def body_loft():
 # Rounded XZ footprint, independent bottom chamfer and softened upper rim.
 levels=[(117,266,210,18),(118,270,214,20),(130,286,230,26),(131,286,230,26),(220,286,230,26),(222,284,228,25)]
 v=[]; f=[]; n=len(rr(286,230,26))
 for y,w,d,r in levels: v.extend((x,y,-z) for x,z in rr(w,d,r))
 for k in range(len(levels)-1):
  for i in range(n):
   j=(i+1)%n; a=k*n+i; b=k*n+j; f.extend([(a,b,b+n),(a,b+n,a+n)])
 v.extend([(0,levels[0][0],0),(0,levels[-1][0],0)])
 for i in range(n):
  j=(i+1)%n; f.extend([(len(v)-2,j,i),(len(v)-1,(len(levels)-1)*n+i,(len(levels)-1)*n+j)])
 m=trimesh.Trimesh(v,f,process=True); m.fix_normals()
 return mf.Manifold(mf.Mesh(np.array(m.vertices,dtype=np.float32),np.array(m.faces,dtype=np.uint32)))
shell=body_loft()-prism(278,222,23,96,'y',(0,171,0))
cuts=[]
# Circular ventilation fields on both sides.
for side in (-1,1):
 for y in np.linspace(146,212,10):
  for z in np.linspace(30 if side==-1 else 35,72 if side==-1 else 87,8):
   cuts.append(disc(1.65,14,(side*141,float(y),float(z)),'x',segments=24))
# Side horizontal intake beside the AC socket.
for y in np.linspace(139,186,10): cuts.append(prism(25,2.6,1.1,14,'x',(-141,float(y),-80)))
# Deep figure-eight power inlet behind its separate recessed mounting plate.
cuts.append(prism(20,36,3,15,'x',(-141,163,-43)))
# Rear wide grille: staggered horizontal capsules.
for row,y in enumerate(np.linspace(187,133,10)):
 # Coordinates run left-to-right as seen from the rear (world -X).
 intervals=[(0,69),(74,150)] if row==0 else ([(0,33),(37,70),(74,105),(109,150)] if row%2 else [(0,69),(74,150)])
 for a,b in intervals:
  cuts.append(prism(b-a,3.7,1.6,17,'z',(31-(a+b)/2,float(y),-113)))
shell=mf.Manifold.batch_boolean([shell]+cuts,mf.OpType.Subtract); add('BODY / rounded lavender shell with through vents',shell,BODY)
add('Internal equipment shadow',prism(270,210,22,84,'y',(0,170,0)),HOLE)
# Dark baffles directly behind the ventilation fields add the same physical
# depth visible in the reference product instead of pale, flat-looking holes.

# Glossy top lid and subtle seam.
lid=rounded_prism(288,232,27,5,1.6).rotate((-90,0,0)).translate((0,224.5,0))
# Button opening remains circular after the overall depth correction below.
recess=disc(18.7,4,(-103,227,-82),'y').scale((1,1,1/1.2)).translate((0,0,-82+82/1.2))
lid=lid-recess
add('TOP / glossy white lid',lid,TOP)
seam=(mf.CrossSection([rr(285,229,25.5)])-mf.CrossSection([rr(284.4,228.4,25.2)])).extrude(.25).rotate((-90,0,0)).translate((0,222.1,0)); add('Top lid perimeter seam',seam,SEAM)
add('Power recessed shadow',disc(18.5,.3,(-103,225.2,-82),'y'),SEAM)
add('Power button',rounded_prism(28.4,28.4,14.2,1.2,.5).rotate((-90,0,0)).translate((-103,225.9,-82)),TOP)
bezel=trimesh.creation.torus(major_radius=16.4,minor_radius=1.15,major_sections=128,minor_sections=24)
bezel.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[1,0,0]));bezel.apply_translation([-103,226.6,-82]);add('Power rounded bezel',bezel,TOP)
iconmat=mat('Subtle embossed power symbol',[177,178,198,255],.05,.35)
add('Power icon open ring',sector_mesh(-103,-82,4.1,5.2,130,410,226.53,'xz'),iconmat)
add('Power icon stem',prism(1.3,6.0,.6,.15,'y',(-103,226.55,-78.8)),iconmat)
# Very low contrast printed quarter-circle bands, not raised grooves.
pearl=mat('Tone on tone broad lid pattern',[208,195,240,255],0,.19)
for side in (-1,1):
 cx,cz=110*side,88*side
 shape=sector_mesh(cx,cz,70,113,180 if side==1 else 0,270 if side==1 else 90,227.012,'xz',128)
 shape.vertices[:,2]=cz+(shape.vertices[:,2]-cz)/1.2
 add('Top pearl quarter band '+str(side),shape,pearl)
 # Tangential continuations run to the top/side perimeter.
 for x,z,w,d in [(cx-side*91.5,cz+side*12.7,43,25.4),(cx+side*15.8,cz-side*76.25,31.6,43/1.2)]:
  add('Top pearl band continuation '+str(side)+str(x),prism(w,d,.1,.012,'y',(x,227.012,z)),pearl)
rim=(mf.CrossSection([rr(281,225,24)])-mf.CrossSection([rr(280.5,224.5,23.75)])).extrude(.018).rotate((-90,0,0)).translate((0,227.015,0))
add('Top inset hairline perimeter',rim,mat('Top perimeter soft grey',[202,203,221,255],.05,.35))

# Front decorative inset, optics, sensor and focus wheel.
front_panel=rounded_prism(186,84,41.9,0.4,.12).translate((2,173,115.05)); add('Front soft inset panel',front_panel,BODY)
add('Front panel outline', (mf.CrossSection([rr(186,84,41.9)])-mf.CrossSection([rr(185.4,83.4,41.6)])).extrude(.12).translate((2,173,115.3)), SEAM)
add('Lens black mount',disc(43,3,(-70,173,116.3),'z'),BLACK)
trim=mat('Lens lavender polished rim',[179,178,232,255],.65,.19)
def optical_ring(name,r,tube,z,material):
 m=trimesh.creation.torus(major_radius=r,minor_radius=tube,major_sections=192,minor_sections=24)
 m.apply_translation([-70,173,z]);add(name,m,material)
optical_ring('Lens rounded lavender bezel',40.5,1.65,118.0,trim)
optical_ring('Lens fine inner rim',38.1,.65,118.3,SILVER)
add('Lens recessed black barrel',disc(37.6,2.8,(-70,173,117.7),'z',28),BLACK)
optical_ring('Lens inner rolled lip',33.6,2.1,118.8,BLACK)
optical_ring('Lens glass retaining ring',28.9,.9,118.9,BLACK)
def dome(cx,cy,r,depth,z,material,name):
 n=128; rings=22; v=[(cx,cy,z+depth)]; f=[]
 for k in range(1,rings+1):
  rr0=r*k/rings; zz=z+depth*(1-(rr0/r)**2)
  for a in np.linspace(0,math.tau,n,endpoint=False): v.append((cx+rr0*math.cos(a),cy+rr0*math.sin(a),zz))
 for i in range(n): f.append((0,1+i,1+(i+1)%n))
 for k in range(rings-1):
  a=1+k*n; b=a+n
  for i in range(n): j=(i+1)%n; f += [(a+i,b+i,b+j),(a+i,b+j,a+j)]
 add(name,trimesh.Trimesh(v,f,process=False),material)
# Smooth vertex-colour optical coating on real convex geometry. Colour pools
# are an artistic approximation of reference reflections, not emitted light.
dome(-70,173,27.8,2.3,118.0,LENS,'OPTICS / convex multicoated lens')
glass=items[-1][1];p=glass.vertices*1000;xx=(p[:,0]+70)/27.8;yy=(p[:,1]-173)/27.8;rad=np.sqrt(xx*xx+yy*yy)
purple=np.exp(-((xx+.32)**2/.23+(yy-.30)**2/.32))
cyan=np.exp(-((xx-.33)**2/.23+(yy+.28)**2/.25))
halo=.82+.18*np.cos(rad*math.pi*8)
edge=np.clip((1-rad)/.18,0,1);pupil=1-.86*np.exp(-(rad/.18)**4)
rgb=np.array([10.,14.,25.])+edge[:,None]*pupil[:,None]*(purple[:,None]*np.array([155.,57.,207.])+cyan[:,None]*np.array([10.,135.,176.]))*halo[:,None]
glint=np.exp(-((xx+.34)**2/.10+(yy-.35)**2/.08))*edge
rgb+=glint[:,None]*np.array([110.,100.,112.])
glass.visual=trimesh.visual.ColorVisuals(glass,vertex_colors=np.c_[np.clip(rgb,0,255),np.full(len(rgb),255)].astype(np.uint8));glass.visual.material=mat('Optical coating vertex colour',[255,255,255,255],.15,.12)
add('Front IR sensor',disc(9,0.5,(101,207,115.25),'z'),BLACK)
# Ribbed focus wheel visible at front upper-left.
wheelmat=mat('Focus wheel lavender',[161,164,204,255],.18,.36)
wheelrim=prism(287,231,26.5,14,'y',(0,214.5,0))-prism(283,227,24.5,18,'y',(0,214.5,0))
window=mf.Manifold.cube((42,18,43),True).translate((-125,214.5,95))
add('Focus wheel curved backing',wheelrim^window,wheelmat)
for i,a in enumerate(np.linspace(90,180,48)):
 rad=math.radians(a); x=-117+26.9*math.cos(rad);z=89+26.9*math.sin(rad)
 rib=prism(.36,13.2,.16,.5).rotate((0,90-a,0)).translate((x,214.5,z))
 add('Focus wheel curved rib '+str(i),rib,STAND)
for i,x in enumerate(np.linspace(-116,-104.5,13)):
 add('Focus wheel front rib '+str(i),prism(.36,13.2,.16,.5,'z',(x,214.5,115.9)),STAND)
for i,z in enumerate(np.linspace(75,88,14)):
 add('Focus wheel side rib '+str(i),prism(.36,13.2,.16,.5,'x',(-143.9,214.5,z)),STAND)

# Rear connector island: HDMI, audio, USB and indicator.
add('Rear connector island',rounded_prism(140,27,6,0.5,.15).translate((-40,207,-115.1)),BODY)
border=(mf.CrossSection([rr(140,27,6)])-mf.CrossSection([rr(138.8,25.8,5.4)])).extrude(.18).translate((-40,207,-115.52))
add('Rear connector fine rounded outline',border,SEAM)
hdmi=np.array([[-16,-5],[-16,2],[-12,5],[12,5],[16,2],[16,-5],[14,-6],[-14,-6]])
shape=mf.CrossSection([hdmi[::-1]]).offset(.45,circular_segments=32)
add('HDMI shaped socket bezel',shape.extrude(.8).translate((-1,204,-116.1)),BLACK)
add('HDMI recessed inner opening',shape.offset(-1.4).extrude(.15).translate((-1,204,-116.25)),HOLE)
add('HDMI inner tongue',prism(24,1.4,.4,.2,'z',(-1,202,-116.4)),BLACK)
add('Audio rim',disc(5.7,.4,(-37,206,-115.8),'z'),BLACK)
add('Audio inner ring',disc(4.7,.25,(-37,206,-116.1),'z'),SILVER)
add('Audio hole',disc(3.9,.15,(-37,206,-116.3),'z'),HOLE)
add('USB metal surround',prism(29,12,1,.4,'z',(-69,204,-115.8)),SILVER)
add('USB opening',prism(26,9,.6,.2,'z',(-69,204,-116.1)),HOLE)
add('USB tongue',prism(22,2.2,.4,.2,'z',(-69,202,-116.4)),BLACK)
for x in (-77,-72,-67,-62): add('USB contact '+str(x),prism(1.4,2.8,.1,.1,'z',(x,206,-116.4)),SILVER)
add('Rear indicator',disc(1.75,.25,(-91,214,-115.7),'z'),HOLE)
add('Rear control slot',prism(6.3,10,2.7,.35,'z',(-105,207,-115.7)),BLACK)
# Small printed labels represented by vector strokes, visible in any GLB viewer.
glyphs={'H':[[(0,0),(0,4)],[(3,0),(3,4)],[(0,2),(3,2)]],
 'D':[[(0,0),(0,4),(2,4),(3,3),(3,1),(2,0),(0,0)]],
 'U':[[(0,4),(0,.7),(.7,0),(2.3,0),(3,.7),(3,4)]],
 'S':[[(3,4),(0,4),(0,2),(3,2),(3,0),(0,0)]],
 'B':[[(0,0),(0,4),(2.5,4),(3,3),(2.5,2),(0,2)],[(2.5,2),(3,1),(2.5,0),(0,0)]]}
def line_label(name,paths,cx,cy):
 for k,path in enumerate(paths):
  for j,(a,b) in enumerate(zip(path,path[1:])):
   a=np.array(a); b=np.array(b); mid=(a+b)/2; delta=b-a
   bar=prism(float(np.linalg.norm(delta)),.25,.1,.1).rotate((0,0,math.degrees(math.atan2(delta[1],delta[0])))).translate((mid[0],mid[1],0))
   bar=bar.rotate((0,180,0)).translate((cx,cy,-115.6)); add(name+str(k)+'-'+str(j),bar,SEAM)
for label,cx in [('HD',3),('USB',69)]:
 for i,ch in enumerate(label): line_label('Rear label '+ch+str(i),glyphs[ch],cx*-1-i*4+len(label)*2,213)
line_label('Headphone icon',[[(-2,0),(-2,2),(-1,3),(1,3),(2,2),(2,0)],[(-2,0),(-1,0) ],[(1,0),(2,0)]],-37,214)

# AC figure-eight inlet on the right side and rubber feet under the body.
for side in (-1,):
 plate=prism(25,47,3.8,1.8,'x',(-143.3,163,-43))
 apertures=[disc(6.7,6,(-143,yy,-43),'x') for yy in (156.6,169.4)]
 apertures.append(prism(7,12.8,2,6,'x',(-143,163,-43)))
 plate=mf.Manifold.batch_boolean([plate]+apertures,mf.OpType.Subtract)
 add('AC figure eight recessed plate',plate,BLACK)
 add('AC dark inner well',prism(18,34,4,1,'x',(-138.5,163,-43)),HOLE)
 for yy in (156.6,169.4):
  add('AC contact pin '+str(yy),disc(1.05,2.2,(-140,yy,-43),'x'),SILVER)
for x in (-117,117):
 for z in (-92,92): add('Body rubber foot',disc(7,3,(x,115,z),'y'),BLACK)

# Correct near-square top proportions and shift optical centre to the reference.
for name,mesh,_ in items:
 if name.startswith('Power'):
  mesh.vertices[:,2]=-.082+(mesh.vertices[:,2]+.082)/1.2
 mesh.vertices[:,2]*=1.20
 if name.startswith(('Lens','OPTICS')): mesh.vertices[:,0]+=.020
scene.metadata={'description':'HA109 revision 2: rounded horizontal body corners, separate lower chamfer, round-head raked stand and curved heels. Dimensions inferred from images, not production CAD.'}
scene.export(OUT/'ha109-projector.glb')
with open(OUT/'scene.pkl','wb') as f: pickle.dump(items,f)
loaded=trimesh.load(OUT/'ha109-projector.glb',force='scene'); assert len(loaded.geometry)>0; assert np.isfinite(loaded.bounds).all()
print('Exported',len(items),'source objects /',len(loaded.geometry),'GLB meshes;',sum(len(m.faces) for _,m,_ in items),'triangles; bounds',loaded.bounds.tolist())
