import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, json, numpy as np; sys.path.insert(0,ROOT + '/scripts'); from mxs import *
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
f,out,x0,x1,z0,z1=sys.argv[1],sys.argv[2],*map(float,sys.argv[3:7]); ref=sys.argv[7] if len(sys.argv)>7 else None
T=Track(f,'xz'); j0,j1,i0,i1=[int(v/T.s) for v in (x0,x1,z0,z1)]
H=T.H[i0:i1,j0:j1]; ls=LightSource(300,40)
fig,ax=plt.subplots(figsize=(18,18*(z1-z0)/(x1-x0)))
hs=ls.hillshade(H,vert_exag=4/T.s,dx=1,dy=1)
ax.imshow(hs,cmap='gray',extent=[x0,x1,z1,z0])
ax.imshow(H,cmap='terrain',alpha=0.35,extent=[x0,x1,z1,z0])
cs=ax.contour(np.linspace(x0,x1,H.shape[1]),np.linspace(z0,z1,H.shape[0]),H,levels=np.arange(0.5,14,1.0),colors='k',linewidths=0.3)
if ref and ref!='none':
  C=json.load(open(ROOT + '/analysis/catalog_raw.json'))
  for c in C:
    if c['ref']==ref and x0<c['crest_xz'][0]<x1 and z0<c['crest_xz'][1]<z1: ax.text(*c['crest_xz'],f"g{c['grad']}.{c['idx']}\n{c['height']:.1f}",fontsize=7,color='red',ha='center')
G=parse_gates(f+'/timing_gates')
for i,cp in enumerate(G['cps']):
  L,x,y,z,dx,dy,dz=cp[:7]; ax.plot([x-dx,x+dx],[z-dz,z+dz],'m-',lw=1)
ax.set_xticks(np.arange(x0,x1,20)); ax.set_yticks(np.arange(z0,z1,20)); ax.tick_params(labelsize=7); ax.grid(alpha=.35,color='y'); ax.set_xlim(x0,x1); ax.set_ylim(z1,z0); plt.savefig(out,dpi=int(sys.argv[8]) if len(sys.argv)>8 else 60,bbox_inches='tight')
