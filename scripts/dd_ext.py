import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, json, numpy as np; sys.path.insert(0,ROOT + '/scripts'); from mxs import *
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
T=Track(REF + '/JGMXDrDew/JGMXDrDew','xz')
G=[31,72,125,132,8,43,21,28,29,6,18,15,65,67,110,107,134,131]
fig,axs=plt.subplots(len(G),2,figsize=(26,3.2*len(G)),gridspec_kw=dict(width_ratios=[1,3]))
for k,gi in enumerate(G):
    g=T.gradients[gi]; a=np.array(g['a']); b=np.array(g['b']); u=(b-a)/g['len']
    A=a-u*40; B=b+u*140
    d,h=T.line(*A,*B,step=0.25); d=d-40
    ax=axs[k,1]; ax.plot(d,h,'k'); ax.axvspan(0,g['len'],color='y',alpha=.2); ax.set_aspect('equal'); ax.grid(alpha=.3); ax.set_xticks(np.arange(-40,g['len']+141,10)); ax.tick_params(labelsize=6)
    ax.set_title(f'g{gi} a={np.round(a)} b={np.round(b)} len={g["len"]:.0f}')
    pad=50; bx0,bx1=min(A[0],B[0])-pad,max(A[0],B[0])+pad; bz0,bz1=min(A[1],B[1])-pad,max(A[1],B[1])+pad
    j0,j1,i0,i1=[int(np.clip(v,0,T.size)/T.s) for v in (bx0,bx1,bz0,bz1)]
    ax=axs[k,0]; ax.imshow(LightSource(300,40).hillshade(T.H[i0:i1,j0:j1],vert_exag=3/T.s),cmap='gray',extent=[j0*T.s,j1*T.s,i1*T.s,i0*T.s])
    ax.plot([A[0],B[0]],[A[1],B[1]],'r-'); ax.plot([a[0],b[0]],[a[1],b[1]],'y-',lw=3); ax.plot(*B,'ro')
plt.tight_layout(); plt.savefig(ROOT + '/analysis/dd_ext.png',dpi=32)
