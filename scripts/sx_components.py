"""Segment SX reference heightmaps into isolated obstacle components (2D stamps)."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, json, numpy as np; sys.path.insert(0,ROOT + '/scripts'); from mxs import *
from scipy import ndimage as ndi
R=REF + '/JGSX2026TestTracks/'
refs=['JGSX2026Detroit','JGSX2026Custom','JGSX2026Arlington','JGSX2026Glendale','JGSX2026Custom1']
lib=[]; os.makedirs(ROOT + '/lib/sx',exist_ok=True)
for r in refs:
    T=Track(R+r,'xz'); H=T.H.copy()
    floor=np.median(H); Hr=H-floor
    lab,n=ndi.label(Hr>0.12)
    sl=ndi.find_objects(lab)
    for k,s in enumerate(sl):
        m=lab[s]==k+1; area=m.sum()*T.s**2
        if area<40: continue
        hh=np.where(m,Hr[s],0.0); hmax=hh.max()
        if hmax<0.6: continue
        ii,jj=np.nonzero(m); X=(jj+s[1].start)*T.s; Z=(ii+s[0].start)*T.s
        w=hh[m]; cx,cz=np.average(X,weights=w),np.average(Z,weights=w)
        cov=np.cov(np.vstack([X-cx,Z-cz]),aweights=w); ev,evec=np.linalg.eigh(cov)
        major=evec[:,1]; ang=float(np.arctan2(major[1],major[0]))
        # extents along principal axes
        u=(X-cx)*major[0]+(Z-cz)*major[1]; v=-(X-cx)*major[1]+(Z-cz)*major[0]
        # save patch (local raw grid, with 2 px margin) + mask
        pad=3; i0=max(s[0].start-pad,0); i1=min(s[0].stop+pad,T.N); j0=max(s[1].start-pad,0); j1=min(s[1].stop+pad,T.N)
        patch=np.where(lab[i0:i1,j0:j1]==k+1,Hr[i0:i1,j0:j1],0.0)
        # include faint skirt: dilate mask so foot transition (h<0.12) is kept
        mk=ndi.binary_dilation(lab[i0:i1,j0:j1]==k+1,iterations=6)
        patch=np.where(mk,np.clip(Hr[i0:i1,j0:j1],0,None),0.0)
        pid=f'{r.replace("JGSX2026","")}_{k:03d}'
        np.save(f'{ROOT}/lib/sx/{pid}.npy',patch.astype(np.float32))
        lib.append(dict(id=pid,ref=r,x0=j0*T.s,z0=i0*T.s,s=T.s,cx=cx,cz=cz,ang=ang,
                        len_major=float(u.max()-u.min()),len_minor=float(v.max()-v.min()),hmax=float(hmax),area=float(area),
                        vol=float(hh.sum()*T.s**2)))
    print(r,n,'components kept',sum(1 for l in lib if l['ref']==r))
json.dump(lib,open(ROOT + '/lib/sx_components.json','w'),indent=0)
