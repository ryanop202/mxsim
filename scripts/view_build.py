import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, numpy as np; sys.path.insert(0,ROOT + '/scripts')
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.colors import LightSource, ListedColormap
H=np.load(ROOT + '/legacy_mx/build/H.npy'); T=np.load(ROOT + '/legacy_mx/build/tiles.npy'); s=0.4; size=(H.shape[0]-1)*s
crop=[float(v) for v in sys.argv[2].split(',')] if len(sys.argv)>2 else [0,size,0,size]
x0,x1,z0,z1=crop; j0,j1,i0,i1=[int(v/s) for v in crop]; st=max(1,int((j1-j0)/2400))
Hc=H[i0:i1:st,j0:j1:st]
fig,ax=plt.subplots(1,2 if len(sys.argv)<=3 else 1,figsize=(28 if len(sys.argv)<=3 else 18,14*(z1-z0)/(x1-x0)+1))
ax=np.atleast_1d(ax)
hs=LightSource(315,35).hillshade(Hc,vert_exag=2.5/(s*st))
ax[0].imshow(hs,cmap='gray',extent=[x0,x1,z1,z0]); ax[0].imshow(Hc,cmap='terrain',alpha=.35,extent=[x0,x1,z1,z0])
ax[0].contour(np.linspace(x0,x1,Hc.shape[1]),np.linspace(z0,z1,Hc.shape[0]),Hc,levels=np.arange(-20,45,2.5),colors='k',linewidths=.25)
if len(ax)>1:
    cm=ListedColormap(['#7aa35a','#8b5a2b','#c0392b','#f1d48a','#b0a090','#6e3b1f','#2e86c1','#8e44ad'])
    ax[1].imshow(T[int(i0/2):int(i1/2),int(j0/2):int(j1/2)],cmap=cm,vmin=-.5,vmax=7.5,extent=[x0,x1,z1,z0],interpolation='nearest')
    ax[1].set_title('tiles: grass/dirt/jump/sand/sxfloor/sxjump/whoops/berm')
plt.tight_layout(); plt.savefig(sys.argv[1],dpi=55)
