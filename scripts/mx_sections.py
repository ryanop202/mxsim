"""Extract MX sections: as-built profiles along reference lane lines (through a checkpoint, along the lane), with QA crops."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, json, numpy as np; sys.path.insert(0,ROOT + '/scripts'); from mxs import *
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
REF={'DrDew':REF + '/JGMXDrDew/JGMXDrDew','Desert':REF + '/JGMXDesertSand/JGMXDesertSand'}
SEL=[('dd_table27','DrDew',27,-20,100),('dd_table30','DrDew',30,-45,45),('dd_table12','DrDew',12,-35,35),('dd_jump24','DrDew',24,-90,55),
     ('dd_stepdown48','DrDew',48,-40,80),('dd_rhythm17','DrDew',17,-35,90),('dd_table35','DrDew',35,-55,100),('dd_jump16','DrDew',16,5,105),
     ('ds_double31','Desert',31,-80,100),('ds_kicker30','Desert',30,-60,30),('ds_table53','Desert',53,-40,70),('ds_table59','Desert',59,-28,40),
     ('ds_rollers50','Desert',50,-50,100),('ds_jump15','Desert',15,-50,45),('ds_jump44','Desert',44,-110,-15),('ds_stepdown26','Desert',26,0,100),
     ('ds_tables16','Desert',16,-5,100),('ds_chop3','Desert',3,-85,60),('ds_chop58','Desert',58,-75,5),('ds_chop56','Desert',56,-40,40),
     ('ds_jump54','Desert',54,-70,35),('ds_jump47','Desert',47,-40,15)]
CP={n:{p['cp']:p for p in json.load(open(f'{ROOT}/analysis/cplanes_{n}.json'))} for n in REF}
TR={n:Track(f,'xz') for n,f in REF.items()}
out={}
fig,axs=plt.subplots(6,8,figsize=(40,30)); k=0
for sid,ref,cp,da,db in SEL:
    p=dict(CP[ref][cp]); T=TR[ref]
    # refine lane direction: the direction along which cross-sections are most uniform (extruded track surface)
    best=None
    mx_,mz_=p['x']+p['ux']*(da+db)/2,p['z']+p['uz']*(da+db)/2
    for th in np.radians(np.arange(0,180,2)):
        ux,uz=np.cos(th),np.sin(th); t=np.arange(-14,14.01,1.0); cost=0
        for dd in np.arange(-(db-da)/2,(db-da)/2+0.1,6.0):
            cx,cz=mx_+ux*dd,mz_+uz*dd; hx=T.h(cx-uz*t,cz+ux*t); cost+=np.var(hx-np.polyval(np.polyfit(t,hx,1),t))+0.05*np.polyfit(t,hx,1)[0]**2*100
        if best is None or cost<best[0]: best=(cost,ux,uz)
    _,ux,uz=best
    if ux*p['ux']+uz*p['uz']<0: ux,uz=-ux,-uz
    ang_change=np.degrees(np.arccos(np.clip(ux*p['ux']+uz*p['uz'],-1,1)))
    p['ux'],p['uz']=ux,uz; p['x'],p['z']=mx_-ux*(da+db)/2,mz_-uz*(da+db)/2
    x0,z0=p['x']+p['ux']*da,p['z']+p['uz']*da; x1,z1=p['x']+p['ux']*db,p['z']+p['uz']*db
    d,h=T.line(x0,z0,x1,z1,step=0.1)
    # lateral check: cross sections every 5 ft -> riding width where |h - h_centre| < 0.75 ft (track surface continuity)
    W=[]
    for dd in np.arange(0,d[-1],5.0):
        cx,cz=x0+p['ux']*dd,z0+p['uz']*dd; t=np.arange(-30,30.01,0.5)
        hx=T.h(cx-p['uz']*t,cz+p['ux']*t); c=len(t)//2; rel=np.abs(hx-hx[c])
        a=c
        while a>0 and rel[a-1]<0.75: a-=1
        b=c
        while b<len(t)-1 and rel[b+1]<0.75: b+=1
        W.append((b-a)*0.5)
    prof=h-h[0]
    out[sid]=dict(ref=ref,cp=cp,file=_os.path.relpath(REF[ref], _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')),line=[x0,z0,x1,z1],step=0.1,length=float(d[-1]),prof=np.round(prof,3).tolist(),
                  net=float(prof[-1]),hmax=float(prof.max()),hmin=float(prof.min()),flat_width_median=float(np.median(W)),flat_width_min=float(np.min(W)))
    out[sid]['dir_refined_deg']=float(ang_change)
    print(f"dirfix {ang_change:5.1f}deg {sid:15s} {ref:6s} cp{cp:<3d} L={d[-1]:5.0f} net={prof[-1]:+6.1f} range[{prof.min():+.1f},{prof.max():+.1f}] flat-width med {np.median(W):4.0f} min {np.min(W):4.0f}")
    # QA crop
    ax=axs.flat[k]; k+=1
    pad=60; bx0,bx1=min(x0,x1)-pad,max(x0,x1)+pad; bz0,bz1=min(z0,z1)-pad,max(z0,z1)+pad
    j0,j1,i0,i1=[int(max(v,0)/T.s) for v in (bx0,bx1,bz0,bz1)]
    ax.imshow(LightSource(300,40).hillshade(T.H[i0:i1,j0:j1],vert_exag=3/T.s),cmap='gray',extent=[j0*T.s,j1*T.s,i1*T.s,i0*T.s])
    ax.plot([x0,x1],[z0,z1],'r-',lw=2); ax.plot(x1,z1,'ro'); ax.set_title(sid,fontsize=12)
    ax2=axs.flat[k]; k+=1; ax2.plot(d,prof,'k'); ax2.set_aspect('equal'); ax2.grid(alpha=.3); ax2.set_title(f'{sid} profile',fontsize=10)
plt.tight_layout(); plt.savefig(ROOT + '/analysis/mx_sections_qa.png',dpi=30)
lib=json.load(open(ROOT + '/lib/library.json')); lib['mx_sections']=out
json.dump(lib,open(ROOT + '/lib/library.json','w'),default=float)
