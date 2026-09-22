import os,pickle,math
from pathlib import Path
import numpy as np
import moderngl
from PIL import Image
ROOT=Path('/workspace/ha109-3d')
ctx=moderngl.create_standalone_context(backend='egl');ctx.enable(moderngl.DEPTH_TEST)
def norm(v):v=np.array(v,dtype=float);return v/np.linalg.norm(v)
def view(eye,target,up=(0,1,0)):
 f=norm(np.array(target)-eye);s=norm(np.cross(f,up));u=np.cross(s,f);m=np.eye(4);m[0,:3]=s;m[1,:3]=u;m[2,:3]=-f;m[:3,3]=-m[:3,:3]@eye;return m
def ortho(l,r,b,t,n,f):
 return np.array([[2/(r-l),0,0,-(r+l)/(r-l)],[0,2/(t-b),0,-(t+b)/(t-b)],[0,0,-2/(f-n),-(f+n)/(f-n)],[0,0,0,1]])
def perspective(fov,aspect,n,f):
 a=1/math.tan(math.radians(fov)/2);return np.array([[a/aspect,0,0,0],[0,a,0,0],[0,0,(f+n)/(n-f),2*f*n/(n-f)],[0,0,-1,0]])
vertex='''#version 330
in vec3 position;in vec3 normal;in vec3 tint;uniform mat4 mvp;uniform mat4 lightmatrix;out vec3 world;out vec3 N;out vec4 lightpos;out vec3 tintColor;
void main(){world=position;N=normal;tintColor=tint;lightpos=lightmatrix*vec4(position,1);gl_Position=mvp*vec4(position,1);}
'''
frag='''#version 330
in vec3 world;in vec3 N;in vec4 lightpos;in vec3 tintColor;out vec4 color;
uniform vec3 base;uniform vec3 eye;uniform float metallic;uniform float rough;uniform sampler2DShadow shadows;
float visibility(){vec3 p=lightpos.xyz/lightpos.w*.5+.5;float v=0;for(int x=-2;x<=2;x++)for(int y=-2;y<=2;y++)v+=texture(shadows,vec3(p.xy+vec2(x,y)/2048.,p.z-.0006));return v/25.;}
vec3 aces(vec3 x){return clamp((x*(2.51*x+.03))/(x*(2.43*x+.59)+.14),0.,1.);}
void main(){vec3 n=normalize(N);if(!gl_FrontFacing)n=-n;vec3 v=normalize(eye-world);vec3 albedo=pow(base*tintColor,vec3(2.2));vec3 f0=mix(vec3(.035),albedo,metallic);vec3 sum=albedo*(.16+.10*max(n.y,0.));
vec3 dirs[3]=vec3[3](normalize(vec3(-.48,.88,.55)),normalize(vec3(.78,.42,.28)),normalize(vec3(-.2,.34,-1.)));float powers[3]=float[3](1.45,.32,.42);
for(int i=0;i<3;i++){vec3 l=dirs[i];vec3 h=normalize(v+l);float ndl=max(dot(n,l),0.);float ndh=max(dot(n,h),0.);float spec=pow(ndh,mix(260.,8.,sqrt(rough)));float vis=i==0?visibility():1.;sum+=(albedo*(1.-metallic*.55)*ndl*.65+f0*spec*5.)*powers[i]*vis;}
vec3 refl=reflect(-v,n);float strip=pow(max(dot(refl,normalize(vec3(-.48,.74,1.))),0.),mix(125.,6.,rough));float rim=pow(max(dot(refl,normalize(vec3(.7,.45,-.7))),0.),mix(80.,5.,rough));sum+=f0*(strip*3.0+rim*.8);
float micro=.992+.008*sin(world.x*940.)*sin(world.y*710.+world.z*370.);float ao=1.-.16*exp(-max(world.y,0.)*48.);sum*=ao*micro;sum=aces(sum*.94);color=vec4(pow(sum,vec3(1./2.2)),1.);}
'''
program=ctx.program(vertex_shader=vertex,fragment_shader=frag)
depthprog=ctx.program(vertex_shader='''#version 330
in vec3 position;uniform mat4 mvp;void main(){gl_Position=mvp*vec4(position,1);}
''',fragment_shader='''#version 330
void main(){}
''')
with open(ROOT/'scene.pkl','rb') as f:items=pickle.load(f)
geoms=[]
for _,mesh,transform in items:
 p=np.c_[mesh.vertices,np.ones(len(mesh.vertices))]@transform.T;n=mesh.vertex_normals@transform[:3,:3].T
 faces=mesh.faces.reshape(-1);tint=mesh.visual.vertex_colors[:,:3]/255 if mesh.visual.kind=='vertex' else np.ones((len(mesh.vertices),3));verts=np.c_[p[:,:3][faces],n[faces],tint[faces]].astype('f4');buf=ctx.buffer(verts.tobytes());vao=ctx.vertex_array(program,[(buf,'3f 3f 3f','position','normal','tint')]);dvao=ctx.vertex_array(depthprog,[(buf,'3f 24x','position')]);m=mesh.visual.material;geoms.append((vao,dvao,np.array(m.baseColorFactor[:3])/255,float(m.metallicFactor),float(m.roughnessFactor)))
