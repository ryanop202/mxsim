import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, json, numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
U=json.load(open(ROOT + '/analysis/mx_units.json'))
for name in ['DrDew','Desert']:
    P={p['cp']:p for p in json.load(open(f'{ROOT}/analysis/cplanes_{name}.json'))}
    cps=sorted({u['cp'] for u in U if u['ref']==name and u['kind'] in ('jump','table','step-down-from-jump')})
    fig,axs=plt.subplots(int(np.ceil(len(cps)/2)),2,figsize=(30,2.4*np.ceil(len(cps)/2)))
    for ax,cp in zip(axs.flat,cps):
        p=P[cp]; h=np.array(p['h']); d=p['d0']+np.arange(len(h))*0.25
        ax.plot(d,h,'k',lw=1); ax.set_aspect('equal'); ax.set_xticks(np.arange(-110,111,10)); ax.grid(alpha=.35); ax.tick_params(labelsize=7)
        for u in U:
            if u['ref']==name and u['cp']==cp: ax.axvspan(u['d_start'],u['d_start']+len(u['prof'])*0.25-u['prof_off']-10,color={'jump':'r','table':'g'}.get(u['kind'],'y'),alpha=.15)
        ax.set_title(f'{name} cp{cp} ({p["x"]:.0f},{p["z"]:.0f})',fontsize=10)
    plt.tight_layout(); plt.savefig(f'{ROOT}/analysis/mxcand_{name}.png',dpi=42)
