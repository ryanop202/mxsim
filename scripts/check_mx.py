import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, json, numpy as np; sys.path.insert(0,ROOT + '/scripts')
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from scipy import ndimage as ndi
H=np.load(ROOT + '/legacy_mx/build/H.npy').astype(float); s=0.4
D=np.load(ROOT + '/legacy_mx/build/mx_line.npz'); x,z,ss,E,O=D['x'],D['z'],D['s'],D['E'],D['O']
R=json.load(open(ROOT + '/legacy_mx/build/build_report.json'))
# actual centreline height from the exported heightmap
hc=ndi.map_coordinates(H,[z/s,x/s],order=1)
# lateral wall check: max |slope| across +-35 ft
th=np.arctan2(np.gradient(z),np.gradient(x)); nx,nz=-np.sin(th),np.cos(th)
lat=[]
for off in np.arange(-40,40.1,1.0):
    lat.append(ndi.map_coordinates(H,[(z+nz*off)/s,(x+nx*off)/s],order=1))
lat=np.array(lat)
sl=np.degrees(np.arctan(np.abs(np.diff(lat,axis=0))/1.0))
left=sl[:20].max(0); right=sl[20:].max(0)
fig,ax=plt.subplots(5,1,figsize=(30,16))
n=len(ss)//5
for k in range(5):
    m=slice(k*n,(k+1)*n); a=ax[k]
    a.plot(ss[m],hc[m],'k',lw=.8,label='exported centreline'); a.plot(ss[m],(E-O)[m],'b--',lw=.5,label='grade')
    a2=a.twinx(); a2.plot(ss[m],np.maximum(left,right)[m],'r',lw=.4,alpha=.6); a2.set_ylim(0,90); a2.set_ylabel('max lateral slope deg',color='r')
    for p in R['mx']['sections']:
        if ss[m][0]<=p['s0']<=ss[m][-1]: a.axvspan(p['s0'],p['s1'],color='y',alpha=.25); a.text(p['s0'],hc[m].max(),p['sid'],fontsize=7)
    a.grid(alpha=.3)
ax[0].legend()
plt.tight_layout(); plt.savefig(ROOT + '/analysis/mx_profile_check.png',dpi=45)
print('centreline height range',hc.min(),hc.max(),' |exported - designed| max',np.abs(hc-E).max(), 'p99', np.percentile(np.abs(hc-E),99))
