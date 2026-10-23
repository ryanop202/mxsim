"""Measure SX crescent berms: arc radius, angular span, radial (cross-section) profile."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, json, numpy as np; sys.path.insert(0,ROOT + '/scripts'); from mxs import *
from scipy import ndimage as ndi
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
R=REF + '/JGSX2026TestTracks/'
out=[]
fig,axs=plt.subplots(6,4,figsize=(20,18)); ai=0
for r in ['JGSX2026Detroit','JGSX2026Custom','JGSX2026Arlington','JGSX2026Glendale','JGSX2026Custom1']:
    T=Track(R+r,'xz'); H=T.H-np.median(T.H)
    # separate obstacles at 0.5 ft, then look for curved ridges
    lab,n=ndi.label(H>0.5)
    for k,s in enumerate(ndi.find_objects(lab)):
        m=lab[s]==k+1; hh=np.where(m,H[s],0); hm=hh.max()
        if hm<2 or m.sum()*T.s**2<150: continue
        from skimage.morphology import skeletonize
        sk=skeletonize(m); ii,jj=np.nonzero(sk)
        if len(ii)<30: continue
        X=(jj+s[1].start)*T.s; Z=(ii+s[0].start)*T.s
        A=np.c_[2*X,2*Z,np.ones_like(X)]; b=X**2+Z**2
        sol,*_=np.linalg.lstsq(A,b,rcond=None); cx,cz=sol[0],sol[1]; rad=np.sqrt(sol[2]+cx**2+cz**2)
        res=np.abs(np.hypot(X-cx,Z-cz)-rad)
        ang=np.unwrap(np.sort(np.arctan2(Z-cz,X-cx)))
        th=np.arctan2(Z-cz,X-cx)
        # angular span: histogram coverage
        hist,_=np.histogram(th,bins=72,range=(-np.pi,np.pi)); span=(hist>0).sum()*5
        if not (10<rad<150 and np.median(res)<1.5 and span>=60): continue
        # radial profile averaged over covered angles (middle 70% of span)
        covered=np.nonzero(hist>0)[0]; angs=np.radians(covered*5-180+2.5)
        rr=np.arange(max(rad-35,0),rad+25,0.1)
        prof=[]
        for a in angs:
            prof.append(T.h(cx+rr*np.cos(a),cz+rr*np.sin(a))-np.median(T.H))
        prof=np.array(prof); pk=prof.max(1); prof=prof[pk>0.8*pk.max()]; pm=np.median(prof,axis=0)
        ci=np.argmax(pm); top=pm[ci]
        inner=np.nonzero(pm[:ci]<0.05)[0]; outer=np.nonzero(pm[ci:]<0.05)[0]
        r_in=rr[inner.max()] if len(inner) else rr[0]; r_out=rr[ci+outer.min()] if len(outer) else rr[-1]
        g=np.degrees(np.arctan(np.gradient(pm,0.1)))
        rec=dict(ref=r,cx=float(cx),cz=float(cz),R_crest=float(rr[ci]),span_deg=int(span),H=float(top),
                 r_foot_in=float(r_in),r_foot_out=float(r_out),inner_face=float(rr[ci]-r_in),outer_face=float(r_out-rr[ci]),
                 inner_max_deg=float(g[:ci].max()) if ci>0 else 0,outer_max_deg=float(-g[ci:].min()),
                 prof_r0=float(rr[0]),prof=np.round(pm,3).tolist())
        out.append(rec)
        if ai<24:
            ax=axs.flat[ai]; ai+=1; ax.plot(rr,pm,'k'); ax.fill_between(rr,np.percentile(prof,10,0),np.percentile(prof,90,0),alpha=.3)
            ax.set_aspect('equal'); ax.set_title(f"{r[8:]} R={rr[ci]:.0f} span={span} H={top:.1f}",fontsize=9); ax.axvline(rad,color='r',lw=.5)
        print(f"{r[8:]:10s} c=({cx:.0f},{cz:.0f}) Rcrest={rr[ci]:.1f} span={span} H={top:.2f} inner face {rr[ci]-r_in:.1f}ft max {rec['inner_max_deg']:.0f}deg | outer {r_out-rr[ci]:.1f}ft max {rec['outer_max_deg']:.0f}deg")
plt.tight_layout(); plt.savefig(ROOT + '/analysis/sx_berms.png',dpi=55)
json.dump(out,open(ROOT + '/lib/sx_berms.json','w'))