floor=np.array([[-2,-.001,-2,0,1,0],[-2,-.001,2,0,1,0],[2,-.001,2,0,1,0],[-2,-.001,-2,0,1,0],[2,-.001,2,0,1,0],[2,-.001,-2,0,1,0]],'f4');floor=np.c_[floor,np.ones((6,3))].astype('f4');buf=ctx.buffer(floor.tobytes());geoms.append((ctx.vertex_array(program,[(buf,'3f 3f 3f','position','normal','tint')]),ctx.vertex_array(depthprog,[(buf,'3f 24x','position')]),np.array([.74,.77,.81]),0.,.88))
light=ortho(-.35,.35,-.32,.32,.01,3)@view(np.array([-.7,1.15,.85]),np.array([0,.11,0]))
shadow=ctx.depth_texture((2048,2048));shadow.compare_func='<=';shadow.repeat_x=False;shadow.repeat_y=False;sfbo=ctx.framebuffer(depth_attachment=shadow);sfbo.use();sfbo.clear(depth=1);ctx.viewport=(0,0,2048,2048);depthprog['mvp'].write(light.T.astype('f4').tobytes())
for _,vao,*_ in geoms:vao.render()
W,H=1600,1600;ms_color=ctx.renderbuffer((W,H),components=3,samples=4);ms_depth=ctx.depth_renderbuffer((W,H),samples=4);fbo=ctx.framebuffer(ms_color,ms_depth);resolved=ctx.simple_framebuffer((W,H),components=3);fbo.use();ctx.viewport=(0,0,W,H);shadow.use(0);program['shadows']=0;program['lightmatrix'].write(light.T.astype('f4').tobytes())
for name,az,el in [('front',0,1),('hero',31,13),('rear',180,2),('side',90,2),('rear-detail',180,0),('top',180,90),('front-detail',0,0),('left-detail',-55,5),('left-side',-90,2),('stand-detail',90,0)]:
 a=math.radians(az);b=math.radians(el);eye=np.array([.78*math.sin(a)*math.cos(b),.12+.78*math.sin(b),.78*math.cos(a)*math.cos(b)]);target=np.array([0,.115,0]);mvp=perspective(31,1,.05,4)@view(eye,target)
 if name=='rear-detail':
  eye=np.array([-.041,.176,-.68]); target=np.array([-.041,.176,0]);mvp=ortho(-.102,.102,-.102,.102,.01,2)@view(eye,target)
 if name=='top':
  eye=np.array([0,.8,0]);target=np.array([0,.15,0]);mvp=ortho(-.157,.157,-.157,.157,.01,2)@view(eye,target,(0,0,1))
 if name=='front-detail':
  eye=np.array([0,.171,.68]); target=np.array([0,.171,0]);mvp=ortho(-.15,.15,-.15,.15,.01,2)@view(eye,target)
 if name=='left-detail':
  target=np.array([0,.17,0]); eye=target+np.array([-.7,.08,.49]);mvp=ortho(-.205,.205,-.205,.205,.01,2)@view(eye,target)
 if name=='stand-detail':
  target=np.array([0,.097,.030]);eye=np.array([.8,.097,.030]);mvp=ortho(-.115,.115,-.115,.115,.01,2)@view(eye,target)
 fbo.clear(.935,.945,.96,depth=1);program['mvp'].write(mvp.T.astype('f4').tobytes());program['eye'].value=tuple(eye)
 for vao,_,color,metal,rough in geoms:
  program['base'].value=tuple(color);program['metallic']=metal;program['rough']=rough;vao.render()
 ctx.copy_framebuffer(resolved,fbo);im=Image.frombytes('RGB',(W,H),resolved.read(components=3)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
 if name=='rear-detail': im=im.crop((0,375,1600,1200))
 if name=='front-detail': im=im.crop((0,475,1600,1100))
 if name=='left-detail': im=im.crop((0,485,1600,1070))
 if name=='stand-detail': im=im.crop((260,115,1340,1510))
 im.save(ROOT/(name+'.png'));print('Rendered',name,flush=True)
