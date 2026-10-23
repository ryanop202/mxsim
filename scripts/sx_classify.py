import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, json, numpy as np; sys.path.insert(0,ROOT + '/scripts')
from scipy import ndimage as ndi
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from profiles import face_metrics
L=json.load(open(ROOT + '/lib/sx_components.json'))
def rot_patch(P, s, ang, step=0.1):
    """resample patch into local frame: u along 'ang' direction, v across."""
    h,w=P.shape; cy,cx=(h-1)/2,(w-1)/2
    R=np.hypot(h,w)*s/2
    u=np.arange(-R,R,step); U,V=np.meshgrid(u,u,indexing='xy')
    ca,sa=np.cos(ang),np.sin(ang)
    X=U*ca-V*sa; Z=U*sa+V*ca
    out=ndi.map_coordinates(P,[Z/s+cy,X/s+cx],order=1,cval=0)
    return u,out  # out[v_index, u_index]
for c in L:
    P=np.load(f'{ROOT}/lib/sx/{c["id"]}.npy'); s=c['s']
    best=None
    for ang in (c['ang'], c['ang']+np.pi/2):
        u,Q=rot_patch(P,s,ang)
        rows=Q.max(1)>0.3; cols=Q.max(0)>0.3
        # mean |d/du| on the top region
        g=np.abs(np.gradient(Q,axis=1)).mean(); 
        if best is None or g>best[0]: best=(g,ang,u,Q)
    g,ang,u,Q=best; c['lane_ang']=float(ang)
    # centre line profile along lane (median over the central 30% of width)
    occ=Q.max(1)>0.3*Q.max(); vi=np.nonzero(occ)[0]
    width=(vi.max()-vi.min())*0.1 if len(vi) else 0
    mid=(vi.min()+vi.max())//2 if len(vi) else Q.shape[0]//2; k=max(1,int(0.15*len(vi)))
    prof=np.median(Q[mid-k:mid+k+1],axis=0)
    nz=np.nonzero(prof>0.05)[0]
    a,b=nz.min(),nz.max(); c['prof']=np.round(prof[a:b+1],3).tolist(); c['prof_step']=0.1
    c['length_lane']=float((b-a)*0.1); c['width_lane']=float(width)
    # cross profile at crest
    ci=int(np.argmax(prof)); xs=Q[:,ci]; c['xs']=np.round(xs[xs>0.02],3).tolist()
    # fill ratio (crescent detection): occupied pixels / bbox
    m=P>0.3; c['solidity']=float(m.sum()/ (ndi.binary_fill_holes(ndi.binary_closing(m,iterations=25)).sum()+1))
    top=np.max(prof); pl=np.nonzero(prof>top-0.25)[0]
    c['top_len']=float((pl.max()-pl.min())*0.1)
    d=np.arange(len(prof))*0.1
    up=face_metrics(d,prof,a,pl.min(),+1); dn=face_metrics(d,prof,pl.max(),b,-1)
    c['up']=up; c['down']=dn
    # number of peaks along lane
    from scipy.signal import find_peaks
    pk,_=find_peaks(np.r_[0,prof,0],prominence=0.4); c['npeaks']=int(len(pk))
json.dump(L,open(ROOT + '/lib/sx_components.json','w'),default=float)
# gallery
n=len(L); cols=8; rows=int(np.ceil(n/cols))
fig,axs=plt.subplots(rows,cols,figsize=(cols*3,rows*2.4))
for ax,c in zip(axs.flat,L):
    P=np.load(f'{ROOT}/lib/sx/{c["id"]}.npy'); ax.imshow(P,cmap='terrain',vmin=0,vmax=12); ax.set_xticks([]);ax.set_yticks([])
    ax.set_title(f'{c["id"]} H{c["hmax"]:.1f} L{c["length_lane"]:.0f} W{c["width_lane"]:.0f}\nsol{c["solidity"]:.2f} pk{c["npeaks"]}',fontsize=7)
for ax in list(axs.flat)[n:]: ax.axis('off')
plt.tight_layout(); plt.savefig(ROOT + '/analysis/sx_gallery.png',dpi=55)
