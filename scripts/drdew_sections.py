"""MX sections along verified JGMX design axes (gradient lines) on Dr. Dew."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, json, numpy as np; sys.path.insert(0,ROOT + '/scripts'); from mxs import *
from mx_faces import faces
T=Track(REF + '/JGMXDrDew/JGMXDrDew','xz')
SEL={'dd_g8':(8,-10,90),'dd_g43':(43,0,175),'dd_g125':(125,-10,160),'dd_g132':(132,-10,110),'dd_g18':(18,-30,80)}
out={}
for sid,(gi,da,db) in SEL.items():
    g=T.gradients[gi]; a=np.array(g['a']); u=(np.array(g['b'])-a)/g['len']
    A=a+u*da; B=a+u*db; d,h=T.line(*A,*B,step=0.25); prof=h-h[0]
    F,ang=faces(prof)
    up=[f for f in F if f['sign']>0]; big=max(up,key=lambda f:f['H']) if up else None
    out[sid]=dict(ref='DrDew',source=f'JGMX gradient line g{gi} (design axis)',line=[*A,*B],step=0.25,length=float(d[-1]),prof=np.round(prof,3).tolist(),
                  net=float(prof[-1]),hmax=float(prof.max()),main_face=big)
    print(f"{sid:8s} L{d[-1]:5.0f} net{prof[-1]:+6.1f} hmax{prof.max():5.1f} main face: L{big['L']:.1f} H{big['H']:.1f} max{big['amax']:.0f} lip{big['lip']:.0f} [{big['a25']:.0f},{big['a50']:.0f},{big['a75']:.0f}]")
lib=json.load(open(ROOT + '/lib/library.json')); lib['mx_drdew_sections']=out
json.dump(lib,open(ROOT + '/lib/library.json','w'),default=float)
