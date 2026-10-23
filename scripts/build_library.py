"""Assemble the measured obstacle library used by the builder (all values measured from reference heightmaps)."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, json, numpy as np; sys.path.insert(0,ROOT + '/scripts')
from mxs import *; from profiles import analyze
from sx_classify_lib import rot_patch
R=REF + '/JGSX2026TestTracks/'
lib={}
# ---------- SX lateral wall (normalized), measured on single blocks
L=json.load(open(ROOT + '/lib/sx_components.json'))
singles=[c for c in L if c['npeaks']==1 and c['solidity']>1.5 and c['hmax']>2.5 and 35<c['width_lane']<38.5]
walls=[]; topw=[]
for c in singles:
    P=np.load(f'{ROOT}/lib/sx/{c["id"]}.npy'); u,Q=rot_patch(P,c['s'],c['lane_ang'])
    prof=Q.max(0); ci=np.argmax(prof); xs=Q[:,ci]/prof[ci]
    occ=np.nonzero(xs>0.97)[0]; c0=(occ.min()+occ.max())/2; half=(occ.max()-occ.min())/2*0.1
    topw.append(2*half)
    # outward distance from top edge (>=0) vs normalized height, both sides
    v=(np.arange(len(xs))-c0)*0.1
    for sgn in (1,-1):
        m=(sgn*v>=half-1.0)&(sgn*v<=half+8)
        walls.append(np.interp(np.arange(-1.0,8.01,0.1),sgn*v[m]-half if sgn>0 else (sgn*v[m]-half),xs[m]) if sgn>0 else np.interp(np.arange(-1.0,8.01,0.1),(-v[m]-half)[::-1],xs[m][::-1]))
W=np.median(np.array(walls),0); W=np.clip(W,0,1)
lib['sx_lateral']=dict(top_width=float(np.median(topw)),wall_d0=-1.0,wall_step=0.1,wall=np.round(W,4).tolist(),
                       n_samples=len(singles),note='h(u,v)=p(u)*wall(|v|-top_width/2); measured median over single SX blocks')
print('SX lane top width', np.median(topw), 'wall 10/50/90% at', [float(np.arange(-1,8.01,.1)[np.argmax(W<q)]) for q in (0.9,0.5,0.1)])
# ---------- SX sections along gradient lines
SECT=[('whoops_det','JGSX2026Detroit',32),('whoops_cus','JGSX2026Custom',32),('rhythm5_det','JGSX2026Detroit',36),
      ('rhythm5_gle','JGSX2026Glendale',36),('rhythm_gap_gle','JGSX2026Glendale',84),('mixed7_det','JGSX2026Detroit',35),
      ('mixed5_arl','JGSX2026Arlington',37),('mixed5_cle','JGSX2026Custom1',71),('longtable_cus','JGSX2026Custom',55),
      ('triple_det','JGSX2026Detroit',27),('stepup_det','JGSX2026Detroit',30),('bigdouble_gle','JGSX2026Glendale',83),
      ('table9_arl','JGSX2026Arlington',20),('onoff_det','JGSX2026Detroit',11),('rhythm3_cus','JGSX2026Custom',49),('mixed4_arl','JGSX2026Arlington',49)]
secs={}
COMP=json.load(open(ROOT + '/lib/sx_components.json'))
for sid,ref,gi in SECT:
    T=Track(R+ref,'xz'); g=dict(T.gradients[gi])
    # true lane axis: direction = median 'lane_ang' of the isolated blocks crossed by the gradient line,
    # offset = median perpendicular offset of their centroids (the JGMX gradient lines are sometimes diagonal / off-centre)
    _a=np.array(g['a']); _u=(np.array(g['b'])-_a)/g['len']
    crossed=[]
    for c in COMP:
        if c['ref']!=ref or c['npeaks']!=1 or c['solidity']<1.3 or not (30<c['width_lane']<45): continue
        pv=np.array([c['cx'],c['cz']])-_a; t=pv@_u; perp=pv[0]*(-_u[1])+pv[1]*_u[0]
        if -5<t<g['len']+5 and abs(perp)<22: crossed.append(c)
    axis_note='gradient line'
    if len(crossed)>=2 and True:
        angs=np.array([c['lane_ang'] for c in crossed])
        dirs=np.c_[np.cos(angs),np.sin(angs)]; dirs*=np.sign(dirs@_u)[:,None]
        ax=np.median(dirs,0); ax/=np.linalg.norm(ax)
        nrm=np.array([-ax[1],ax[0]])
        offs=np.array([(np.array([c['cx'],c['cz']])-_a)@nrm for c in crossed]); off=float(np.median(offs))
        P0=_a+nrm*off; t1=(np.array(g['b'])-P0)@ax
        ang_dev=float(np.degrees(np.arccos(np.clip(ax@_u,-1,1))))
    if len(crossed)>=2 and ang_dev<10 and abs(off)<16:
        g['a']=list(P0); g['b']=list(P0+ax*t1); g['len']=float(t1); _a=np.array(g['a']); _u=ax
        axis_note=f'lane axis from {len(crossed)} blocks: {ang_dev:.1f} deg / {off:+.1f} ft from the gradient line'
    _A=_a-_u*30; _B=np.array(g['b'])+_u*30
    d,h=T.line(*_A,*_B,step=0.1); h=h-np.median(T.H)
    # keep only the obstacles belonging to this lane: stop at the first floor gap > 30 ft outside the original line

    G=parse_gates(R+ref+'/timing_gates'); C=np.array([[c[1],c[3]] for c in G['cps']]); lap=G['normal']
    ux,uz=(g['b'][0]-g['a'][0])/g['len'],(g['b'][1]-g['a'][1])/g['len']
    # travel direction from lap order: checkpoints lying on this lane line
    on=[]
    for k,i in enumerate(lap):
        px,pz=C[i]-np.array(g['a']); t=px*ux+pz*uz; perp=abs(-px*uz+pz*ux)
        if perp<18 and -20<t<g['len']+20: on.append((k,t))
    direction=0
    for (k1,t1),(k2,t2) in zip(on,on[1:]):
        if k2==k1+1: direction+=np.sign(t2-t1)
    rule='lap order'
    res,_=analyze(d,h,'sx')
    if direction==0:  # fallback: takeoff faces are steeper than landing faces on average
        s=sum((m['up']['amax']-m['down']['amax']) for m in res if m['up'] and m['down']); direction=1 if s>=0 else -1; rule='steeper-face rule'
    i0,i1=int(30/0.1),int((30+g['len'])/0.1)
    def fix_end(i, step):
        """obstacle cut by the original gradient end: walk <=25 ft to the floor, else retreat to the last floor point"""
        if h[i] <= 0.3: return i
        j=i
        while 0<j<len(h)-1 and h[j]>0.05 and abs(j-i)<250: j+=step
        if h[j]<=0.05: return j
        j=i
        while h[j]>0.05: j-=step
        return j
    i0=fix_end(i0,-1); i1=fix_end(i1,+1)
    h=h[i0:i1+1]
    FIXED_DIR={'bigdouble_gle':1,'rhythm_gap_gle':1,'mixed5_cle':1,'triple_det':1}
    if sid in FIXED_DIR: direction=FIXED_DIR[sid]; rule='fixed (as reviewed)'
    if direction<0: h=h[::-1]
    nz=np.nonzero(h>0.05)[0]; a,b=max(nz.min()-20,0),min(nz.max()+20,len(h)-1)
    p=np.clip(h[a:b+1],0,None)
    res,_=analyze(np.arange(len(p))*0.1,p,'sx')
    secs[sid]=dict(ref=ref,grad=gi,axis=axis_note,a=g['a'],b=g['b'],dir=int(np.sign(direction)),dir_rule=rule,step=0.1,length=float(len(p)*0.1),prof=np.round(p,3).tolist(),
                   elements=[dict(foot0=m['foot0'],foot1=m['foot1'],crest=m['crest'],H=m['height'],top=m['top_len'],
                                  up_max=(m['up'] or {}).get('amax'),dn_max=(m['down'] or {}).get('amax'),up_L=(m['up'] or {}).get('L'),dn_L=(m['down'] or {}).get('L')) for m in res])
    print(f"{sid:15s} {ref[8:]:9s} g{gi:<3d} [{axis_note}] dir {direction:+.0f} ({rule}) L={len(p)*0.1:6.1f} :", ' '.join(f"{e['H']:.1f}@{e['crest']:.0f}" for e in secs[sid]['elements']))
lib['sx_sections']=secs

def contiguous_taper(rel, hm):
    order=np.argsort(rel); r=rel[order]; h=hm[order]/hm.max(); i0=np.argmin(np.abs(r)); a=i0; b=i0
    while a>0 and h[a-1]>0.05: a-=1
    while b<len(h)-1 and h[b+1]>0.05: b+=1
    return r[a:b+1].tolist(), np.round(h[a:b+1],3).tolist()
# ---------- SX berms (two families)
B=json.load(open(ROOT + '/lib/sx_berms.json'))
big=[b for b in B if 38<b['R_crest']<43 and b['span_deg']>=120]; small=[b for b in B if 21<b['R_crest']<26 and b['inner_max_deg']>40]
def fam(lst):
    rr=np.arange(-30,25.01,0.1)  # relative to crest radius
    P=[np.interp(rr,np.arange(len(b['prof']))*0.1+b['prof_r0']-b['R_crest'],b['prof']) for b in lst]
    return dict(n=len(lst),R_crest=float(np.median([b['R_crest'] for b in lst])),span_deg=float(np.median([b['span_deg'] for b in lst])),
                H=float(np.median([b['H'] for b in lst])),r_rel0=-30.0,step=0.1,prof=np.round(np.median(P,0),3).tolist(),
                members=[(b['ref'],round(b['cx']),round(b['cz'])) for b in lst])
lib['sx_berm_big']=fam(big); lib['sx_berm_small']=fam(small)
for k in ('sx_berm_big','sx_berm_small'): print(k,{q:lib[k][q] for q in ('n','R_crest','span_deg','H')})
# angular taper of the big berm: crest height vs angle
T=Track(R+'JGSX2026Detroit','xz'); b=big[0]
angs=np.radians(np.arange(-180,180,1)); hm=[]
for a in angs:
    rr=np.arange(b['R_crest']-8,b['R_crest']+8,0.2); hm.append((T.h(b['cx']+rr*np.cos(a),b['cz']+rr*np.sin(a))-np.median(T.H)).max())
hm=np.array(hm); on=hm>0.1*hm.max(); idx=np.nonzero(on)[0]
# rotate so the crescent is contiguous, express height vs angle from the crescent middle
k0=np.argmax(hm); rel=((np.degrees(angs)-np.degrees(angs[k0])+180)%360)-180
order=np.argsort(rel); lib['sx_berm_big']['taper_deg'],lib['sx_berm_big']['taper']=contiguous_taper(rel,hm)
for fam_key,members in (('sx_berm_small',small),):
    b=members[0]; T=Track(R+b['ref'],'xz'); hm=[]
    for a in angs:
        rr=np.arange(b['R_crest']-8,b['R_crest']+8,0.2); hm.append((T.h(b['cx']+rr*np.cos(a),b['cz']+rr*np.sin(a))-np.median(T.H)).max())
    hm=np.array(hm); k0=np.argmax(np.convolve(hm,np.ones(31)/31,'same')); rel=((np.degrees(angs)-np.degrees(angs[k0])+180)%360)-180; order=np.argsort(rel)
    lib[fam_key]['taper_deg'],lib[fam_key]['taper']=contiguous_taper(rel,hm); lib[fam_key]['taper_src']=b['ref']+f" ({b['cx']:.0f},{b['cz']:.0f})"
print('big taper span',min(lib['sx_berm_big']['taper_deg']),max(lib['sx_berm_big']['taper_deg']),' small',min(lib['sx_berm_small']['taper_deg']),max(lib['sx_berm_small']['taper_deg']))

def contiguous_taper(rel, hm):
    order=np.argsort(rel); r=rel[order]; h=hm[order]/hm.max(); i0=np.argmin(np.abs(r)); a=i0; b=i0
    while a>0 and h[a-1]>0.05: a-=1
    while b<len(h)-1 and h[b+1]>0.05: b+=1
    return r[a:b+1].tolist(), np.round(h[a:b+1],3).tolist()

for fam_key in ('sx_berm_big','sx_berm_small'): pass
# ---------- MX
U=json.load(open(ROOT + '/analysis/mx_units.json'))
lib['mx_units']=U
json.dump(lib,open(ROOT + '/lib/library.json','w'),default=float)
print('saved')
