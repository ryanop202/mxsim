"""Cut 2D stamps of reference crescent berms (exact as-built shape), with centre and mid-angle."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, json, numpy as np; sys.path.insert(0,ROOT + '/scripts'); from mxs import *
from scipy import ndimage as ndi
R=REF + '/JGSX2026TestTracks/'
B=json.load(open(ROOT + '/lib/sx_berms.json'))
picks={'big_det_a':('JGSX2026Detroit',102,154),'big_cus':('JGSX2026Custom',515,165),'big_cle':('JGSX2026Custom1',125,388),
       'small_cus_a':('JGSX2026Custom',74,145),'small_cus_b':('JGSX2026Custom',524,387),'small_arl':('JGSX2026Arlington',533,164)}
out={}
for k,(ref,cx0,cz0) in picks.items():
    b=min([b for b in B if b['ref']==ref],key=lambda b:(b['cx']-cx0)**2+(b['cz']-cz0)**2)
    T=Track(R+ref,'xz'); H=T.H-np.median(T.H)
    rad=b['R_crest']+30
    i0,i1=int((b['cz']-rad)/T.s),int((b['cz']+rad)/T.s); j0,j1=int((b['cx']-rad)/T.s),int((b['cx']+rad)/T.s)
    P=H[i0:i1,j0:j1].copy()
    # component containing the crest ring
    yy,xx=np.mgrid[i0:i1,j0:j1]; r=np.hypot(xx*T.s-b['cx'],yy*T.s-b['cz'])
    ann=(r>b['R_crest']-22)&(r<b['R_crest']+20)
    lab,n=ndi.label((P>0.5)&ann)
    ring=(np.abs(r-b['R_crest'])<1.5)&(P>0.5)
    ids,cnt=np.unique(lab[ring],return_counts=True); keep=ids[(ids>0)]
    keep=keep[np.argmax(cnt[ids>0])] if len(keep) else keep
    m=np.isin(lab,np.atleast_1d(keep))
    wm=np.where(m,P,0); mid0=np.arctan2(((yy*T.s-b['cz'])*wm).sum(),((xx*T.s-b['cx'])*wm).sum())
    # JGMX crescents are a radial profile swept on an arc -> symmetric about the mid-angle.
    # Symmetrise by the minimum of the two mirrored sides: removes neighbouring obstacles touching one tip
    # and restores the natural taper of the tip, without changing the measured shape elsewhere.
    th=np.arctan2(yy*T.s-b['cz'],xx*T.s-b['cx'])-mid0
    thm=mid0-th
    mx_=b['cx']+r*np.cos(thm); mz_=b['cz']+r*np.sin(thm)
    Pm=T.h(mx_.ravel(),mz_.ravel()).reshape(P.shape)-np.median(T.H)
    ann2=(r>b['R_crest']-30)&(r<b['R_crest']+30)
    Ps=np.where(ann2,np.clip(np.minimum(P,Pm),0,None),0.0)
    # downhill flood from the crescent: a pixel joins only if it is not higher than an already-joined neighbour
    dang=np.degrees(np.abs((th+np.pi)%(2*np.pi)-np.pi))
    Ps=np.where(dang<100,Ps,0.0)
    grown=m.copy(); val=np.where(grown,Ps,-1.0)
    for _ in range(200):
        nb=ndi.maximum_filter(val,size=3)
        add=(~grown)&(nb>=0)&(Ps<=nb+0.002)&(Ps<0.6)
        if not add.any(): break
        grown|=add; val=np.where(grown,Ps,-1.0)
    Pk=np.where(grown,Ps,0.0)
    eb=grown&~ndi.binary_erosion(grown); cut_before=float(Pk[eb].max())
    dist=ndi.distance_transform_edt(grown)*T.s
    P=Pk*np.clip((dist-T.s)/2.0,0,1); m=P>0.5
    w=np.where(m,P,0); ang=np.arctan2((yy*T.s-b['cz'])*w,(xx*T.s-b['cx'])*w)
    mid=np.arctan2(((yy*T.s-b['cz'])*w).sum(),((xx*T.s-b['cx'])*w).sum())
    np.save(f'{ROOT}/lib/berm_{k}.npy',P.astype(np.float32))
    out[k]=dict(ref=ref,cx=b['cx'],cz=b['cz'],R_crest=b['R_crest'],H=float(P.max()),mid_angle=float(mid),x0=j0*T.s,z0=i0*T.s,s=T.s,shape=P.shape,
                ride_r=float(b['R_crest']-b['inner_face']-1.5),edge_before_feather=cut_before)
    print(k,ref[8:],'R',round(b['R_crest'],1),'H',round(P.max(),2),'mid',round(np.degrees(mid)),'ride r',round(out[k]['ride_r'],1),'skirt cut before feather %.3f ft'%cut_before)
json.dump(out,open(ROOT + '/lib/berm_stamps.json','w'),default=float)
