import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, json, numpy as np; sys.path.insert(0,ROOT + '/scripts'); from mxs import *
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
f=sys.argv[1]; name=sys.argv[2]
T=Track(f,'xz'); C=json.load(open(ROOT + '/analysis/catalog_raw.json'))
grads=sorted({c['grad'] for c in C if c['ref']==name})
fig,axs=plt.subplots(len(grads),1,figsize=(26,2.6*len(grads)))
for ax,gi in zip(axs,grads):
    g=T.gradients[gi]; d,h=T.line(*g['a'],*g['b'],step=0.25)
    ax.plot(d,h,'k',lw=1); P=g['pts']; ax.plot(P[:,1],P[:,2]-(P[0,2]-h[0]) if abs(P[0,2]-h[0])>3 else P[:,2],'r.',ms=2)
    ax.set_aspect('equal'); ax.set_title(f'{name} g{gi} a={np.round(g["a"])} b={np.round(g["b"])} L={g["len"]:.0f}',fontsize=9)
    ax.set_xticks(np.arange(0,d[-1],20)); ax.grid(alpha=.4); ax.tick_params(labelsize=6)
plt.tight_layout(); plt.savefig(f'{ROOT}/analysis/gprof_{name}.png',dpi=45)
