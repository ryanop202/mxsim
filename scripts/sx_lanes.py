import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, json, numpy as np; sys.path.insert(0,ROOT + '/scripts')
from mxs import *; from profiles import *
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
R=REF + '/JGSX2026TestTracks/'
name=sys.argv[1]; T=Track(R+name,'xz')
good=[]
for gi,g in enumerate(T.gradients):
    P=g['pts']
    if len(P)<4 or g['len']<15 or P[:,2].max()<1.0: continue
    d,h=T.line(*g['a'],*g['b'],step=0.1)
    ref=np.interp(d,P[:,1],P[:,2])
    err=np.median(np.abs(h-ref)); corr=np.corrcoef(h,ref)[0,1] if h.std()>0.05 else 0
    if corr>0.95 and err<0.35: good.append((gi,g,d,h,err,corr))
print(name,'gradients matching as-built:',len(good),'of',len(T.gradients))
fig,axs=plt.subplots(len(good),1,figsize=(18,2.2*len(good)))
for k,(gi,g,d,h,err,corr) in enumerate(good):
    res,base=analyze(d,h,'sx')
    ax=axs[k] if len(good)>1 else axs
    ax.plot(d,h,'k-',lw=1); P=g['pts']; ax.plot(P[:,1],P[:,2],'r.',ms=3); ax.set_aspect('equal'); ax.set_ylim(-0.5,8.5)
    ax.set_title(f'grad {gi} a={np.round(g["a"],1)} b={np.round(g["b"],1)} len={g["len"]:.1f} err={err:.2f} r={corr:.3f}',fontsize=8)
    for m in res:
        ax.axvline(m['lip_x'],color='g',lw=.5); ax.axvline(m['land_x'],color='b',lw=.5)
        u=m['up']; ax.text(m['crest'],m['height']+0.3,f"{m['height']:.1f}/{(u['lip'] if u else 0):.0f}°",fontsize=6,ha='center')
plt.tight_layout(); plt.savefig(f'{ROOT}/analysis/lanes_{name}.png',dpi=70)
json.dump([dict(gi=gi,a=g['a'],b=g['b'],err=err) for gi,g,d,h,err,corr in good],open(f'{ROOT}/analysis/lanes_{name}.json','w'))
