"""Detect MX jumps/rollers along a reference centerline; measure faces, lips, landings, cross-sections; turns & berms."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, json, numpy as np; sys.path.insert(0,ROOT + '/scripts'); from mxs import *
from scipy.signal import find_peaks
from scipy.ndimage import uniform_filter1d
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
name,f=sys.argv[1],sys.argv[2]
D=np.load(f'{ROOT}/analysis/cl_{name}.npz'); s,x,z,h,k,th=[D[q] for q in ('s','x','z','h','kappa','th')]
T=Track(f,'xz'); ds=0.25
slope=np.degrees(np.arctan(np.gradient(h,ds)))
pk,pr=find_peaks(h,prominence=2.0,distance=int(25/ds))
feat=[]
for p in pk:
    w=int(90/ds); a=max(0,p-w); b=min(len(h)-1,p+w)
    # up-face: walk back from crest while slope > 4 deg
    i=p
    while i>a and slope[i-1]>4: i-=1
    j=p
    while j<b and slope[j+1]<-4: j+=1
    upL=(p-i)*ds; up_h=h[p]-h[i]; dnL=(j-p)*ds; dn_h=h[p]-h[j]
    up_max=slope[i:p+1].max() if p>i else 0
    # lip angle: max slope in last 3 ft before crest plateau
    lipzone=slope[max(i,p-int(6/ds)):p+1]; lip=lipzone.max() if len(lipzone) else 0
    dn_max=-slope[p:j+1].min() if j>p else 0
    # face curvature: angle at 25/50/75% of face
    q=lambda fr: float(slope[int(i+fr*(p-i))]) if p>i else 0
    # cross-section at the 75% point of the face
    ci=int(i+0.75*(p-i)); ux,uz=np.cos(th[ci]),np.sin(th[ci]); vx,vz=-uz,ux
    t=np.arange(-45,45.01,0.25); hx=T.h(x[ci]+vx*t,z[ci]+vz*t)
    rel=hx-hx[len(t)//2]
    # width where surface is within 1.0 ft of centre height
    c=len(t)//2; L_=c
    while L_>0 and abs(rel[L_])<1.0: L_-=1
    R_=c
    while R_<len(t)-1 and abs(rel[R_])<1.0: R_+=1
    kind='jump' if (lip>18 and dn_max>18 and up_h>2.5) else ('step-down' if dn_h>up_h*1.5 and dn_max>15 else ('roller/hill' if up_max<16 else 'jump/roller'))
    feat.append(dict(s=float(s[p]),x=float(x[p]),z=float(z[p]),prom=float(pr['prominences'][list(pk).index(p)]),kind=kind,
        up_len=upL,up_h=float(up_h),up_max=float(up_max),lip=float(lip),a25=q(.25),a50=q(.5),a75=q(.75),
        dn_len=dnL,dn_h=float(dn_h),dn_max=float(dn_max),width_flat=float((R_-L_)*0.25),
        prof_s0=float(s[a]),prof=np.round(h[a:b+1]-h[p],3).tolist()))
# turns: segments with |kappa| > 1/80
R=1/np.maximum(np.abs(k),1e-4); turns=[]
m=R<80; i=0
while i<len(m):
    if m[i]:
        j=i
        while j<len(m) and m[j]: j+=1
        if (j-i)*ds>15:
            seg=slice(i,j); ap=i+np.argmin(R[seg]); ang=abs(th[j-1]-th[i])
            sgn=np.sign(k[ap]); ux,uz=np.cos(th[ap]),np.sin(th[ap]); vx,vz=-uz,ux
            t=np.arange(-50,50.01,0.25); hx=T.h(x[ap]+vx*t,z[ap]+vz*t)-h[ap]
            outer=hx[::-1] if sgn>0 else hx  # orient so outside is positive t... (sign convention checked visually)
            turns.append(dict(s=float(s[ap]),x=float(x[ap]),z=float(z[ap]),Rmin=float(R[ap]),angle_deg=float(np.degrees(ang)),
                              xs=np.round(hx,3).tolist(),sign=float(sgn)))
        i=j
    else: i+=1
json.dump(dict(features=feat,turns=turns),open(f'{ROOT}/analysis/mxfeat_{name}.json','w'))
print(name,'peaks',len(feat),'turns',len(turns))
for ft in feat: print(f"s={ft['s']:6.0f} ({ft['x']:4.0f},{ft['z']:4.0f}) {ft['kind']:11s} prom{ft['prom']:4.1f} up {ft['up_len']:5.1f}ft/{ft['up_h']:4.1f}ft max{ft['up_max']:3.0f} lip{ft['lip']:3.0f} [{ft['a25']:3.0f},{ft['a50']:3.0f},{ft['a75']:3.0f}] | dn {ft['dn_len']:5.1f}/{ft['dn_h']:4.1f} max{ft['dn_max']:3.0f} | w{ft['width_flat']:4.0f}")
Rs=np.array([t['Rmin'] for t in turns]); A=np.array([t['angle_deg'] for t in turns])
print('turn radius percentiles (ft) 10/50/90:',np.percentile(Rs,[10,50,90]).round(1),' angles:',np.percentile(A,[10,50,90]).round(0))
