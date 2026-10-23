"""Face-based segmentation of MX as-built profiles (checkpoint lane lines): faces, plateaus, units."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, json, numpy as np
from scipy.ndimage import gaussian_filter1d
ds=0.25
def faces(h, thr=12.0):
    hs=gaussian_filter1d(np.asarray(h),2)  # 0.5 ft smoothing for slope estimation only
    ang=np.degrees(np.arctan(np.gradient(hs,ds)))
    sgn=np.where(ang>thr,1,np.where(ang<-thr,-1,0))
    F=[]; i=0; n=len(h)
    while i<n:
        if sgn[i]!=0:
            j=i; s0=sgn[i]
            while j<n and sgn[j]==s0: j+=1
            # extend to feet where |ang| < 3 deg
            a=i
            while a>0 and ang[a-1]*s0>3: a-=1
            b=j-1
            while b<n-1 and ang[b+1]*s0>3: b+=1
            dh=h[b]-h[a]
            if abs(dh)>=1.0:
                seg=ang[a:b+1]*s0; m=len(seg)
                F.append(dict(sign=int(s0),i0=a,i1=b,L=(b-a)*ds,H=float(abs(dh)),amax=float(seg.max()),
                              a25=float(seg[int(.25*(m-1))]),a50=float(seg[int(.5*(m-1))]),a75=float(seg[int(.75*(m-1))]),
                              lip=float(seg[-int(min(m-1,4/ds)):].max()) if s0>0 else float(seg[:int(min(m-1,4/ds))+1].max())))
            i=j
        else: i+=1
    # merge overlapping same-sign faces
    return F, ang
def units(h, F):
    U=[]
    for k,f in enumerate(F):
        if f['sign']!=1 or f['H']<1.5: continue
        nxt=F[k+1] if k+1<len(F) else None
        if nxt and nxt['sign']==-1 and (nxt['i0']-f['i1'])*ds<120:
            top=(nxt['i0']-f['i1'])*ds; ratio=nxt['H']/f['H']
            if 0.5<ratio<2.0:
                kind='roller' if f['amax']<18 and nxt['amax']<18 else ('table' if top>12 else 'jump')
            elif ratio<=0.5: kind='step-up'
            else: kind='step-down-from-jump'
            U.append(dict(kind=kind,i0=f['i0'],i1=nxt['i1'],up=f,down=nxt,top=top))
        else:
            U.append(dict(kind='step-up' if f['H']>=3 else 'bump',i0=f['i0'],i1=f['i1'],up=f,down=None,top=None))
    return U
if __name__=='__main__':
    out=[]
    for name in ['DrDew','Desert']:
        P=json.load(open(f'{ROOT}/analysis/cplanes_{name}.json'))
        for p in P:
            h=np.array(p['h']); F,ang=faces(h); U=units(h,F)
            for u in U:
                a,b=max(0,u['i0']-int(10/ds)),min(len(h)-1,u['i1']+int(10/ds))
                out.append(dict(ref=name,cp=p['cp'],x=p['x'],z=p['z'],ux=p['ux'],uz=p['uz'],d_start=p['d0']+u['i0']*ds,
                                kind=u['kind'],top=u['top'],up=u['up'],down=u['down'],prof=np.round(h[a:b+1]-h[u['i0']],3).tolist(),prof_off=(u['i0']-a)*ds))
    json.dump(out,open(ROOT + '/analysis/mx_units.json','w'))
    for u in out:
        up=u['up']; dn=u['down'] or {}
        print(f"{u['ref']:6s} cp{u['cp']:<3d} {u['kind']:20s} up L{up['L']:5.1f} H{up['H']:5.1f} max{up['amax']:3.0f} [{up['a25']:3.0f},{up['a50']:3.0f},{up['a75']:3.0f}] lip{up['lip']:3.0f} | top {u['top'] if u['top'] is not None else -1:5.1f} | dn L{dn.get('L',0):5.1f} H{dn.get('H',0):5.1f} max{dn.get('amax',0):3.0f}")
