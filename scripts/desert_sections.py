"""MX sections along the Desert Sand centerline (track-following), with on-track QA."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, json, re, numpy as np; sys.path.insert(0,ROOT + '/scripts'); from mxs import *
from mx_faces import faces, units
from scipy.ndimage import distance_transform_edt
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
f=REF + '/JGMXDesertSand/JGMXDesertSand'; T=Track(f,'xz')
D=np.load(ROOT + '/analysis/cl_Desert.npz'); s,x,z,h,k=D['s'],D['x'],D['z'],D['h'],D['kappa']
# on-track mask from sand decals
cell=2.0; n=int(T.size/cell)+1; mask=np.zeros((n,n),bool)
for l in open(f+'/decals'):
    if 'sand.png' not in l or 'sandoff' in l: continue
    v=[float(q) for q in re.findall(r'-?\d+\.?\d*',l.split('@')[0])]; xx,zz,size=v[0],v[1],v[3]
    if 0<=xx<T.size and 0<=zz<T.size:
        r=int(size/2/cell); ci,cj=int(zz/cell),int(xx/cell); mask[max(0,ci-r):ci+r+1,max(0,cj-r):cj+r+1]=True
on=mask[(z/cell).astype(int).clip(0,n-1),(x/cell).astype(int).clip(0,n-1)]
F,ang=faces(h); U=units(h,F)
cands=[]
for u in U:
    if u['kind'] not in ('jump','table','step-up','step-down-from-jump','roller'): continue
    if u['up']['H']<2.0: continue
    a=max(0,u['i0']-int(40/0.25)); b=min(len(h)-1,u['i1']+int(50/0.25))
    if b-a<int(40/0.25): continue
    if on[a:b].mean()<0.95: continue
    R=1/np.maximum(np.abs(k[a:b]),1e-4)
    cands.append(dict(kind=u['kind'],s0=float(s[a]),s1=float(s[b]),i0=a,i1=b,Rmin=float(R.min()),up=u['up'],down=u['down'],top=u['top']))
# de-duplicate overlapping windows (keep first)
sel=[]
for c in cands:
    if all(c['s0']>=q['s1'] or c['s1']<=q['s0'] for q in sel): sel.append(c)
print('candidates',len(cands),'kept',len(sel))
out={}
fig,axs=plt.subplots(len(sel),2,figsize=(24,3*len(sel)),gridspec_kw=dict(width_ratios=[1,3]))
for j,c in enumerate(sel):
    a,b=c['i0'],c['i1']; sid=f"ds_s{int(c['s0'])}_{c['kind'].split('-')[0]}"
    prof=h[a:b+1]-h[a]
    out[sid]=dict(ref='Desert',source='decal-traced centerline',s0=c['s0'],s1=c['s1'],step=0.25,length=float((b-a)*0.25),prof=np.round(prof,3).tolist(),
                  net=float(prof[-1]),hmax=float(prof.max()),Rmin_path=c['Rmin'],kind=c['kind'],
                  up=dict(L=c['up']['L'],H=c['up']['H'],amax=c['up']['amax'],lip=c['up']['lip']),
                  down=(dict(L=c['down']['L'],H=c['down']['H'],amax=c['down']['amax']) if c['down'] else None),top=c['top'],
                  xz=[[float(x[i]),float(z[i])] for i in range(a,b+1,40)])
    ax=axs[j,1]; ax.plot(s[a:b+1]-s[a],prof,'k'); ax.set_aspect('equal'); ax.grid(alpha=.3); ax.set_title(f"{sid} Rmin={c['Rmin']:.0f} up H{c['up']['H']:.1f} max{c['up']['amax']:.0f}",fontsize=9)
    pad=40; bx0,bx1=x[a:b].min()-pad,x[a:b].max()+pad; bz0,bz1=z[a:b].min()-pad,z[a:b].max()+pad
    j0,j1,i0,i1=[int(np.clip(v,0,T.size)/T.s) for v in (bx0,bx1,bz0,bz1)]
    ax=axs[j,0]; ax.imshow(LightSource(300,40).hillshade(T.H[i0:i1,j0:j1],vert_exag=3/T.s),cmap='gray',extent=[j0*T.s,j1*T.s,i1*T.s,i0*T.s]); ax.plot(x[a:b],z[a:b],'r-'); ax.plot(x[b],z[b],'ro')
plt.tight_layout(); plt.savefig(ROOT + '/analysis/desert_sections.png',dpi=30)
for sid,v in out.items(): print(f"{sid:22s} L{v['length']:5.0f} net{v['net']:+6.1f} hmax{v['hmax']:5.1f} Rmin{v['Rmin_path']:5.0f} up H{v['up']['H']:.1f} L{v['up']['L']:.0f} max{v['up']['amax']:.0f} lip{v['up']['lip']:.0f} top {v['top']}")
lib=json.load(open(ROOT + '/lib/library.json')); lib['mx_desert_sections']=out
json.dump(lib,open(ROOT + '/lib/library.json','w'),default=float)
