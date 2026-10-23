import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, json, numpy as np; sys.path.insert(0,ROOT + '/scripts'); from mxs import *
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from scipy.ndimage import uniform_filter1d, median_filter
name,f=sys.argv[1],sys.argv[2]
C=json.load(open(f'{ROOT}/analysis/centerline_{name}.json')); X,Z=np.array(C['x']),np.array(C['z'])
T=Track(f,'xz')
# resample at 0.25 ft
s=np.r_[0,np.cumsum(np.hypot(np.diff(X),np.diff(Z)))]; ss=np.arange(0,s[-1],0.25)
x=np.interp(ss,s,X); z=np.interp(ss,s,Z); h=T.h(x,z)
# heading & curvature from smoothed path
xs_=uniform_filter1d(x,81,mode='wrap'); zs_=uniform_filter1d(z,81,mode='wrap')
th=np.unwrap(np.arctan2(np.gradient(zs_),np.gradient(xs_))); kappa=np.gradient(th,0.25)
kappa=uniform_filter1d(kappa,41,mode='wrap')
np.savez(f'{ROOT}/analysis/cl_{name}.npz',s=ss,x=x,z=z,h=h,kappa=kappa,th=th)
n=8; L=ss[-1]/n
fig,axs=plt.subplots(n,1,figsize=(24,3*n))
for i in range(n):
    m=(ss>=i*L)&(ss<(i+1)*L); ax=axs[i]
    ax.plot(ss[m],h[m],'k',lw=.8); ax.set_ylim(h.min()-1,h.max()+1)
    ax2=ax.twinx(); ax2.plot(ss[m],1/np.maximum(np.abs(kappa[m]),1e-3),'r',lw=.5,alpha=.6); ax2.set_ylim(0,200); ax2.set_ylabel('turn R ft',color='r')
    ax.grid(alpha=.3)
plt.tight_layout(); plt.savefig(f'{ROOT}/analysis/clprof_{name}.png',dpi=50)
