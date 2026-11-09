"""Saint-Thibéry -> game folder tracks/USLAND2026StThibery (first playable version of the v4 track map).
Own terrain / tilemap / shading / timing gates / statues / decals / flaggers / minimap; textures and models are the shared
USLAND ones (@USLAND2026SX1/..., installed with the USLAND pack), like SX2 and SX3. No fence, no paddock, no flames, no start gantry / finish arch (v13: removed, new ones to come).
Works without the reference archives. Run: python3 scripts/export_stt.py"""
import os, sys, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
import numpy as np
from PIL import Image
from matplotlib.colors import LightSource
import matplotlib.cm as cm
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from shading import lambert_shadow
import layouts_sx as LS, build_stt as B, props_usland as PU, props_place as PP
LT = B.LT; KEY, PFX = B.KEY, B.PFX                                   # v66: the layout chosen by MX_LAYOUT (default Saint-Thibery)
from timing import gates
from starts import StartRoute
from engine import turn_mid_angle

FOLDER, DESC = (LT.DAY['folder'], LT.DAY['desc']) if getattr(LT, 'DAY', None) else ('USLAND2026StThibery', 'USLAND: Saint-Thibery')
SH = '@USLAND2026SX1'; P = '@' + FOLDER
OUT = f'{ROOT}/tracks/{FOLDER}'; S = 0.28975

# v85: Windows sometimes refuses a file for a moment (OSError 22 on open, antivirus / indexer): retry the image saves
import PIL.Image as _PIr, time as _tr
_save0_ = _PIr.Image.save
def _save_retry_(self, fp, *a, **k):
    for i_ in range(10):
        try: return _save0_(self, fp, *a, **k)
        except OSError as e_:
            if getattr(e_, 'errno', None) != 22 or i_ == 9: raise
            _tr.sleep(0.5 * (i_ + 1))
_PIr.Image.save = _save_retry_
rng = np.random.default_rng(31)

def ang_of(fx, fz): return float(np.arctan2(-fx, -fz))                 # decal / gate convention
def statue(x, y, z, a, model, tex, shared=True):
    pre = SH if shared else P
    return f'[{x:.6f} {y:.6f} {z:.6f}] {a:.6f} {pre}/statue/{model}.jm {SH}/statue/{tex}.png null'
def decal(x, z, a, size, tex): return f'[{x:.6f} {z:.6f}] {a:.6f} {size:.6f} 1.000000 {SH}/decal/{tex}.png'
def pts_q(pts, sv, s):
    """point at arc length s along a contour polyline."""
    return np.array([np.interp(s, sv, pts[:, 0]), np.interp(s, sv, pts[:, 1])])

def h_at(H, x, z): return H[np.clip((np.asarray(z) / S).astype(int), 0, H.shape[0] - 1), np.clip((np.asarray(x) / S).astype(int), 0, H.shape[1] - 1)]

def terrain(H, tiles):
    N = H.shape[0]; hmin, hmax = float(H.min()) - 0.5, float(H.max()) + 0.5
    open(f'{OUT}/terrain.hf', 'w', newline='\n').write(f'11 {S:.6f} {hmin:.6f} {hmax:.6f}\n')
    Image.fromarray(np.round((H - hmin) / (hmax - hmin) * 65535).astype(np.uint16)).save(f'{OUT}/terrain.png')
    tiles.astype(np.uint8).tofile(f'{OUT}/tilemap')
    lam, _ = lambert_shadow(H, S, [-0.6528, 0.3590, 0.6671], shadow=False); sh = np.clip(89.3 + 245.8 * lam, 0, 255).astype(np.uint8)
    for nm, img in (('shading.ppm', sh), ('shadingx2.ppm', (sh // 2).astype(np.uint8))):
        with open(f'{OUT}/{nm}', 'wb') as fh: fh.write(f'P6\n{N} {N}\n255\n'.encode()); fh.write(np.repeat(img[:, :, None], 3, axis=2).tobytes())

def obstacle_and_turn_decals(p):
    out = []
    for g in p.segs:
        if g['kind'] == 'S':
            c, s_ = np.cos(g['t']), np.sin(g['t']); a = ang_of(c, s_)
            for prof, u0, name in g['sections']:
                for nm, st, en, hh in LS.COMBOS[name]['items']:
                    L = en - st
                    if nm.startswith('whoops'):
                        for k in range(12):
                            uu = u0 + st + (k + 0.5) * L / 12; out.append(decal(g['x0'] + uu * c, g['z0'] + uu * s_, a, 110.0, 'whoops'))
                        continue
                    uu = u0 + (st + en) / 2; tex, cl = ('tripleface', 79.1) if hh >= 6.6 else (('table', 63.4) if L >= 52 else ('single', 47.5))
                    out.append(decal(g['x0'] + uu * c, g['z0'] + uu * s_, a, max(110.0, 110.0 * (L + 14) / cl), tex))
        elif g['kind'] == 'T' and g.get('berm'):
            m = turn_mid_angle(g); fx, fz = np.cos(m), np.sin(m)
            if abs(g['ang']) > 120: out.append(decal(g['cx'] + fx * 9, g['cz'] + fz * 9, ang_of(fx, fz), 110.0, '180'))
            else: out.append(decal(g['cx'] + fx * 14, g['cz'] + fz * 14, ang_of(fx, fz), 110.0, '90'))
    return out

def surface_decals(p, R):
    out = []; smp = p.samples(3.9)
    for x, z, th in zip(smp['x'], smp['z'], smp['th']):
        nx, nz = -np.sin(th), np.cos(th)
        for v in (-10.4, -5.2, 0.0, 5.2, 10.4):
            j = rng.normal(0, 0.8, 2); out.append(decal(x + nx * v + j[0], z + nz * v + j[1], rng.uniform(-np.pi, np.pi), 26.0, 'track'))
    X_, Z_, _, _ = R.area_points(4.5, 5.5, margin=2.0)
    for x, z in zip(X_, Z_): out.append(decal(x + rng.normal(0, 0.6), z + rng.normal(0, 0.6), rng.uniform(-np.pi, np.pi), 26.0, 'track'))
    for i in (rng.choice(len(smp['x']), 40, replace=False) if getattr(LT, 'TEAROFFS', True) else []):   # v86 (Saint-Georges v33, user): none
        out.append(decal(smp['x'][i] + rng.normal(0, 5), smp['z'][i] + rng.normal(0, 5), rng.uniform(-np.pi, np.pi), 4.84, 'Tearoff'))
    return out

def _ppm(path, img):
    with open(path, 'wb') as fh: fh.write(('P6' + chr(10) + f'{img.shape[1]} {img.shape[0]}' + chr(10) + '255' + chr(10)).encode()); fh.write(img.astype(np.uint8).tobytes())

def gravel_dark_tile(path, n=256):
    """v86 (Saint-Georges v33, user's photo): dark crushed stone - angular blue-grey chips packed tight, a lit facet
    top-left, a darker facet bottom-right, black gaps; tileable (drawn 3x3 then cropped)."""
    from PIL import ImageDraw, ImageFilter
    r = np.random.default_rng(33); N = n * 3
    im = Image.new('RGB', (N, N), (16, 17, 20)); d = ImageDraw.Draw(im)
    pts = []
    for _ in range(int(n * n / 38)):
        pts.append((r.uniform(0, n), r.uniform(0, n), r.uniform(3.0, 6.5)))
    for x0, y0, rr in pts:
        k = int(r.integers(5, 8)); a0 = r.uniform(0, 2 * np.pi); ang = np.sort(a0 + np.linspace(0, 2 * np.pi, k, endpoint=False) + r.normal(0, 0.25, k))
        rad = rr * r.uniform(0.65, 1.15, k); g = r.uniform(58, 98); tint = np.array([g * 0.93, g * 0.96, g * 1.08])
        for ox in (-n, 0, n):
            for oy in (-n, 0, n):
                cx, cy = x0 + n + ox, y0 + n + oy
                P = [(cx + np.cos(a) * q, cy + np.sin(a) * q) for a, q in zip(ang, rad)]
                d.polygon(P, fill=tuple(int(c) for c in tint))
                hi = [(cx + np.cos(a) * q * 0.55 - rr * 0.18, cy + np.sin(a) * q * 0.55 - rr * 0.18) for a, q in zip(ang, rad)]
                d.polygon(hi[: max(3, k // 2 + 1)], fill=tuple(int(min(255, c * 1.28)) for c in tint))   # lit facet
                lo = [(cx + np.cos(a) * q * 0.6 + rr * 0.2, cy + np.sin(a) * q * 0.6 + rr * 0.2) for a, q in zip(ang[k // 2:], rad[k // 2:])] + [(cx + rr * 0.15, cy + rr * 0.15)]
                if len(lo) >= 3: d.polygon(lo, fill=tuple(int(c * 0.72) for c in tint))                 # shaded facet
    im = im.filter(ImageFilter.GaussianBlur(0.45)).crop((n, n, 2 * n, 2 * n))
    a_ = np.asarray(im, float) * (1 + 0.04 * r.normal(size=(n, n, 1)))
    _ppm(path, np.clip(a_, 0, 255))

def gravel_tile(path, n=256):
    """v84 (Saint-Georges v29, user: "it looks like tarmac, make it gravel"): light grey-beige gravel (tileable): a fine dusty base,
    thousands of rounded pebbles of several sizes and greys with a lit top-left edge and a shadow bottom-right."""
    from PIL import ImageDraw
    r = np.random.default_rng(13); base = np.clip(118 + 6 * r.normal(size=(n, n)), 0, 255)
    im = Image.fromarray(np.dstack([base, base * 0.98, base * 0.94]).astype(np.uint8)); d = ImageDraw.Draw(im)
    cols = [(150, 146, 138), (128, 124, 118), (104, 100, 96), (172, 166, 156), (138, 128, 112), (90, 86, 82)]
    for _ in range(1900):
        x, y = r.uniform(0, n), r.uniform(0, n); rr = r.uniform(0.9, 3.4) if r.random() < 0.9 else r.uniform(3.4, 5.5)
        c = cols[int(r.integers(len(cols)))]; e = r.uniform(0.6, 1.0)
        for dx in (-n, 0, n):
            for dy in (-n, 0, n):
                cx, cy = x + dx, y + dy
                d.ellipse([cx - rr + 0.8, cy - rr * e + 0.8, cx + rr + 0.8, cy + rr * e + 0.8], fill=(62, 60, 58))           # shadow
                d.ellipse([cx - rr, cy - rr * e, cx + rr, cy + rr * e], fill=c)
                d.ellipse([cx - rr * 0.6, cy - rr * e * 0.7, cx + rr * 0.1, cy - rr * e * 0.05], fill=tuple(min(255, int(v * 1.12)) for v in c))   # lit top
    _ppm(path, np.asarray(im))

def lightdirt_tile(path, n=256):
    """v82: light dry dirt (tileable): pale beige-brown, soft blotches, fine grain, a few pebbles."""
    r = np.random.default_rng(17); F = np.fft.fftfreq(n)[:, None] ** 2 + np.fft.fftfreq(n)[None, :] ** 2
    w = np.fft.ifft2(np.fft.fft2(r.normal(size=(n, n))) * np.exp(-F * 2500.0)).real; w = (w - w.mean()) / w.std()
    base = np.array([182.0, 150.0, 112.0]); img = base[None, None, :] * (1 + 0.06 * w[:, :, None]) + 7 * r.normal(size=(n, n, 1))
    img[r.random((n, n)) > 0.993] *= 0.75
    _ppm(path, np.clip(img, 0, 255))

def asphalt_tile(path, n=256):
    """v81: tileable asphalt (256 x 256 PPM): dark grey, fine aggregate speckle, soft wear patches."""
    r = np.random.default_rng(11); F = np.fft.fftfreq(n)[:, None] ** 2 + np.fft.fftfreq(n)[None, :] ** 2
    w = np.fft.ifft2(np.fft.fft2(r.normal(size=(n, n))) * np.exp(-F * 3000.0)).real; w = (w - w.mean()) / w.std()
    a_ = 74.0 + 6.0 * w + 9.0 * r.normal(size=(n, n)) + 30.0 * (r.random((n, n)) > 0.985)
    img = np.clip(np.dstack([a_, a_, a_ * 1.03]), 0, 255).astype(np.uint8)
    with open(path, 'wb') as fh: fh.write(('P6' + chr(10) + f'{n} {n}' + chr(10) + '255' + chr(10)).encode()); fh.write(img.tobytes())


def grass_tile(path, n=256):
    """v21: more realistic tileable grass (256 x 256 PPM): mottled greens at several scales, thousands of short blades drawn with
    wrap-around (seamless), a few dry yellowish blades and darker clumps."""
    from PIL import ImageDraw
    r = np.random.default_rng(7); F = np.fft.fftfreq(n)[:, None] ** 2 + np.fft.fftfreq(n)[None, :] ** 2
    def noise(scale):
        w = np.fft.ifft2(np.fft.fft2(r.normal(size=(n, n))) * np.exp(-F * scale)).real; return (w - w.mean()) / w.std()
    big, mid = noise(4000.0), noise(600.0)
    base = np.array([58, 92, 38], float)
    img = base[None, None, :] * (1 + 0.10 * big[:, :, None] + 0.07 * mid[:, :, None])
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    greens = [(46, 78, 30), (64, 102, 40), (78, 118, 48), (90, 128, 56), (54, 88, 34)]
    dry = [(122, 124, 70), (138, 132, 82)]
    for k in range(9000):
        x, y = r.uniform(0, n), r.uniform(0, n); L = r.uniform(3, 9); a = r.normal(-np.pi / 2, 0.45)
        c = dry[r.integers(len(dry))] if r.random() < 0.06 else greens[r.integers(len(greens))]
        c = tuple(int(np.clip(v * r.uniform(0.85, 1.15), 0, 255)) for v in c)
        for ox_ in (-n, 0, n):
            for oy_ in (-n, 0, n):
                x0, y0 = x + ox_, y + oy_
                if -10 < x0 < n + 10 and -10 < y0 < n + 10:
                    d.line([(x0, y0), (x0 + L * np.cos(a), y0 + L * np.sin(a))], fill=c, width=1)
    a_ = np.asarray(im, float) * (1 - 0.12 * np.clip(noise(150.0), 0, None))[:, :, None]   # darker clumps
    ref = f"{ROOT}/assets/grass_jgsx/{LT.GRASS_TUFTS['tex']}.png" if getattr(LT, 'GRASS_TUFTS', None) else f'{ROOT}/assets/grass_dvdb/grass_dvdb.png'
    if (getattr(LT, 'GRASS_DECALS', None) or getattr(LT, 'GRASS_TUFTS', None)) and os.path.exists(ref):   # v25: ground tile matches the tufts    # v23: same mean colour as the grass decals (gaps don't show)
        q = np.asarray(Image.open(ref).convert('RGBA'), float); m_ = q[:, :, 3] > 200; tgt = q[:, :, :3][m_].mean(0)
        a_ = a_ * (tgt / a_.reshape(-1, 3).mean(0))[None, None, :]
    if getattr(LT, 'GRASS_DRY', None):           # v67 (user, Saint-Georges): drier grass - the tile's mean colour moved to this one
        a_ = a_ * (np.array(LT.GRASS_DRY, float) / a_.reshape(-1, 3).mean(0))[None, None, :]
    a_ = np.clip(a_, 0, 255).astype(np.uint8)
    with open(path, 'wb') as fh: fh.write(f'P6\n{n} {n}\n255\n'.encode()); fh.write(a_.tobytes())

def main():
    import time as _tm; T0_RUN = _tm.time() - 2.0
    H, p, rep = B.build(); H = H.astype(np.float64); tiles = np.load(f'{ROOT}/build/{PFX}_tiles.npy')
    GR = getattr(LT, 'GRASS_OUTSIDE', None)
    if GR:                                       # v18/v24: grass tile outside, dirt inside and (v24) up to the fence
        from scipy.ndimage import distance_transform_edt
        TN = tiles.shape[0]; g = (np.arange(TN) * 2 + 0.5) * S; GX, GZ = np.meshgrid(g - LT.STT_ORIGIN[0], g - LT.STT_ORIGIN[1])
        DF = np.load(f'{ROOT}/build/{PFX}_dist.npy')                      # v25: same rounded distance field as the bank
        ii = np.clip(((GZ + LT.STT_ORIGIN[1])).astype(int), 0, DF.shape[0] - 1); jj = np.clip(((GX + LT.STT_ORIGIN[0])).astype(int), 0, DF.shape[1] - 1)
        dirt = DF[ii, jj] <= (LT.FENCE['off'] if GR.get('dirt_to_fence') and getattr(LT, 'FENCE', None) else 0.0)
        gi = sum(1 for l in open(f'{ROOT}/tracks/USLAND2026SX1/tileinfo') if l.strip() == 'addtile')   # grass = next block index
        tiles = np.where(dirt, tiles, gi).astype(np.uint8)
    os.makedirs(f'{OUT}/statue', exist_ok=True)
    RD_ = getattr(LT, 'ROAD', None)                 # v80 (Saint-Georges v24): the user's straight road (gravel / concrete tile)
    if RD_:
        TN = tiles.shape[0]; g = (np.arange(TN) * 2 + 0.5) * S; GXr, GZr = np.meshgrid(g - LT.STT_ORIGIN[0], g - LT.STT_ORIGIN[1])
        gi_ = sum(1 for l in open(f'{ROOT}/tracks/USLAND2026SX1/tileinfo') if l.strip() == 'addtile')   # grass = gi_, asphalt = gi_ + 1
        road = np.zeros(GXr.shape, bool)
        GRr = getattr(LT, 'GRAVEL_RING', None)       # v82 (Saint-Georges v26): dark gravel all round the arena (fence -> mounds)
        if GRr:
            DFr = np.load(f'{ROOT}/build/{PFX}_dist.npy'); from scipy.ndimage import map_coordinates as mcr_
            dr_ = mcr_(DFr, [GZr.ravel() + LT.STT_ORIGIN[1], GXr.ravel() + LT.STT_ORIGIN[0]], order=1).reshape(GXr.shape)
            rg_ = (dr_ > GRr['d'][0]) & (dr_ < GRr['d'][1])
            for x0_, x1_, z0_, z1_ in GRr.get('skip', []): rg_ &= ~((GXr > x0_) & (GXr < x1_) & (GZr > z0_) & (GZr < z1_))   # v84
            road |= rg_
        for RW_ in LT.ROADS:
            m_ = B.road_dist(GXr, GZr, [RW_]) < 8.0
            if RW_['kind'] == 'asphalt': tiles = np.where(m_, gi_ + 1, tiles).astype(np.uint8); road &= ~m_
            else: road |= m_
        LDr = getattr(LT, 'LIGHT_DIRT', None)
        if LDr:
            ld_ = (GXr > LDr['x'][0]) & (GXr < LDr['x'][1]) & (GZr > LDr['z'][0]) & (GZr < LDr['z'][1]); road &= ~ld_
            tiles = np.where(ld_, 0 if LDr.get('tile') == 'main' else gi_ + 3, tiles).astype(np.uint8)   # v86: 'main' = the track dirt tile
        for BL_ in getattr(LT, 'BUILDINGS', []):
            hx_, hz_ = BL_.get('half', (19.0, 11.0)); road &= ~((np.abs(GXr - BL_['c'][0]) < hx_) & (np.abs(GZr - BL_['c'][1]) < hz_))
        PD_ = getattr(LT, 'PATHS_DIRT', False)
        tp_ = 0 if PD_ == 'main' else (gi_ + 3 if PD_ else gi_ + 2)     # v85 (Saint-Georges v30, user): dirt paths; v86 'main' = track dirt
        tiles = np.where(road, tp_, tiles).astype(np.uint8); print('path tiles', int(road.sum()), {0: 'track dirt', gi_ + 3: 'light dirt'}.get(tp_, 'gravel'))   # v82: own dark gravel tile
    terrain(H, tiles)
    A = f'{ROOT}/tracks/USLAND2026SX1'
    for f in ('tileinfo', 'lighting'): shutil.copy(f'{A}/{f}', f'{OUT}/{f}')
    if getattr(LT, 'SKY_FLAT', None):               # v82 (Saint-Georges v26): sky sides without the mountains (fields to the horizon)
        import sky_flat as SKF; os.makedirs(f'{OUT}/sky', exist_ok=True); lt_ = open(f'{OUT}/lighting').read()
        for k_ in ('n', 'e', 's', 'w'):
            SKF.flatten(f'{A}/sky/sky-{k_}.png', f'{OUT}/sky/sky-{k_}.png', seed=ord(k_)); lt_ = lt_.replace(f'@USLAND2026SX1/sky/sky-{k_}.png', f'{P}/sky/sky-{k_}.png')
        open(f'{OUT}/lighting', 'w', newline='\n').write(lt_)
    if GR:                                       # v18: grass tile appended to the SX1 tileinfo (5th block), own texture
        os.makedirs(f'{OUT}/tiles', exist_ok=True); grass_tile(f'{OUT}/tiles/grass.ppm')
        ti = open(f'{OUT}/tileinfo').read(); blk = ti.split('addtile')[0]
        blk = blk.replace('name Main', 'name Grass').replace('@USLAND2026SX1/tiles/dirt.ppm', f'{P}/tiles/grass.ppm')
        blk = blk.replace('r=123 g=73 b=52', 'r=72 g=104 b=46')
        open(f'{OUT}/tileinfo', 'w', newline='\n').write(ti.rstrip('\n') + '\n\n' + blk.strip('\n') + '\naddtile\n\n')
        if getattr(LT, 'ROADS', None):              # v81 (Saint-Georges v25): asphalt tile (departmental road), no ruts
            asphalt_tile(f'{OUT}/tiles/asphalt.ppm'); ti2 = open(f'{OUT}/tileinfo').read()
            ba = ti.split('addtile')[0].replace('name Main', 'name Asphalt').replace('@USLAND2026SX1/tiles/dirt.ppm', f'{P}/tiles/asphalt.ppm')
            ba = ba.replace('r=123 g=73 b=52', 'r=90 g=90 b=92').replace('erode_depth 2.5', 'erode_depth 0.0')
            open(f'{OUT}/tileinfo', 'w', newline=chr(10)).write(ti2.rstrip(chr(10)) + chr(10) * 2 + ba.strip(chr(10)) + chr(10) + 'addtile' + chr(10) * 2)
            gt_ = gravel_dark_tile if getattr(LT, 'GRAVEL_STYLE', '') == 'dark' else gravel_tile
            for nm_, fn_, rgb_ in (('Gravel', gt_, 'r=62 g=64 b=70' if gt_ is gravel_dark_tile else 'r=126 g=122 b=116'), ('LightDirt', lightdirt_tile, 'r=176 g=140 b=100')):   # v82 (Saint-Georges v26)
                fn_(f'{OUT}/tiles/{nm_.lower()}.ppm'); ti3 = open(f'{OUT}/tileinfo').read()
                bg = ti.split('addtile')[0].replace('name Main', 'name ' + nm_).replace('@USLAND2026SX1/tiles/dirt.ppm', f'{P}/tiles/{nm_.lower()}.ppm').replace('r=123 g=73 b=52', rgb_)
                if nm_ == 'Gravel': bg = bg.replace('erode_depth 2.5', 'erode_depth 0.0')
                open(f'{OUT}/tileinfo', 'w', newline=chr(10)).write(ti3.rstrip(chr(10)) + chr(10) * 2 + bg.strip(chr(10)) + chr(10) + 'addtile' + chr(10) * 2)
        if getattr(LT, 'LIGHT_TRACK', None):        # v82: the track dirt a bit lighter (own copy of the SX1 dirt texture)
            from PIL import Image as ImL_
            kL_ = np.array(LT.LIGHT_TRACK if np.ndim(LT.LIGHT_TRACK) else (LT.LIGHT_TRACK,) * 3, float)   # v83: (r, g, b) factors
            dl_ = np.asarray(ImL_.open(f'{ROOT}/tracks/USLAND2026SX1/tiles/dirt.ppm').convert('RGB')).astype(float) * kL_
            ImL_.fromarray(np.clip(dl_, 0, 255).astype(np.uint8)).save(f'{OUT}/tiles/dirt_light.ppm')
            ti4 = open(f'{OUT}/tileinfo').read().replace('@USLAND2026SX1/tiles/dirt.ppm', f'{P}/tiles/dirt_light.ppm')
            c_ = np.clip(np.array([123, 73, 52]) * kL_, 0, 255).astype(int); ti4 = ti4.replace('r=123 g=73 b=52', f'r={c_[0]} g={c_[1]} b={c_[2]}')
            open(f'{OUT}/tileinfo', 'w', newline=chr(10)).write(ti4)
    open(f'{OUT}/desc', 'w', newline='\n').write(DESC + '\n'); open(f'{OUT}/billboards', 'w').close()
    CR = getattr(LT, 'CROWD', None); FE0 = getattr(LT, 'FENCE', None); crowd_st = []
    if CR and FE0:                                 # v40 (user): public on the grass bank (people cut-outs, 2 rows behind the fence)
        from skimage.measure import find_contours
        DF0 = np.load(f'{ROOT}/build/{PFX}_dist.npy'); rg = np.random.default_rng(40); bb = []; crowd_pos = []
        for dr in CR['rows']:
            cs = max(find_contours(DF0, FE0['off'] + dr), key=len); pts = np.c_[cs[:, 1], cs[:, 0]]
            sv = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
            for s0 in np.arange(rg.uniform(0, CR['step']), sv[-1], CR['step']):
                if rg.random() < CR['skip']: continue
                if CR.get('hmin') and float(h_at(H, pts_q(pts, sv, s0)[0], pts_q(pts, sv, s0)[1])) < CR['hmin']: continue   # v70: on the mounds only
                s1 = float(np.clip(s0 + rg.uniform(-CR['jitter'], CR['jitter']), 0, sv[-1]))
                q = np.array([np.interp(s1, sv, pts[:, 0]), np.interp(s1, sv, pts[:, 1])])
                k_ = min(int(np.searchsorted(sv, s1)), len(pts) - 1); tg_ = pts[min(k_ + 1, len(pts) - 1)] - pts[max(k_ - 1, 0)]
                if np.linalg.norm(tg_) > 0: q = q + np.array([-tg_[1], tg_[0]]) / np.linalg.norm(tg_) * rg.uniform(-CR.get('side_jit', 0), CR.get('side_jit', 0))
                sz_ = CR['size'] * rg.uniform(0.95, 1.05); im_ = CR['imgs'][rg.integers(len(CR['imgs']))]
                if CR.get('mesh'): crowd_pos.append((q, sz_, im_))
                else: bb.append(f"[{q[0]:.6f} 0.000000 {q[1]:.6f}] {sz_:.6f} 1.000000 {CR['src']}/{im_}.png")
        EX_ = CR.get('extra')
        if EX_ and CR.get('mesh'):                 # v86 (Saint-Georges v33, user): people all round, against the fence, round the hall, under the arch
            ox_, oz_ = LT.STT_ORIGIN; nex_ = len(crowd_pos)
            blk_ = []; rot_ = []                   # v88 (v39): the real footprint of each building model (rotated), + clear
            for b_ in getattr(LT, 'BUILDINGS', []):
                jm_p = f"{ROOT}/assets/props/{b_['model']}.jm"
                if os.path.exists(jm_p):
                    L_ = open(jm_p).read().split(chr(10)); nv_ = int(L_[2].split()[0])
                    P_ = np.array([[float(t_) for t_ in L_[3 + i_].split()[:3]] for i_ in range(nv_)])
                    rot_.append((np.array(b_['c'], float), np.radians(b_.get('ang', 0.0)), P_[:, 0].min(), P_[:, 0].max(), P_[:, 2].min(), P_[:, 2].max()))
                elif max(b_.get('half', (0, 0))) > 0:
                    blk_.append((b_['c'][0] - b_['half'][0] - EX_['clear'], b_['c'][0] + b_['half'][0] + EX_['clear'],
                                 b_['c'][1] - b_['half'][1] - EX_['clear'], b_['c'][1] + b_['half'][1] + EX_['clear']))
            pol_ = [np.array(p_) for p_, _ in getattr(LT, 'POLE_SPOTS', [])]
            def ok_(wx, wz):
                lx_, lz_ = wx - ox_, wz - oz_
                if any(a0 < lx_ < a1 and b0 < lz_ < b1 for a0, a1, b0, b1 in EX_['avoid'] + blk_): return False
                if any(np.hypot(lx_ - p_[0], lz_ - p_[1]) < 9.0 for p_ in pol_): return False
                for c_, a_, x0b, x1b, z0b, z1b in rot_:
                    d_ = np.array([lx_, lz_]) - c_; u_ = d_ @ np.array([np.cos(a_), np.sin(a_)]); w_ = d_ @ np.array([-np.sin(a_), np.cos(a_)])
                    cl_ = EX_['clear']
                    if x0b - cl_ < u_ < x1b + cl_ and z0b - cl_ < w_ < z1b + cl_: return False
                return True
            for dr in EX_['rings']:
                for cs in find_contours(DF0, FE0['off'] + dr):
                    if len(cs) < 40: continue
                    pts = np.c_[cs[:, 1], cs[:, 0]]; sv = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
                    for s0 in np.arange(rg.uniform(0, EX_['step']), sv[-1], EX_['step']):
                        if rg.random() < EX_['skip']: continue
                        s1 = float(np.clip(s0 + rg.uniform(-1.5, 1.5), 0, sv[-1])); q = np.array([np.interp(s1, sv, pts[:, 0]), np.interp(s1, sv, pts[:, 1])])
                        if not ok_(*q): continue
                        crowd_pos.append((q, CR['size'] * rg.uniform(0.95, 1.05), CR['imgs'][rg.integers(len(CR['imgs']))]))
            SPk_ = EX_['sprinkle']; d0_, d1_ = SPk_['d']
            for _ in range(int(DF0.shape[0] * DF0.shape[1] / SPk_['per'] * 0.25)):
                wx, wz = rg.uniform(0, DF0.shape[1] - 1), rg.uniform(0, DF0.shape[0] - 1); dv_ = DF0[int(wz), int(wx)] - FE0['off']
                if not (d0_ < dv_ < d1_) or float(h_at(H, wx, wz)) > SPk_['hmax'] or not ok_(wx, wz): continue
                crowd_pos.append((np.array([wx, wz]), CR['size'] * rg.uniform(0.95, 1.05), CR['imgs'][rg.integers(len(CR['imgs']))]))
            for zn_ in EX_['zones']:
                x0_, x1_, z0_, z1_ = zn_[:4]; per_ = zn_[4] if len(zn_) > 4 else EX_['zone_per']
                for _ in range(int((x1_ - x0_) * (z1_ - z0_) / per_)):
                    wx, wz = rg.uniform(x0_, x1_) + ox_, rg.uniform(z0_, z1_) + oz_
                    if ok_(wx, wz): crowd_pos.append((np.array([wx, wz]), CR['size'] * rg.uniform(0.95, 1.05), CR['imgs'][rg.integers(len(CR['imgs']))]))
            print('crowd extra (fence rings, flat ground, arch alley)', len(crowd_pos) - nex_)
        if EX_ and EX_.get('no_back') and CR.get('mesh'):   # v87 (v38, user): nobody behind the start nor behind the mounds' crest
            gzd_, gxd_ = np.gradient(DF0); ox_, oz_ = LT.STT_ORIGIN; kept_ = []
            for q, sz_, nm_ in crowd_pos:
                lx_, lz_ = q[0] - ox_, q[1] - oz_
                if any(a0 < lx_ < a1 and b0 < lz_ < b1 for a0, a1, b0, b1 in EX_['avoid']): continue
                i_, j_ = int(np.clip(q[1], 0, DF0.shape[0] - 1)), int(np.clip(q[0], 0, DF0.shape[1] - 1))
                g_ = np.array([gxd_[i_, j_], gzd_[i_, j_]]); ng_ = np.linalg.norm(g_)
                if ng_ > 1e-6:
                    g_ /= ng_; h0_ = float(h_at(H, q[0], q[1])); h1_ = float(h_at(H, q[0] + g_[0] * 5.0, q[1] + g_[1] * 5.0))
                    if h0_ > 1.0 and h1_ < h0_ - 0.4: continue                  # the ground drops away from the track: back side
                kept_.append((q, sz_, nm_))
            print('crowd: removed behind the start / behind the crests', len(crowd_pos) - len(kept_)); crowd_pos = kept_
        open(f'{OUT}/billboards', 'w', newline='\n').write(('\n'.join(bb) + '\n') if bb else ''); print('crowd billboards', len(bb))
        if crowd_pos and CR.get('sprites'):        # v49: billboards cropped to the people (they turn to the view)
            from PIL import Image as Im_
            os.makedirs(f'{OUT}/billboard', exist_ok=True); cr_ = {}
            for im_ in CR['imgs']:
                own_ = CR.get('own', {}).get(im_)
                src_ = f'{ROOT}/assets/crowd/{own_}.png' if own_ else f"{CR['game']}/{CR['src'][1:]}/{im_}.png"
                pic_ = Im_.open(src_).convert('RGBA'); x0_, y0_, x1_, y1_ = pic_.getchannel('A').point(lambda a: 255 if a > 8 else 0).getbbox()
                pic_.crop((x0_, y0_, x1_, y1_)).resize((256, 256), Im_.LANCZOS).save(f'{OUT}/billboard/crowd_{im_}.png')
                cr_[im_] = ((y1_ - y0_) / pic_.height, (x1_ - x0_) / (y1_ - y0_))       # height share of the square, aspect w / h
            bb = [f"[{q[0]:.6f} 0.000000 {q[1]:.6f}] {sz_ * cr_[nm_][0]:.6f} {cr_[nm_][1]:.6f} {P}/billboard/crowd_{nm_}.png" for q, sz_, nm_ in crowd_pos]
            open(f'{OUT}/billboards', 'w', newline=chr(10)).write(chr(10).join(bb) + chr(10)); print('crowd billboards (cropped)', len(bb))
            if CR.get('beast'):                     # v86 (Saint-Georges v31, user): Mr Beast's face on every face (scripts/sgm_crowd_faces.py)
                for im_ in CR['imgs']:
                    b_ = f'{ROOT}/assets/crowd/beast/crowd_{im_}.png'
                    if os.path.exists(b_): shutil.copy(b_, f'{OUT}/billboard/crowd_{im_}.png')
                print('crowd: Mr Beast faces')
            for f_ in os.listdir(f'{OUT}/statue'):
                if f_.startswith(('crowd_', 'vip_')) and f_.endswith('.jm'): os.remove(f'{OUT}/statue/{f_}')
        elif crowd_pos:                              # v42 (user: same crowd, less lag): one mesh per picture, each person a quad
            # cropped to the people (the Miami pictures are 1024 px squares, people ~2 % of them: 2221 big transparent
            # billboards = huge overdraw). Quads face the arena centre. Textures referenced from the Miami track (not copied).
            # One origin on flat ground inside the arena for all meshes (the game tilts a statue with the slope at its origin).
            from PIL import Image as Im_
            ctr_ = np.mean(np.array([q for q, _, _ in crowd_pos]), axis=0); NSEC = CR.get('sectors', 8)
            sec_ = lambda q: int(((np.arctan2(q[1] - ctr_[1], q[0] - ctr_[0]) + np.pi) / (2 * np.pi) * NSEC)) % NSEC
            # flat candidates (+-4 ft within 0.03 ft), 4 ft grid over the dirt area and the terrace
            fl_ = []
            for ox_ in np.arange(ctr_[0] - 330, ctr_[0] + 330, 4.0):
                for oz_ in np.arange(ctr_[1] - 220, ctr_[1] + 220, 4.0):
                    if not (0 < ox_ < 1180 and 0 < oz_ < 1180): continue
                    hs_ = [float(h_at(H, ox_ + dx, oz_ + dz)) for dx in (-4, 0, 4) for dz in (-4, 0, 4)]
                    if max(hs_) - min(hs_) < 0.03: fl_.append((ox_, oz_))
            fl_ = np.array(fl_); worst_ = 0.0
            for k_s in range(NSEC):
              grp_ = [c_ for c_ in crowd_pos if sec_(c_[0]) == k_s]
              if not grp_: continue
              cg_ = np.mean(np.array([q for q, _, _ in grp_]), axis=0)
              org_ = fl_[int(np.argmin(np.hypot(fl_[:, 0] - cg_[0], fl_[:, 1] - cg_[1])))]; h0_ = float(h_at(H, *org_))
              worst_ = max(worst_, float(np.hypot(*(org_ - cg_))))
              for im_ in CR['imgs']:
                  own_ = CR.get('own', {}).get(im_)                 # v43: our own recoloured copy of that picture
                  tex_ = f"{P}/billboard/{own_}.png" if own_ else f"{CR['src']}/{im_}.png"
                  if own_:
                      os.makedirs(f'{OUT}/billboard', exist_ok=True); shutil.copy(f'{ROOT}/assets/crowd/{own_}.png', f'{OUT}/billboard/{own_}.png')
                  al_ = np.asarray(Im_.open(f'{ROOT}/assets/crowd/{own_}.png' if own_ else f"{CR['game']}/{CR['src'][1:]}/{im_}.png").convert('RGBA'))[..., 3]
                  ys_, xs_ = np.where(al_ > 8); x0_, x1_, y0_, y1_ = xs_.min() - 2, xs_.max() + 3, ys_.min() - 2, min(ys_.max() + 1, 1024)
                  m_ = PU.Mesh(1024, 1024); n_ = 0
                  for q, sz_, nm_ in grp_:
                      if nm_ != im_: continue
                      k_ = sz_ / 1024.0; hw_ = (x1_ - x0_) * k_ / 2; cxo_ = ((x0_ + x1_) / 2 - 512) * k_; ht_ = (y1_ - y0_) * k_
                      f_ = ctr_ - q; f_ = f_ / np.linalg.norm(f_); r_ = np.array([-f_[1], f_[0]])        # faces the centre
                      hb_ = float(h_at(H, *q)) - h0_ - 0.15
                      c0_ = q + r_ * cxo_ - org_
                      pa_ = np.array([c0_[0] - r_[0] * hw_, hb_, c0_[1] - r_[1] * hw_]); pb_ = np.array([c0_[0] + r_[0] * hw_, hb_, c0_[1] + r_[1] * hw_])
                      up_ = np.array([0, ht_, 0]); nrm_ = np.array([f_[0], 0.0, f_[1]])
                      # seen from the centre (looking along -f), its right is -r -> the picture's left edge at +r
                      m_.tri_fan([pb_, pa_, pa_ + up_, pb_ + up_], nrm_, [m_.uv_px(x0_, y1_), m_.uv_px(x1_, y1_), m_.uv_px(x1_, y0_), m_.uv_px(x0_, y0_)]); n_ += 1
                  if n_:
                      m_.write(f'{OUT}/statue/crowd_{k_s}_{im_}.jm', (0, 0, 0, 0, 0))
                      crowd_st.append(f"[{org_[0]:.6f} 0.000000 {org_[1]:.6f}] 0.000000 {P}/statue/crowd_{k_s}_{im_}.jm {tex_} null")
            print('crowd meshes', len(crowd_st), 'people quads', len(crowd_pos), 'sectors', NSEC, 'origin max %.0f ft from its people' % worst_)
        for f_ in os.listdir(f'{OUT}/statue'):     # no stale crowd mesh from an earlier export
            if f_.startswith('crowd_') and f'statue/{f_}' not in chr(10).join(crowd_st): os.remove(f'{OUT}/statue/{f_}')
    # timing gates (JGSX method, timing.py) + our gate model on the starting gates
    TG_ = getattr(LT, 'TURN_GATES', None)
    if TG_ and getattr(LT, 'PYLONS', None) and LT.PYLONS.get('points'): TG_ = dict(TG_, pylons=LT.PYLONS['points'])
    txt, cps, first, normal, sM, sF = gates(p, LS.STARTS[KEY], turn_gates=TG_)
    tl, sec = [], None
    for l in txt.split('\n'):
        if l.endswith(':'): sec = l
        elif sec == 'startinggate:' and l.startswith('['):
            v = l.split(']')[0][1:].split()     # v14: y = 0 - the game puts the gate on the ground (the platform) itself; y 2.5 floated
            # v30 (user): hollow red gate (USLAND gate without its plate), own model; same collision shape
            l = f'[{float(v[0]):.6f} 0.000000 {float(v[2]):.6f}] ' + l.split(']')[1].split()[0] + f' {P}/statue/start_gate_frame.jm {P}/statue/start_gate_frame.png @startgate.shp'
        tl.append(l)
    CF_ = getattr(LT, 'CHECKPOINT_FIX', None)
    if CF_:                                         # v88 (Saint-Georges v40): the user's own checkpoints (edited in the game editor)
        sec_ = None; nfx_ = 0
        for i_, l_ in enumerate(tl):
            if l_.endswith(':'): sec_ = l_; continue
            if sec_ != 'checkpoints:' or not l_.strip(): continue
            m_ = l_.split('[')[1].split(']')[0].split(); cx_, cz_ = float(m_[0]), float(m_[2])
            for (ox_, oz_), (nx_, nz_), (vx_, vz_) in CF_:
                if abs(cx_ - ox_) < 3.0 and abs(cz_ - oz_) < 3.0:
                    tl[i_] = f'{np.hypot(vx_, vz_):.6f} [{nx_:.6f} 0.000000 {nz_:.6f}] [{vx_:.6f} 0.000000 {vz_:.6f}]'; nfx_ += 1
        print('checkpoints from the user', nfx_)
    TGF_ = getattr(LT, 'TIMING_GATES_FILE', None)
    if TGF_:                                        # v89 (Saint-Georges v41, user: "on va les garder comme ca"): his own gates file
        tl = open(f'{ROOT}/{TGF_}', encoding='utf-8').read().replace(chr(13), '').replace('@USLAND2026SaintGeorgesbyBazo/', f'{P}/').rstrip(chr(10)).split(chr(10))
        print('timing gates: the user file', TGF_, len(tl), 'lines')
    open(f'{OUT}/timing_gates', 'w', newline='\n').write('\n'.join(tl))
    # statues: grates behind the gates (v13: no start gantry, no finish arch - new ones to come)
    st = []; gl = [l for l in tl if l.startswith('[') and '@startgate.shp' in l]
    G = [[float(v) for v in l.split(']')[0][1:].split()] + [float(l.split(']')[1].split()[0])] for l in gl]
    gx = float(np.mean([g[0] for g in G])); gz = float(np.mean([g[2] for g in G])); fa = G[0][3]
    if getattr(LT, 'START_FLOOR', None):          # v28: ONE big floor (square mesh) behind the whole row, cut at each gate
        import stt_props; stt_props.build()
        for nm in ('start_floor', 'stake_yellow', 'start_gate_frame', 'pylon_black', 'bale_straw', 'boudin_black', 'boudin_plain'):
            for e in ('jm', 'png'): shutil.copy(f'{ROOT}/assets/props/{nm}.{e}', f'{OUT}/statue/{nm}.{e}')
        for nm in ('pylon_black', 'bale_straw', 'boudin_black', 'boudin_plain'): shutil.copy(f'{ROOT}/assets/props/{nm}.shp', f'{OUT}/statue/{nm}.shp')
        GF_ = getattr(LT, 'GATE_FRAME', None)
        if GF_:                                    # v85 (Saint-Georges v30, user): the falling gate as a red rectangle (this track only)
            import stt_props as SPg2_
            mgf_, igf_ = SPg2_.gate_frame(rgb=GF_.get('rgb'), square=GF_.get('square', False), flat=GF_.get('flat'))
            mgf_.write(f'{OUT}/statue/start_gate_frame.jm', (16, 1, 0.35, 0.35, 0.35)); igf_.save(f'{OUT}/statue/start_gate_frame.png')
        import stt_ads as AD_                      # v38: logo boudins (textures only), advertising tarps on the fence
        for nm in [f'boudin_{n}' for n in AD_.BOUDIN_LOGOS] + [f'ad_{n}' for n in AD_.TARP['order']]:
            shutil.copy(f'{ROOT}/assets/props/{nm}.png', f'{OUT}/statue/{nm}.png')
        import stt_ads as AD2
        for nm in [f'startb_{n}.png' for n in AD2.START_BOUDINS_TEX['black'] + (AD2.START_BOUDINS_TEX['yellow'],)] + ['pylon_f50.png', 'pylon_motul.png', 'startb.shp']:
            shutil.copy(f'{ROOT}/assets/props/{nm}', f'{OUT}/statue/{nm}')       # v50
        for nm in ('ad_tarp.jm', 'boudin_logo.jm', 'boudin_logo.shp', 'start_sign.jm', 'start_sign.png', 'flag_cage.jm', 'flag_cage.png'):   # v39 / v40 / v41
            shutil.copy(f'{ROOT}/assets/props/{nm}', f'{OUT}/statue/{nm}')
        f = np.array([-np.sin(fa), -np.cos(fa)])
        SG_ = getattr(LT, 'START_GRIDS', None)
        if SG_:                                     # v84 (Saint-Georges v29): short diamond-mesh plates in red frames + a beam behind
            import start_grids as SGR_
            mG_, iG_ = SGR_.floor_mesh(LS.N_GATES, LS.GATE_PITCH, SG_['length'], frame_rgb=SG_.get('frame_rgb'), beam_gap=SG_.get('beam_gap', 0.0), clean=SG_.get('clean')); mG_.write(f'{OUT}/statue/start_grids.jm', (0, 0, 0, 0, 0)); iG_.save(f'{OUT}/statue/start_grids.png')
            hh_ = np.radians(LT.START_HEADING); bx_, bz_ = -np.cos(hh_), -np.sin(hh_)      # behind the gates; statue +x -> (cos A, -sin A)
            shg_ = 'null'
            if SG_.get('beam_shp'):                 # v86 (Saint-Georges v31): collision on the beam
                open(f'{OUT}/statue/start_grids.shp', 'w', newline=chr(10)).write(SGR_.beam_shape(LS.N_GATES, LS.GATE_PITCH, SG_['length'], SG_.get('beam_gap', 0.0)))
                shg_ = f'{P}/statue/start_grids.shp'
            st.append(f'[{gx:.6f} 0.000000 {gz:.6f}] {float(np.arctan2(-bz_, bx_)):.6f} {P}/statue/start_grids.jm {P}/statue/start_grids.png {shg_}')
        else: st.append(f'[{gx:.6f} 0.000000 {gz:.6f}] {PP.statue_ang(*f):.6f} {P}/statue/start_floor.jm {P}/statue/start_floor.png null')
    else:
        for x, y, z, a in G:
            f = np.array([-np.sin(a), -np.cos(a)])
            st.append(statue(x, 0.0, z, PP.statue_ang(*f), 'start_grate', 'start_grate'))      # v14: y 0, the game puts it on the platform
    PY_ = getattr(LT, 'PYLONS', None)
    if PY_:                                       # v32: black pylon inside every turn, same spot each time (turn bisector)
        smp_p = p.samples(1.0); npy_ = 0
        for g in p.segs:
            if g['kind'] != 'T' or g['tag'] in PY_.get('skip', ()): continue   # v71
            sel = (smp_p['s'] >= g['s0']) & (smp_p['s'] <= g['s0'] + g['L']); X_, Z_ = smp_p['x'][sel], smp_p['z'][sel]
            c_ = np.array([g['cx'], g['cz']]); m_ = np.array([X_[len(X_) // 2], Z_[len(Z_) // 2]]); u_ = (m_ - c_) / np.linalg.norm(m_ - c_)
            k_ = 1.0 if abs(g['ang']) > 135 else np.sqrt(2)          # U turn: apex of the inner half circle; 90 deg: corner of the inner edges
            x_, z_ = c_ + u_ * (g['r'] - PY_['half'] - PY_['margin']) * k_
            if PY_.get('points'): x_, z_ = PY_['points'][npy_]      # v33: the user's spots
            npy_ += 1
            j_ = int(np.argmin(np.hypot(smp_p['x'] - x_, smp_p['z'] - z_)))   # v35: logo side (+z) faces the riding line
            a_ = PP.statue_ang(smp_p['x'][j_] - x_, smp_p['z'][j_] - z_)
            tx_ = getattr(LT, 'PYLON_SKINS', {}).get(npy_ - 1, 'pylon_round' if getattr(LT, 'PYLON_MODEL', '') == 'pylon_round' else 'pylon_black')     # v50: sponsor skins
            pm_ = getattr(LT, 'PYLON_MODEL', 'pylon_black')   # v82: round plain pylons (Saint-Georges v26)
            if pm_ != 'pylon_black':
                for e_ in ('jm', 'shp'): shutil.copy(f'{ROOT}/assets/props/{pm_}.{e_}', f'{OUT}/statue/{pm_}.{e_}')
                shutil.copy(f'{ROOT}/assets/props/{tx_}.png', f'{OUT}/statue/{tx_}.png')
            st.append(f'[{x_:.6f} 0.000000 {z_:.6f}] {a_:.6f} {P}/statue/{pm_}.jm {P}/statue/{tx_}.png {P}/statue/{pm_}.shp')
    if getattr(LT, 'RAILS', None):                # v75 (Saint-Georges v19): wooden barriers following the ground (one mesh each)
        import rail_wood as RWD
        img_, pal_ = RWD.rail_texture(); img_.save(f'{OUT}/statue/rail_wood.png')
        def gnd_(x, z):
            fx, fz = x / S, z / S; j, i = int(fx), int(fz); a, b = fx - j, fz - i
            return float(H[i, j] * (1 - a) * (1 - b) + H[i, j + 1] * a * (1 - b) + H[i + 1, j] * (1 - a) * b + H[i + 1, j + 1] * a * b)
        for k_, RL_ in enumerate(LT.RAILS):
            ln_ = np.array(RL_['line']); org_ = RL_['origin']
            if getattr(LT, 'CONCRETE_WALL', None) and not hasattr(LT, 'WALLS'):  # v84 (Saint-Georges v29): blocks instead of the barrier (v30: own lines, see WALLS)
                import concrete_blocks as CBK_
                CBK_.block_texture().save(f'{OUT}/statue/concrete_block.png'); rr_ = LT.CONCRETE_WALL.get('r', 3.0)
                g_out = lambda x, z: min(gnd_(x + dx, z + dz) for dx in (-rr_, 0, rr_) for dz in (-rr_, 0, rr_))
                g_in = lambda x, z: max(gnd_(x + dx, z + dz) for dx in (-rr_, 0, rr_) for dz in (-rr_, 0, rr_))
                CBK_.wall_mesh(ln_, gnd_, gnd_, org_).write(f'{OUT}/statue/cwall_{k_}.jm', (0, 0, 0, 0, 0))
                st.append(f"[{org_[0]:.6f} 0.000000 {org_[1]:.6f}] 0.000000 {P}/statue/cwall_{k_}.jm {P}/statue/concrete_block.png null")
                print('concrete wall', k_, 'length %.0f ft' % (len(ln_) - 1)); continue
            RWD.rail_mesh(ln_, gnd_, org_, pal_).write(f'{OUT}/statue/rail_{k_}.jm', (0, 0, 0, 0, 0))
            st.append(f"[{org_[0]:.6f} 0.000000 {org_[1]:.6f}] 0.000000 {P}/statue/rail_{k_}.jm {P}/statue/rail_wood.png null")
            print('rail', k_, 'length %.0f ft, ground under origin %.2f ft (flat: %.2f)' % (len(ln_) - 1, gnd_(*org_), max(abs(gnd_(org_[0] + dx, org_[1] + dz) - gnd_(*org_)) for dx in (-3, 3) for dz in (-3, 3))))
    for k_, WL_ in enumerate(getattr(LT, 'WALLS', []) or []):   # v85 (Saint-Georges v30, user): concrete block wall = the side of the landing face
        import concrete_blocks as CBK_
        CW_ = LT.CONCRETE_WALL; CBK_.block_texture().save(f'{OUT}/statue/concrete_block.png')
        def gnd2_(x, z):
            fx, fz = x / S, z / S; j, i = int(fx), int(fz); a, b = fx - j, fz - i
            return float(H[i, j] * (1 - a) * (1 - b) + H[i, j + 1] * a * (1 - b) + H[i + 1, j] * (1 - a) * b + H[i + 1, j + 1] * a * b)
        ln_ = np.array(WL_['line']); org_ = np.array(WL_['origin'])   # world coords (as RAILS)
        rg_ = np.array(WL_['rgt']); lo_in = CW_.get('in_drop', 1.0)
        gout_ = lambda x, z: gnd2_(x - rg_[0] * 0.6, z - rg_[1] * 0.6)
        WS_ = getattr(LT, 'WALL_STAIR', {}); ow0_ = np.array(WL_['o']); dlw_ = np.array(WL_['dl'])
        def gin_(x, z):                                            # top layer level with the dirt (no block standing proud), stair end
            t_ = float(B.wall_stair_top(np.array([(x - ow0_[0]) * dlw_[0] + (z - ow0_[1]) * dlw_[1]]), WS_)[0])
            return min(gnd2_(x, z) - lo_in, t_ - 0.3)
        CBK_.wall_mesh(ln_, gout_, gin_, org_, side=1).write(f'{OUT}/statue/cwall_{k_}.jm', (0, 0, 0, 0, 0))
        shp_ = 'null'; rows_ = []
        if CW_.get('shp'):                          # collision: spheres inside the blocks, every 2 ft, up to the dirt level
            g0_ = gout_(*org_); R_ = CBK_.BL['D'] / 2
            for q_ in ln_[::2]:
                c_ = q_ + rg_ * R_; yb_ = gout_(*q_); yt_ = gnd2_(*(q_ + rg_ * (CBK_.BL['D'] + 0.3)))
                for y_ in np.arange(yb_ + R_, max(yb_ + R_, yt_ - 0.3) + 0.01, R_ * 1.4):
                    rows_.append(f'{c_[0] - org_[0]:.4f} {y_ - g0_:.4f} {c_[1] - org_[1]:.4f} {R_:.3f} 1.0 400 40')
            open(f'{OUT}/statue/cwall_{k_}.shp', 'w', newline=chr(10)).write(chr(10).join([str(len(rows_))] + rows_) + chr(10)); shp_ = f'{P}/statue/cwall_{k_}.shp'
        st.append(f"[{org_[0]:.6f} 0.000000 {org_[1]:.6f}] 0.000000 {P}/statue/cwall_{k_}.jm {P}/statue/concrete_block.png {shp_}")
        print('concrete wall', k_, 'length %.0f ft' % (len(ln_) - 1), 'spheres', len(rows_))
        WT_ = getattr(LT, 'WALL_TARPS', None)
        if WT_ and LT.WALL_TOP:                     # v86 (Saint-Georges v31, user): sponsor tarps hung on the block wall
            import stt_ads as ADw_
            if not os.path.exists(f'{OUT}/statue/ad_tarp.jm'): shutil.copy(f'{ROOT}/assets/props/ad_tarp.jm', f'{OUT}/statue/ad_tarp.jm')
            o_w = np.array(WL_['o']); dl_w = np.array(WL_['dl']); out_w = -rg_                   # outward = away from the lane
            a_w = float(np.arctan2(out_w[0], out_w[1]))                                           # statue local +z -> (sin a, cos a) = outward
            jm_ = open(f'{OUT}/statue/ad_tarp.jm').read().split('\n'); nv_ = int(jm_[2].split()[0]); dz_o = 3.0   # v86 (v33): tarp moved back onto the wall
            ks_ = WT_.get('scale', 1.0); y0t_ = 0.85
            for i_ in range(3, 3 + nv_):
                v_ = [float(t_) for t_ in jm_[i_].split()]; v_[0] *= ks_; v_[1] = WT_['y'] + y0t_ + (v_[1] - y0t_) * ks_; v_[2] = v_[2] - 0.43 - dz_o + 0.06
                jm_[i_] = ' '.join(f'{t_:.6f}' for t_ in v_)
            # v86 (v34): the tarps where the wall has its 4th row (the stair end and the low up-face have fewer layers)
            def wtop_(u_):
                q_ = o_w + dl_w * u_ + out_w * (CW_['off'] - 1.3); return np.ceil(max(0.0, gin_(*q_)) / 2.62) * 2.62   # just inside the wall
            need_ = WT_['y'] + y0t_ + 2.4 * ks_ + 0.1; sp_ = 7.2 * ks_ + 0.6; best_ = None
            for c_ in np.arange(LT.WALL_TOP[0] - 14.0, LT.WALL_TOP[0] + 10.0, 0.5):
                us_ = [c_ + k_ * sp_ for k_ in (-1, 0, 1)]
                m_ = min(min(wtop_(u_ + d_) for d_ in (-3.6 * ks_, 0.0, 3.6 * ks_)) for u_ in us_)
                for u_ in us_:                              # the anchor (3 ft in front of the wall) on flat ground at 0 (no lift, no tilt)
                    qa_ = o_w + dl_w * u_ + out_w * (CW_['off'] + dz_o)
                    if max(abs(gnd2_(qa_[0] + ex_, qa_[1] + ez_)) for ex_ in (-1.5, 0, 1.5) for ez_ in (-1.5, 0, 1.5)) > 0.3: m_ = -1.0
                if m_ >= need_ and (best_ is None or abs(c_ - LT.WALL_TOP[0]) < abs(best_ - LT.WALL_TOP[0])): best_ = c_
            if best_ is None: best_ = LT.WALL_TOP[0]; print('wall tarps: no room on the 4th row, put at the top')
            du_list = [best_ + k_ * sp_ - LT.WALL_TOP[0] for k_ in (-1, 0, 1)]
            open(f'{OUT}/statue/wall_tarp.jm', 'w', newline='\n').write('\n'.join(jm_))
            for nm_ in set(WT_['names']) | ({getattr(LT, 'MOUND_TARP', {}).get('name')} - {None}):   # v87 (v36, user): no eyelet dots
                ADw_.tarp_texture(nm_, eyelets=False).save(f'{OUT}/statue/adx_{nm_}.png')
            for nm_, du_ in zip(WT_['names'], du_list):
                if False:
                    p_ = f'{ROOT}/assets/props/ad_{nm_}.png'
                    (shutil.copy(p_, f'{OUT}/statue/ad_{nm_}.png') if os.path.exists(p_) else ADw_.tarp_texture(nm_).save(f'{OUT}/statue/ad_{nm_}.png'))
                q_ = o_w + dl_w * (LT.WALL_TOP[0] + du_) + out_w * (CW_['off'] + dz_o)
                st.append(f"[{q_[0]:.6f} 0.000000 {q_[1]:.6f}] {a_w:.6f} {P}/statue/wall_tarp.jm {P}/statue/adx_{nm_}.png null")
            print('wall tarps', len(WT_['names']))
        MT_ = getattr(LT, 'MOUND_TARP', None)
        if MT_ and LT.WALL_TOP:                     # v86 (Saint-Georges v31, user): an RBT tarp laid on the other flank of the mound
            from props_usland import Mesh as Mm_
            o_w = np.array(WL_['o']); dl_w = np.array(WL_['dl']); rgw_ = np.array(WL_['rgt']); m_ = Mm_(1024, 512)
            us_ = np.linspace(MT_['du'][0], MT_['du'][1], 16); hs_ = np.linspace(MT_['h'][1], MT_['h'][0], 16); offs_ = np.arange(MT_['off'][0], MT_['off'][1], 0.05)
            G_ = np.zeros((len(us_), len(hs_), 3))
            for i_, du_ in enumerate(us_):
                base_ = o_w + dl_w * (LT.WALL_TOP[0] + du_); prof_ = np.array([gnd2_(*(base_ + rgw_ * f_)) for f_ in offs_])
                for j_, h_ in enumerate(hs_):
                    k_ = int(np.argmax(prof_ < h_)); f_ = offs_[k_] + 0.35                   # first point going out where the flank is below h, lifted off it
                    q_ = base_ + rgw_ * f_; G_[i_, j_] = (q_[0], h_, q_[1])
            q0_ = o_w + dl_w * LT.WALL_TOP[0] - rgw_ * (CW_['off'] + 6.0); org_m = np.array([q0_[0], 0.0, q0_[1]]); g0m_ = gnd2_(org_m[0], org_m[2])   # v86: flat ground (no tilt)
            for i_ in range(len(us_) - 1):
                for j_ in range(len(hs_) - 1):
                    P4 = [G_[i_, j_], G_[i_ + 1, j_], G_[i_ + 1, j_ + 1], G_[i_, j_ + 1]]
                    P4 = [np.array([p_[0] - org_m[0], p_[1] - g0m_, p_[2] - org_m[2]]) for p_ in P4]
                    nrm_ = np.cross(P4[1] - P4[0], P4[3] - P4[0]); nrm_ /= np.linalg.norm(nrm_) + 1e-9
                    if nrm_ @ np.array([rgw_[0], 0, rgw_[1]]) < 0: nrm_ = -nrm_
                    UV = [m_.uv_px(1024 * (a_ / (len(us_) - 1)), 341 * b_ / (len(hs_) - 1)) for a_, b_ in ((i_, j_), (i_ + 1, j_), (i_ + 1, j_ + 1), (i_, j_ + 1))]
                    m_.tri_fan(P4, nrm_, UV)
            m_.write(f'{OUT}/statue/mound_tarp.jm', (0, 0, 0, 0, 0))
            if not os.path.exists(f"{OUT}/statue/adx_{MT_['name']}.png"):
                import stt_ads as ADm_; ADm_.tarp_texture(MT_['name'], eyelets=False).save(f"{OUT}/statue/adx_{MT_['name']}.png")
            st.append(f"[{org_m[0]:.6f} 0.000000 {org_m[2]:.6f}] 0.000000 {P}/statue/mound_tarp.jm {P}/statue/adx_{MT_['name']}.png null")
            print('mound tarp', MT_['name'])
    DC_ = getattr(LT, 'DECOR', None)                # v79 (Saint-Georges v23): trees (billboards), pond water, buildings
    if DC_:
        import json as js_
        dj_ = js_.load(open(f"{ROOT}/{DC_['file']}")); rgt_ = np.random.default_rng(79); tb_ = []
        RDt = getattr(LT, 'ROAD', None); BLt = getattr(LT, 'BUILDINGS', [])
        for tx_, tz_ in dj_['trees']:
            if RDt and float(B.road_dist(np.array([tx_]), np.array([tz_]))[0]) < 8.0 + 9.0: continue            # v80: no tree on the roads
            if any(abs(tx_ - b_['c'][0]) < b_.get('half', (19, 11))[0] + 10 and abs(tz_ - b_['c'][1]) < b_.get('half', (19, 11))[1] + 10 for b_ in BLt): continue
            sz_ = rgt_.uniform(*DC_['tree_size']); tex_ = DC_['tree_tex'][int(rgt_.integers(len(DC_['tree_tex'])))]
            tb_.append(f"[{tx_ + LT.STT_ORIGIN[0]:.6f} -1.000000 {tz_ + LT.STT_ORIGIN[1]:.6f}] {sz_:.6f} 1.000000 {tex_}")
        open(f'{OUT}/billboards', 'a', newline='\n').write('\n'.join(tb_) + '\n'); print('trees', len(tb_))
        PD_ = getattr(LT, 'POND', None)
        if PD_:                                     # water: a flat grid of 4 ft cells inside the bank, at the water level
            from matplotlib.path import Path as MP_
            from props_usland import Mesh as Mesh_, palette as pal_f
            from PIL import Image as Im_
            poly_ = np.array(dj_['pond']); mp_ = MP_(poly_); org_ = (poly_[:, 0].min() - 12.0, poly_[:, 1].mean())
            wimg = Im_.new('RGB', (256, 256), PD_['water_rgb']); wp = pal_f(wimg, ['water'], [PD_['water_rgb']]); wimg.save(f'{OUT}/statue/pond_water.png')
            mw = Mesh_(256, 256); uvw_ = mw.uv_px(*wp['water'][1]); cell = 4.0; nq = 0
            dmin_ = lambda q: float(np.min(np.hypot(poly_[:, 0] - q[0], poly_[:, 1] - q[1])))
            for cx_ in np.arange(poly_[:, 0].min(), poly_[:, 0].max(), cell):
                for cz_ in np.arange(poly_[:, 1].min(), poly_[:, 1].max(), cell):
                    q_ = (cx_ + cell / 2, cz_ + cell / 2)
                    if not mp_.contains_point(q_) or dmin_(q_) < PD_['bank'] - 3.0: continue
                    y_ = -PD_['drop']; P_ = [np.array([cx_ - org_[0], y_, cz_ - org_[1]]), np.array([cx_ + cell - org_[0], y_, cz_ - org_[1]]),
                                            np.array([cx_ + cell - org_[0], y_, cz_ + cell - org_[1]]), np.array([cx_ - org_[0], y_, cz_ + cell - org_[1]])]
                    mw.tri_fan(P_, np.array([0, 1.0, 0]), [uvw_] * 4); nq += 1
            mw.write(f'{OUT}/statue/pond_water.jm', (0, 0, 0, 0, 0))
            st.append(f"[{org_[0] + LT.STT_ORIGIN[0]:.6f} 0.000000 {org_[1] + LT.STT_ORIGIN[1]:.6f}] 0.000000 {P}/statue/pond_water.jm {P}/statue/pond_water.png null")
            print('pond water cells', nq, 'origin ground %.2f' % float(h_at(H, org_[0] + LT.STT_ORIGIN[0], org_[1] + LT.STT_ORIGIN[1])))
        GP_ = getattr(LT, 'GROUND_PHOTO', None)
        if GP_:                                     # v83 (Saint-Georges v27): the real fields (IGN photo, scripts/sgm_fields.py) as
            from props_usland import Mesh as Mesh_   # ground-draped meshes, one per chunk (yaw 0, model x/z = world x/z - origin)
            from PIL import Image as Im_
            F_ = np.asarray(Im_.open(f"{ROOT}/{GP_['file']}").convert('RGBA')); r_ = GP_['res']; nF = F_.shape[0]; ch_ = GP_['chunk']
            cpx = int(round(ch_ / r_)); cl_ = GP_['cell']; cp_ = int(round(cl_ / r_)); ngp = 0; ncl = 0
            for f_ in os.listdir(f'{OUT}/statue'):
                if f_.startswith('field_'): os.remove(f'{OUT}/statue/{f_}')
            for i0 in range(0, nF, cpx):
                for j0 in range(0, nF, cpx):
                    blk = F_[i0:i0 + cpx, j0:j0 + cpx]
                    if (blk[..., 3] > 0).sum() < 64: continue
                    tex_ = np.zeros((cpx, cpx, 4), np.uint8); tex_[:blk.shape[0], :blk.shape[1]] = blk
                    x0_, z0_ = GP_['x0'] + j0 * r_, GP_['z0'] + i0 * r_
                    ii_, jj_ = np.nonzero(tex_[..., 3]); k_ = len(ii_) // 2                     # origin on a field pixel (flat ground)
                    org_ = (x0_ + (jj_[k_] + 0.5) * r_, z0_ + (ii_[k_] + 0.5) * r_)
                    gw_ = lambda x, z: float(h_at(H, x + LT.STT_ORIGIN[0], z + LT.STT_ORIGIN[1]))
                    g0_ = gw_(*org_); mf = Mesh_(cpx, cpx)
                    for a_ in range(0, cpx, cp_):
                        for b_ in range(0, cpx, cp_):
                            if not tex_[a_:a_ + cp_, b_:b_ + cp_, 3].any(): continue
                            P_, U_ = [], []
                            for pa, pb in ((a_, b_), (a_, b_ + cp_), (a_ + cp_, b_ + cp_), (a_ + cp_, b_)):
                                x_, z_ = x0_ + pb * r_, z0_ + pa * r_
                                P_.append(np.array([x_ - org_[0], gw_(x_, z_) - g0_ + GP_['lift'], z_ - org_[1]])); U_.append(mf.uv_px(pb, pa))
                            mf.tri_fan(P_, np.array([0, 1.0, 0]), U_); ncl += 1
                    nm_ = f'field_{i0 // cpx}_{j0 // cpx}'
                    mf.write(f'{OUT}/statue/{nm_}.jm', (0, 0, 0, 0, 0)); Im_.fromarray(tex_, 'RGBA').save(f'{OUT}/statue/{nm_}.png')
                    st.append(f"[{org_[0] + LT.STT_ORIGIN[0]:.6f} 0.000000 {org_[1] + LT.STT_ORIGIN[1]:.6f}] 0.000000 {P}/statue/{nm_}.jm {P}/statue/{nm_}.png null")
                    ngp += 1
                    if abs(g0_) > 0.05: print('WARNING field chunk', nm_, 'origin ground %.2f' % g0_)
            print('field chunks', ngp, 'cells', ncl)
        for BL_ in getattr(LT, 'BUILDINGS', []):
            for e_ in ('jm', 'png'): shutil.copy(f"{ROOT}/assets/props/{BL_['model']}.{e_}", f"{OUT}/statue/{BL_['model']}.{e_}")
            if BL_.get('cables'):                     # v83 (Saint-Georges v28): black guy cables arch -> mound slopes
                import arch_tube as ART
                ab_ = np.radians(BL_['ang']); ex_ = np.array([np.cos(ab_), np.sin(ab_)]); ez_ = np.array([-np.sin(ab_), np.cos(ab_)])
                cw_ = np.array(BL_['c'], float) + LT.STT_ORIGIN; g0_ = float(h_at(H, *cw_)); cab_ = []
                for t_c in (0.30, 0.70):
                    for sd_ in (1, -1):
                        a3 = np.array(ART.arch_attach(t_c, sd_), float); sx_ = np.sign(a3[0])
                        ex2, ez2 = sx_ * BL_.get('cable_out', 30.0), sd_ * BL_.get('cable_along', 14.0)
                        w_ = cw_ + ex_ * ex2 + ez_ * ez2
                        cab_.append((tuple(a3), (ex2, float(h_at(H, *w_)) - g0_, ez2)))
                mA_, iA_ = ART.arch_model(cab_); mA_.write(f"{OUT}/statue/{BL_['model']}.jm", (0, 0, 0, 0, 0)); iA_.save(f"{OUT}/statue/{BL_['model']}.png")
                print('arch cables', [(round(e[1][0]), round(e[1][1], 1), round(e[1][2])) for e in cab_])
            sh_ = 'null'                              # v83 (Saint-Georges v27): collision when the model has a .shp (rider gate box / ramps)
            if os.path.exists(f"{ROOT}/assets/props/{BL_['model']}.shp"):
                shutil.copy(f"{ROOT}/assets/props/{BL_['model']}.shp", f"{OUT}/statue/{BL_['model']}.shp"); sh_ = f"{P}/statue/{BL_['model']}.shp"
            a_ = np.radians(BL_['ang']); st.append(f"[{BL_['c'][0] + LT.STT_ORIGIN[0]:.6f} 0.000000 {BL_['c'][1] + LT.STT_ORIGIN[1]:.6f}] {PP.statue_ang(-np.sin(a_), np.cos(a_)):.6f} {P}/statue/{BL_['model']}.jm {P}/statue/{BL_['model']}.png {sh_}")
    for pr_ in getattr(LT, 'PROPS', []) or []:     # v73 (Saint-Georges v17): wooden barriers up the finish landing, cone
        for e in ('jm', 'png'): shutil.copy(f"{ROOT}/assets/props/{pr_['model']}.{e}", f"{OUT}/statue/{pr_['model']}.{e}")
        st.append(f"[{pr_['x']:.6f} 0.000000 {pr_['z']:.6f}] {PP.statue_ang(*pr_['f']):.6f} {P}/statue/{pr_['model']}.jm {P}/statue/{pr_['model']}.png null")
    # v35: straw bales (user's white rectangles), long axis = model x; statue +x -> (cos a, -sin a)
    for b_ in getattr(LT, 'BALES', []):            # v78: optional 4th item = texture (bale_paille = real straw colour)
        bx_, bz_, ba_ = b_[:3]; btx_ = b_[3] if len(b_) > 3 else 'bale_straw'
        if btx_ != 'bale_straw': shutil.copy(f'{ROOT}/assets/props/{btx_}.png', f'{OUT}/statue/{btx_}.png')
        bm_ = 'bale_straw'
        if os.path.exists(f'{ROOT}/assets/props/{btx_}.jm'):   # v83 (Saint-Georges v28): own model (real hay bale, twines)
            bm_ = btx_
            for e_ in ('jm', 'shp'): shutil.copy(f'{ROOT}/assets/props/{btx_}.{e_}', f'{OUT}/statue/{btx_}.{e_}')
        t_ = np.radians(ba_); a_ = float(np.arctan2(-np.sin(t_), np.cos(t_)))
        st.append(f'[{bx_:.6f} 0.000000 {bz_:.6f}] {a_:.6f} {P}/statue/{bm_}.jm {P}/statue/{btx_}.png {P}/statue/{bm_}.shp')
    BD_ = getattr(LT, 'BOUDINS', None); nbd = 0
    if BD_:
        import stt_props as SP_
        segL = SP_.BOUDIN['L']
        def tube_row(p0, p1, off, sides=(1, -1), model='boudin_black', segL=segL, tex=None):
            rows_ = []
            d0 = np.array(p1, float) - np.array(p0, float); Ld = np.linalg.norm(d0); d0 /= Ld; nn = np.array([-d0[1], d0[0]])
            k_ = max(1, int(round(Ld / segL))); a_ = float(np.arctan2(-d0[1], d0[0]))
            for sgn in sides:
                for q in range(k_):
                    c = np.array(p0, float) + d0 * (Ld / 2 - (k_ * segL) / 2 + (q + 0.5) * segL) + nn * sgn * off
                    tx_ = tex[q % len(tex)] if tex else model                       # v38: logo textures alternated
                    rows_.append(f'[{c[0]:.6f} 0.000000 {c[1]:.6f}] {a_:.6f} {P}/statue/{model}.jm {P}/statue/{tx_}.png {P}/statue/{model}.shp')
            return rows_
        W_ = BD_.get('whoops')
        if W_:                                     # v36: one side only, explicit x range along the lane (user's line)
            for g in p.segs:
                if g['kind'] != 'S' or not g.get('tag', '').startswith(W_['tag']): continue
                c_, s_ = np.cos(g['t']), np.sin(g['t']); xa_, xb_ = W_['x']
                ua_, ub_ = (xa_ - g['x0']) / c_, (xb_ - g['x0']) / c_                 # this lane runs along x
                rows = tube_row((g['x0'] + ua_ * c_, g['z0'] + ua_ * s_), (g['x0'] + ub_ * c_, g['z0'] + ub_ * s_), W_['off'], sides=(W_['side'],),
                                model=W_.get('model', 'boudin_black'), segL=SP_.BOUDIN['L'], tex=W_.get('tex'))
                st.extend(rows); nbd += len(rows)
        done_tex_ = set()
        for ln_ in BD_.get('lines', []):           # v75 (Saint-Georges v19): straight logo rows between two local points
            q0_ = np.array(ln_['p0']) + LT.STT_ORIGIN; q1_ = np.array(ln_['p1']) + LT.STT_ORIGIN
            tl_ = ln_.get('tex', BD_.get('tex'))
            rows = tube_row(q0_, q1_, 0.0, sides=(1,), model=BD_.get('model', 'boudin_logo'), segL=BD_.get('seg', SP_.BOUDIN['L']), tex=tl_)
            for e_ in ('jm', 'shp'):                    # v83: own boudin model (Saint-Georges v28: 3 in one)
                if os.path.exists(f"{ROOT}/assets/props/{BD_.get('model', 'boudin_logo')}.{e_}"): shutil.copy(f"{ROOT}/assets/props/{BD_.get('model', 'boudin_logo')}.{e_}", f"{OUT}/statue/{BD_.get('model', 'boudin_logo')}.{e_}")
            st.extend(rows); nbd += len(rows)
            for tx_ in sorted(set(tl_ or ()) - done_tex_):     # v85: each texture once (several lines share them)
                done_tex_.add(tx_)
                shutil.copy(f"{ROOT}/assets/props/{tx_}.png", f"{OUT}/statue/{tx_}.png")
                if BD_.get('grey_ends'):                # v83 (Saint-Georges v28): ends (rows 960..) grey vinyl
                    import stt_props as SPg_
                    q_ = np.asarray(Image.open(f"{OUT}/statue/{tx_}.png").convert('RGB')).astype(float)
                    q_[960:] = SPg_._vinyl(q_.shape[0] - 960, q_.shape[1], 60, 30, 45, amp=4, base=(118, 120, 124))
                    Image.fromarray(np.clip(q_, 0, 255).astype(np.uint8)).save(f"{OUT}/statue/{tx_}.png")
        F_ = BD_.get('fmx'); R2_ = getattr(LT, 'FMX_RAMP', None)
        if F_ and F_.get('p0'):                    # v37: the user's line, explicit ends
            rows = tube_row(F_['p0'], F_['p1'], 0.0, sides=(1,), model=F_.get('model', 'boudin_black'), segL=SP_.BOUDIN['L'], tex=F_.get('tex'))
            st.extend(rows); nbd += len(rows)
        elif F_ and R2_:
            lip = np.array(R2_['lip']) + np.array(LT.STT_ORIGIN); d_ = np.array(R2_['aim']) - np.array(R2_['lip']); d_ = d_ / np.linalg.norm(d_)
            # landing start: first point after the lip where the ground rises 1 ft above the gap floor
            land = None
            for t_ in np.arange(8.0, 120.0, 0.5):
                q_ = lip + d_ * t_; hq = float(H[int(round(q_[1] / S)), int(round(q_[0] / S))])
                h0 = float(H[int(round((lip + d_ * 6.0)[1] / S)), int(round((lip + d_ * 6.0)[0] / S))])
                if hq > h0 + 1.0: land = t_; break
            if land:
                rows = tube_row(lip + d_ * F_['start'], lip + d_ * (land - F_['end']), F_['off'], sides=(1,), model=F_.get('model', 'boudin_black'),
                                segL=SP_.BOUDIN['L'])   # v36: plain model has no gap: segments touching
                st.extend(rows); nbd += len(rows)
                print('fmx gap', round(land, 1), 'ft')
        print('boudins', nbd)
    SBD = getattr(LT, 'START_BOUDINS', None)
    if SBD:                                        # v50: start-only boudins along the user's lines (no collision, see nofrills.js)
        import stt_ads as AD3, stt_props as SP3
        segL_ = SP3.BOUDIN['L']; nsb = 0; blk_ = AD3.START_BOUDINS_TEX['black']
        for line in SBD['lines']:
            pts_ = np.array(line, float); sv_ = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts_, axis=0), axis=1))]
            k_ = max(1, int(round(sv_[-1] / segL_)))
            for q in range(k_):
                s_ = (q + 0.5) * sv_[-1] / k_; i_ = min(int(np.searchsorted(sv_, s_, 'right')) - 1, len(pts_) - 2)
                d_ = pts_[i_ + 1] - pts_[i_]; d_ /= np.linalg.norm(d_); c = pts_[i_] + d_ * (s_ - sv_[i_])
                pat_ = [n_ for n_, k2 in SBD['pattern'] for _ in range(k2)]          # v51: 10 / 10 / 10
                tx_ = pat_[nsb % len(pat_)]
                hs_ = [float(h_at(H, *(c + d_ * a2 + np.array([-d_[1], d_[0]]) * b2))) for a2 in (-2.9, 0, 2.9) for b2 in (-1.2, 0, 1.2)]
                if max(hs_) - min(hs_) > 0.15: print('  start boudin not flat at', c.round(1), round(max(hs_) - min(hs_), 2))
                st.append(f'[{c[0]:.6f} 0.000000 {c[1]:.6f}] {float(np.arctan2(-d_[1], d_[0])):.6f} {P}/statue/boudin_logo.jm {P}/statue/startb_{tx_}.png null')   # v53: no collision again (with startb.shp the game did not move them)
                nsb += 1
        print('start boudins', nsb)
    FS_ = getattr(LT, 'FMX_STAKES', None); R3_ = getattr(LT, 'FMX_RAMP', None)
    if FS_ and R3_:                                # v35: yellow stakes on both ends of the steel ramp lip (on top of it)
        lip = np.array(R3_['lip']) + np.array(LT.STT_ORIGIN); d_ = np.array(R3_['aim']) - np.array(R3_['lip']); d_ = d_ / np.linalg.norm(d_)
        nn = np.array([-d_[1], d_[0]]); hw = 2.0 - FS_['inset']
        for sgn in (1, -1):
            q_ = lip - d_ * FS_['back'] + nn * sgn * hw
            st.append(f'[{q_[0]:.6f} {FS_["y"]:.6f} {q_[1]:.6f}] {PP.statue_ang(d_[0], d_[1]):.6f} {P}/statue/stake_yellow.jm {P}/statue/stake_yellow.png null')
    # v28: yellow marker stakes on the crest of every bump, both lane edges (drone photos)
    SK = getattr(LT, 'STAKES', None); nsk = 0; bb_sk = []
    if SK:
        from scipy.signal import find_peaks
        for g in p.segs:
            if g['kind'] != 'S': continue
            c_, s_ = np.cos(g['t']), np.sin(g['t'])
            for prof, u0, name in g['sections']:
                pk, _ = find_peaks(np.r_[0, prof, 0], prominence=SK['prom']); pk = pk - 1
                skip = [(a_, b_) for n_, a_, b_, h_ in LS.COMBOS[name]['items'] if n_.startswith(('trapeze',))]   # v36 (user): stakes ON the dirt freestyle take-off again; v29: none on kicker / landing
                for k in pk:
                    if any(a_ <= k * 0.1 <= b_ for a_, b_ in skip): continue
                    top = prof >= prof[k] - 0.15; a_ = k; b_ = k
                    while a_ > 0 and top[a_ - 1]: a_ -= 1
                    while b_ < len(prof) - 1 and top[b_ + 1]: b_ += 1
                    us = [a_ * 0.1 + 0.5, b_ * 0.1 - 0.5] if (b_ - a_) * 0.1 > SK['table'] else [k * 0.1]
                    it_ = [n_ for n_, a2, b2, h_ in LS.COMBOS[name]['items'] if a2 <= k * 0.1 <= b2]
                    if it_ and it_[0] in SK.get('tables', ()):   # v41: tables: both ends of the top
                        topt = prof >= prof[k] - SK['table_drop']; a_ = k; b_ = k
                        while a_ > 0 and topt[a_ - 1]: a_ -= 1
                        while b_ < len(prof) - 1 and topt[b_ + 1]: b_ += 1
                        us = [a_ * 0.1 + 1.6, b_ * 0.1 - 0.5]
                    for uu in us:
                        for sg in (-1, 1):
                            x_ = g['x0'] + (u0 + uu) * c_ - sg * SK['v'] * s_; z_ = g['z0'] + (u0 + uu) * s_ + sg * SK['v'] * c_
                            if SK.get('sprite'):           # v41: billboard, always upright
                                bb_sk.append(f'[{x_:.6f} 0.000000 {z_:.6f}] {SK["sprite"]:.6f} 1.000000 {P}/billboard/stake_sprite.png'); nsk += 1
                            else:
                                st.append(f'[{x_:.6f} 0.000000 {z_:.6f}] {PP.statue_ang(c_, s_):.6f} {P}/statue/stake_yellow.jm {P}/statue/stake_yellow.png null'); nsk += 1   # v29: flat paddle facing the riders
        for g in p.segs:                           # v42 (user): split bumps (L2 1st take-off) are drawn apart, the centre
            if g['kind'] != 'S': continue          # profile is flat there: a stake on the crest of each half
            c_, s_ = np.cos(g['t']), np.sin(g['t'])
            for prof, u0, name in g['sections']:
                for st0, pl_, pr_ in LS.SPLITS.get(name, []):
                    for sg, ph_ in ((-1, pl_), (1, pr_)):
                        uu = u0 + st0 + int(np.argmax(ph_)) * 0.1
                        x_ = g['x0'] + uu * c_ - sg * SK['v'] * s_; z_ = g['z0'] + uu * s_ + sg * SK['v'] * c_
                        bb_sk.append(f'[{x_:.6f} 0.000000 {z_:.6f}] {SK["sprite"]:.6f} 1.000000 {P}/billboard/stake_sprite.png'); nsk += 1
        print('stakes', nsk)
        if bb_sk:
            os.makedirs(f'{OUT}/billboard', exist_ok=True); shutil.copy(f'{ROOT}/assets/props/stake_sprite.png', f'{OUT}/billboard/stake_sprite.png')
            open(f'{OUT}/billboards', 'a', newline='\n').write('\n'.join(bb_sk) + '\n')
    # v28: blue nets on the outside of the turns asked by the user, on the berm crest (flat part: r + half lane + flat_off)
    NT = getattr(LT, 'NETS', None); nnet = 0
    if getattr(LT, 'NET_SHP', None):               # v85 (Saint-Georges v30, user): softer nets on this track only
        import stt_props as SPn_; SPn_.NET_SHP.update(LT.NET_SHP)
    for f_ in os.listdir(f'{OUT}/statue'):          # v34: no stale net from an earlier export (a turn may lose its net)
        if f_.startswith('net_') and f_.endswith(('.jm', '.shp')): os.remove(f'{OUT}/statue/{f_}')
    if NT:
        smp_ = p.samples(1.0); TW_ = 30.4
        for g in p.segs:
            if g['kind'] != 'T' or (NT['turns'] != 'all' and g['tag'] not in NT['turns']) or g['tag'] in NT.get('skip', ()): continue
            sel = (smp_['s'] >= g['s0']) & (smp_['s'] <= g['s0'] + g['L'])
            cc = np.array([g['cx'], g['cz']]) + np.array(getattr(LT, 'BERM_OFFSET', {}).get(g['tag'], (0.0, 0.0))); U_, crs = [], []   # v82: on the (offset) berm
            for x_, z_ in zip(smp_['x'][sel], smp_['z'][sel]):
                u = np.array([x_, z_]) - cc; u /= np.linalg.norm(u); U_.append(u)
                rr = np.arange(g['r'], g['r'] + 30, 0.5); hh = np.array([float(h_at(H, *(cc + u * r_))) for r_ in rr])
                k = int(np.argmax(hh))
                if hh[k] - hh[0] > 1.2 and 0 < k < len(hh) - 6 and hh[k] - hh[k + 6] > 0.2: crs.append(rr[k])   # a berm drops behind its crest
            if len(crs) >= 5:
                rc = float(np.median(crs)) + 1.0                 # one radius per turn: just behind the berm crest
                keep = [i for i, u in enumerate(U_) if float(h_at(H, *(cc + u * (rc - 1.0)))) > 1.5]   # the bermed part (half berms: 2nd half)
            else:                                                # v32 (user: a net in EVERY turn): no berm -> just outside the lane
                rc = g['r'] + TW_ / 2 + NT['flat_gap']; keep = []
            if len(keep) < 5: keep = list(range(len(U_)))
            ef_ = NT.get('end', {}).get(g['tag'])          # v78 (Saint-Georges v22): stop the net at a fraction of the turn
            if ef_: keep = [k for k in keep if k <= ef_ * (len(U_) - 1)] or keep
            pts = U_[keep[0]:keep[-1] + 1]
            line = np.array([cc + u * rc for u in pts])
            # v29: ONE continuous net per turn whose bottom follows the ground (user: no more square panels in steps)
            import stt_props
            def gnd(x, z):                                       # bilinear terrain height (world ft)
                fx, fz = x / S, z / S; j, i = int(fx), int(fz); a, b = fx - j, fz - i
                return float(H[i, j] * (1 - a) * (1 - b) + H[i, j + 1] * a * (1 - b) + H[i + 1, j] * (1 - a) * b + H[i + 1, j + 1] * a * b)
            Ls = np.r_[0, np.cumsum(np.linalg.norm(np.diff(line, axis=0), axis=1))]
            sv = np.linspace(0, Ls[-1], max(2, int(Ls[-1] / 1.0) + 1))
            line1 = np.c_[np.interp(sv, Ls, line[:, 0]), np.interp(sv, Ls, line[:, 1])]
            # origin on flat ground (the game puts the object on the ground under its origin and tilts it with the slope there)
            best = None
            for fr in np.linspace(0.0, 0.85, 18):
                for q in (0.5, 0.3, 0.7):
                    o = cc + (line1[int(q * (len(line1) - 1))] - cc) * fr
                    hs = [gnd(o[0] + dx, o[1] + dz) for dx in (-3, 0, 3) for dz in (-3, 0, 3)]
                    sc_ = max(hs) - min(hs)
                    if best is None or sc_ < best[0] - 1e-6: best = (sc_, o)
            org = best[1]
            nm_ = f"net_{''.join(ch for ch in g['tag'] if ch.isalnum())[:24]}"
            m_ = stt_props.net_ribbon(line1, gnd, org, round_posts=NT.get('round_posts', False)); m_.write(f'{OUT}/statue/{nm_}.jm', (0, 0, 0, 0, 0))
            open(f'{OUT}/statue/{nm_}.shp', 'w', newline='\n').write(stt_props.net_shape(line1, gnd, org))   # v31: soft collision
            st.append(f'[{org[0]:.6f} 0.000000 {org[1]:.6f}] 0.000000 {P}/statue/{nm_}.jm {P}/statue/{NT.get("tex", "net_ribbon")}.png {P}/statue/{nm_}.shp'); nnet += 1
            print('net', g['tag'], 'length %.0f ft, origin flatness %.3f ft' % (Ls[-1], best[0]))
        tx_n = NT.get('tex', 'net_ribbon')
        if NT.get('fine'):                              # v83 (Saint-Georges v28): fine black mesh, wood posts (user's photo)
            fn_ = NT['fine'] if isinstance(NT['fine'], dict) else dict(cell=0.13, strand=1, knot=3)
            stt_props.net_ribbon_texture(stt_props.NET_BLACK_FINE, wood=True, **fn_).save(f'{OUT}/statue/{tx_n}.png')
        else: shutil.copy(f'{ROOT}/assets/props/{tx_n}.png', f'{OUT}/statue/{tx_n}.png')   # v71: grey net (Saint-Georges)
        print('nets', nnet)
    fin = cps[normal[-1]]; c = np.array([fin[1], fin[2]]); f = np.array([fin[3], fin[4]]); f /= np.linalg.norm(f); n = np.array([-f[1], f[0]])
    if os.path.exists(f'{OUT}/statue/finish_arch_STT.jm'): os.remove(f'{OUT}/statue/finish_arch_STT.jm')
    # v18: the user's steel FMX ramp (fmxRamp.rar: ramp_50.jm / .png / _norm.png / .shp collision). Model: foot at the origin,
    # rides towards local -z, lip (9 ft) at z = -model_len. Lip put where the dirt ramp lip was, facing the same way.
    R_ = getattr(LT, 'FMX_RAMP', None)
    if R_ and R_.get('model'):
        src = f"{ROOT}/assets/fmx_ramp_user"
        for e in ('.jm', '.png', '_norm.png', '.shp'): shutil.copy(f"{src}/{R_['model']}{e}", f"{OUT}/statue/{R_['model']}{e}")
        d_ = np.array([R_['aim'][0] - R_['lip'][0], R_['aim'][1] - R_['lip'][1]]); d_ /= np.linalg.norm(d_)
        fx_, fz_ = R_['lip'][0] + LT.STT_ORIGIN[0] - d_[0] * R_['model_len'], R_['lip'][1] + LT.STT_ORIGIN[1] - d_[1] * R_['model_len']
        m_ = R_['model']
        st.append(f'[{fx_:.6f} 0.000000 {fz_:.6f}] {PP.statue_ang(-d_[0], -d_[1]):.6f} {P}/statue/{m_}.jm {P}/statue/{m_}.png {P}/statue/{m_}.shp')
    # v20: wooden fence around the dirt area (arena box + start area), in the grass at the foot of the bank
    WB_ = getattr(LT, 'WOOD_BARRIER', None)
    if WB_:                                         # v83 (Saint-Georges v28): wooden barrier (round posts, one top rail) along the
        import rail_wood as RWB_                    # inside of the metal fence, ground-following meshes of ~chunk ft
        from skimage.measure import find_contours
        DFw = np.load(f'{ROOT}/build/{PFX}_dist.npy'); csw = max(find_contours(DFw, WB_['off']), key=len)
        ptw = np.c_[csw[:, 1], csw[:, 0]]; Lw = np.r_[0, np.cumsum(np.linalg.norm(np.diff(ptw, axis=0), axis=1))]
        svw = np.arange(0, Lw[-1], 1.0); ln_w = np.c_[np.interp(svw, Lw, ptw[:, 0]), np.interp(svw, Lw, ptw[:, 1])]
        lxw, lzw = ln_w[:, 0] - LT.STT_ORIGIN[0], ln_w[:, 1] - LT.STT_ORIGIN[1]; kw_ = np.ones(len(ln_w), bool)   # v84: skipped areas
        for x0_, x1_, z0_, z1_ in WB_.get('skip', []): kw_ &= ~((lxw > x0_) & (lxw < x1_) & (lzw > z0_) & (lzw < z1_))
        runs_ = np.split(np.arange(len(ln_w)), np.where(np.diff(kw_.astype(int)) != 0)[0] + 1); runs_ = [r_ for r_ in runs_ if kw_[r_[0]]]
        if len(runs_) > 1 and runs_[0][0] == 0 and runs_[-1][-1] == len(ln_w) - 1: runs_ = [np.r_[runs_[-1], runs_[0]]] + runs_[1:-1]   # closed contour
        def gndw(x, z):
            fx, fz = x / S, z / S; j, i = int(fx), int(fz); a, b = fx - j, fz - i
            return float(H[i, j] * (1 - a) * (1 - b) + H[i, j + 1] * a * (1 - b) + H[i + 1, j] * (1 - a) * b + H[i + 1, j + 1] * a * b)
        img_w, _ = RWB_.rail_texture(); img_w.save(f'{OUT}/statue/rail_wood.png'); nwb = 0
        pieces_ = []
        for r_ in runs_:
            nch = max(1, int(round(len(r_) / WB_['chunk'])))
            pieces_ += [ln_w[r_[int(k_ * len(r_) / nch): int((k_ + 1) * len(r_) / nch) + 1]] for k_ in range(nch)]
        for k_, seg_ in enumerate(pieces_):
            if len(seg_) < 3: continue
            org_ = tuple(seg_[len(seg_) // 2])
            RWB_.rail_round(seg_, gndw, org_).write(f'{OUT}/statue/barrier_{k_}.jm', (0, 0, 0, 0, 0))
            st.append(f"[{org_[0]:.6f} 0.000000 {org_[1]:.6f}] 0.000000 {P}/statue/barrier_{k_}.jm {P}/statue/rail_wood.png null"); nwb += 1
        print('wooden barrier pieces', nwb, 'length %.0f ft' % Lw[-1])
    FE = getattr(LT, 'FENCE', None)
    if FE and FE.get('models', True):              # v69 (Saint-Georges v11): models=False -> no fence (line kept for decals / light)
        for e in ('jm', 'png'): shutil.copy(f"{ROOT}/assets/props/{FE['model']}.{e}", f"{OUT}/statue/{FE['model']}.{e}")
        # v25: the fence follows the line d = off of the bank's distance field (flat terrace), closed, rounded everywhere
        from skimage.measure import find_contours
        DF = np.load(f'{ROOT}/build/{PFX}_dist.npy'); o = FE['off']
        cs = max(find_contours(DF, o), key=len)                          # (row = world z, col = world x), 1 ft grid
        path = [np.array([c_[1] - LT.STT_ORIGIN[0], c_[0] - LT.STT_ORIGIN[1]]) for c_ in cs[::3]] + [np.array([cs[0][1] - LT.STT_ORIGIN[0], cs[0][0] - LT.STT_ORIGIN[1]])]
        seg = [(path[i], path[i + 1]) for i in range(len(path) - 1) if np.linalg.norm(path[i + 1] - path[i]) > 1e-6]
        L_ = np.cumsum([0] + [np.linalg.norm(b - a) for a, b in seg]); m_ = max(1, int(round(L_[-1] / FE['step']))); stp = L_[-1] / m_
        def at(sv):
            i = min(int(np.searchsorted(L_, sv, 'right')) - 1, len(seg) - 1); a, b = seg[i]
            return a + (b - a) * (sv - L_[i]) / max(np.linalg.norm(b - a), 1e-9)
        dfl = lambda q: float(DF[int(q[1] + LT.STT_ORIGIN[1]), int(q[0] + LT.STT_ORIGIN[0])])
        nf = 0; nad = 0; import stt_ads as AD_; vip_bb = []
        vip_q = {}                                 # v45: VIP cut-outs right behind the nearest fence section (no tarp there)
        for vp in getattr(LT, 'VIPS', []):
            qs = [(np.hypot(*((at((q + 0.5) * stp) + np.array(LT.STT_ORIGIN)) - np.array(vp['at']))), q) for q in range(m_)]
            vip_q[min(qs)[1]] = vp
        for q in range(m_):
            pa, pb = at(q * stp), at((q + 1) * stp); c_ = (pa + pb) / 2 + np.array(LT.STT_ORIGIN); t_ = (pb - pa) / np.linalg.norm(pb - pa)
            inw = np.array([-t_[1], t_[0]])
            if dfl((pa + pb) / 2 + inw * 3) > dfl((pa + pb) / 2 - inw * 3): inw = -inw   # v25: inward = towards the track
            st.append(f"[{c_[0]:.6f} 0.000000 {c_[1]:.6f}] {PP.statue_ang(inw[0], inw[1]):.6f} {P}/statue/{FE['model']}.jm {P}/statue/{FE['model']}.png null"); nf += 1
            # v38 (user): an advertising tarp on the track side every `every` sections, logos in turn; none behind the start
            # gates (the START banner goes there)
            gx_, gz_ = LT.START_GATE[0] + LT.STT_ORIGIN[0], LT.START_GATE[1] + LT.STT_ORIGIN[1]
            behind_start = c_[0] < gx_ and abs(c_[1] - gz_) < 52.0
            vp = vip_q.get(q)
            if vp:                                     # v49: the VIP = a billboard 1 ft behind this section (turns to the view)
                from PIL import Image as Im_
                os.makedirs(f'{OUT}/billboard', exist_ok=True)
                im_ = Im_.open(f"{ROOT}/assets/crowd/{vp['img']}.png").convert('RGBA'); im_.resize((512, 512), Im_.LANCZOS).save(f"{OUT}/billboard/{vp['img']}.png")
                pc_ = c_ - inw * 1.0
                vip_bb.append(f"[{pc_[0]:.6f} {-vp['sink']:.6f} {pc_[1]:.6f}] {vp['h']:.6f} {im_.width / im_.height:.6f} {P}/billboard/{vp['img']}.png")
                print('vip', vp['img'], 'at', pc_.round(1))
            if getattr(LT, 'TARPS', True) and (not vp or vp.get('keep_tarp')) and q % AD_.TARP['every'] != AD_.TARP['gap'] and not behind_start:       # v45: every section; v66: LT.TARPS = False -> none
                n_ = AD_.TARP['order'][nad % len(AD_.TARP['order'])]; nad += 1
                st.append(f"[{c_[0]:.6f} 0.000000 {c_[1]:.6f}] {PP.statue_ang(inw[0], inw[1]):.6f} {P}/statue/ad_tarp.jm {P}/statue/ad_{n_}.png null")
        print('fence sections', nf, 'tarps', nad)
        if vip_bb: open(f'{OUT}/billboards', 'a', newline=chr(10)).write(chr(10).join(vip_bb) + chr(10))
        SB_ = getattr(LT, 'START_BANNER', None)
        if SB_:                                    # v39: START banner in front of the fence section right behind the gate centre
            gx_, gz_ = LT.START_GATE[0] + LT.STT_ORIGIN[0], LT.START_GATE[1] + LT.STT_ORIGIN[1]
            hp_ = float(h_at(H, gx_ - 5.0, gz_)); xf_ = gx_ - 5.0                 # v40: big board at the foot of the wall
            while xf_ > gx_ - 80 and float(h_at(H, xf_ - 0.25, gz_)) <= hp_ + SB_['foot_h']: xf_ -= 0.25
            bx_, bz_ = xf_ + SB_['back'], gz_
            mdl_ = SB_.get('model', 'start_board')
            st.append(f"[{bx_:.6f} 0.000000 {bz_:.6f}] {PP.statue_ang(1.0, 0.0):.6f} {P}/statue/{mdl_}.jm {P}/statue/{mdl_}.png null")
            print('start banner at', round(bx_, 1), round(bz_, 1))
    # v25: 3D grass tufts on the grass (outside the fence), random size mix and rotation
    GT = getattr(LT, 'GRASS_TUFTS', None)
    if GT and getattr(LT, 'FENCE', None):
        for gf_ in os.listdir(f'{ROOT}/assets/grass_jgsx'): shutil.copy(f'{ROOT}/assets/grass_jgsx/{gf_}', f'{OUT}/statue/{gf_}')
        DF = np.load(f'{ROOT}/build/{PFX}_dist.npy'); side = DF.shape[0] - 1.0; rt = np.random.default_rng(25); o = LT.FENCE['off']; nt_ = 0
        names = [m for m, _ in GT['models']]; prob = np.array([w for _, w in GT['models']]); prob /= prob.sum()
        for zz in np.arange(GT['step'] / 2, side, GT['step']):
            for xx in np.arange(GT['step'] / 2, side, GT['step']):
                x_, z_ = xx + rt.uniform(-0.45, 0.45) * GT['step'], zz + rt.uniform(-0.45, 0.45) * GT['step']
                if not (8 < x_ < side - 8 and 8 < z_ < side - 8): continue
                dv = DF[int(z_), int(x_)]
                if not (o + GT['dmin'] <= dv <= o + GT['dmax']) or rt.random() > GT['p']: continue
                m_ = names[rt.choice(len(names), p=prob)]
                st.append(f"[{x_:.6f} 0.000000 {z_:.6f}] {rt.uniform(-np.pi, np.pi):.6f} {P}/statue/{m_}.jm {P}/statue/{GT['tex']}.png null"); nt_ += 1
        print('grass tufts', nt_)
    open(f'{OUT}/statues', 'w', newline='\n').write('\n'.join(st + crowd_st) + '\n')
    # decals (ground texture over the riding surface, obstacle and turn decals)
    R = StartRoute(LS.STARTS[KEY], LS.N_GATES, LS.GATE_PITCH)
    dec = surface_decals(p, R) + obstacle_and_turn_decals(p)
    # v25: track-coloured decals over the dirt up to the fence, put FIRST in the file so the track and obstacle decals are drawn
    # over them (v24 put them last and hid the bump textures); 26 / 13 / 6 ft patches so the edge follows the fence line
    DD = getattr(LT, 'DIRT_DECALS', None)
    if DD and getattr(LT, 'FENCE', None):
        DF = np.load(f'{ROOT}/build/{PFX}_dist.npy'); side = DF.shape[0] - 1.0; rg2 = np.random.default_rng(24); dfirst = []; o = DD.get('edge', LT.FENCE['off'])
        bands_ = ((26.0, 10.0, -1e9, o - 14.0), (13.0, 5.0, o - 14.0, o - 7.0), (6.0, 2.5, o - 7.0, o - 3.2))
        if DD.get('inside'):                        # v83 (Saint-Georges v28): DF is 0 on the dirt -> use the depth inside the dirt
            from scipy.ndimage import distance_transform_edt as dte_
            DF = -dte_(DF <= 0.0); bands_ = ((26.0, 10.0, -1e9, -13.0), (13.0, 5.0, -13.0, -6.5), (6.0, 2.5, -6.5, -3.0))
        for size, step_, lo, hi in bands_:
            for zz in np.arange(step_ / 2, side, step_):
                for xx in np.arange(step_ / 2, side, step_):
                    x_, z_ = xx + rg2.uniform(-0.3, 0.3) * step_, zz + rg2.uniform(-0.3, 0.3) * step_
                    dv = DF[min(int(z_), DF.shape[0] - 1), min(int(x_), DF.shape[1] - 1)]
                    if lo < dv <= hi: dfirst.append(decal(x_, z_, rg2.uniform(-np.pi, np.pi), size, 'track'))
        if getattr(LT, 'GRASS_OUTSIDE', {}).get('dirt_to_fence'):   # v86 (Saint-Georges v33): the strip up to the fence looks like the track
            DFs_ = np.load(f'{ROOT}/build/{PFX}_dist.npy'); ns_ = 0
            for size, step_, lo, hi in ((6.0, 2.5, 0.0, LT.FENCE['off'] + 0.3),):
                for zz in np.arange(step_ / 2, side, step_):
                    for xx in np.arange(step_ / 2, side, step_):
                        x_, z_ = xx + rg2.uniform(-0.3, 0.3) * step_, zz + rg2.uniform(-0.3, 0.3) * step_
                        dv = DFs_[min(int(z_), DFs_.shape[0] - 1), min(int(x_), DFs_.shape[1] - 1)]
                        if lo < dv <= hi: dfirst.append(decal(x_, z_, rg2.uniform(-np.pi, np.pi), size, 'track')); ns_ += 1
            print('fence strip dirt decals', ns_)
        LDy_ = getattr(LT, 'LIGHT_DIRT', None)
        if DD.get('yard') and LDy_:                 # v86 (Saint-Georges v31, user): the yard looks like the track too
            ny_ = 0
            for size, step_, inset_ in ((26.0, 10.0, 13.0), (13.0, 5.0, 6.5), (6.0, 2.5, 3.0)):
                for zz in np.arange(LDy_['z'][0] + inset_, LDy_['z'][1] - inset_ + 0.01, step_):
                    for xx in np.arange(LDy_['x'][0] + inset_, LDy_['x'][1] - inset_ + 0.01, step_):
                        e_ = min(xx - LDy_['x'][0], LDy_['x'][1] - xx, zz - LDy_['z'][0], LDy_['z'][1] - zz)
                        if size < 26.0 and e_ > inset_ * 2.0: continue          # small ones only along the edges
                        x_, z_ = xx + LT.STT_ORIGIN[0] + rg2.uniform(-0.3, 0.3) * step_, zz + LT.STT_ORIGIN[1] + rg2.uniform(-0.3, 0.3) * step_
                        dfirst.append(decal(x_, z_, rg2.uniform(-np.pi, np.pi), size, 'track')); ny_ += 1
            print('yard dirt decals', ny_)
        dec = dfirst + dec; print('dirt decals', len(dfirst))
    # v23: grass decals (DVDBVisualsCompound grass.png, chosen by the user; 3rd-party file, local use only) laid like DVDB does:
    # 45 ft patches, random rotation, jittered grid every 26 ft (each spot covered ~3 times), on the grass only (>= 6 ft from dirt)
    GD = getattr(LT, 'GRASS_DECALS', None)
    if GD and getattr(LT, 'GRASS_OUTSIDE', None):
        os.makedirs(f'{OUT}/decal', exist_ok=True)
        for e in ('', '_tnorm'): shutil.copy(f"{ROOT}/assets/grass_dvdb/grass_dvdb{e}.png", f"{OUT}/decal/grass_dvdb{e}.png")
        if getattr(LT, 'GRASS_DRY', None):       # v70 (Saint-Georges): the patches as dry as the ground tile
            q_ = np.asarray(Image.open(f'{OUT}/decal/grass_dvdb.png').convert('RGBA'), float); m_ = q_[:, :, 3] > 200
            q_[:, :, :3] *= (np.array(LT.GRASS_DRY, float) / q_[:, :, :3][m_].mean(0))[None, None, :]
            Image.fromarray(np.clip(q_, 0, 255).astype(np.uint8), 'RGBA').save(f'{OUT}/decal/grass_dvdb.png')
        from scipy.ndimage import distance_transform_edt
        DF = np.load(f'{ROOT}/build/{PFX}_dist.npy'); side = DF.shape[0] - 1.0; rg = np.random.default_rng(23); ng = 0
        dd = DF[::2, ::2]                                                 # 2 ft grid as before
        from skimage.measure import find_contours                       # v27: one row of patches along the fence, at a constant
        ring = max(find_contours(DF, GD.get('ring', GD['clear'])), key=len)                # distance, so the grass edge runs parallel to the fence
        Lr = np.r_[0, np.cumsum(np.hypot(*np.diff(ring, axis=0).T))]
        mg_ = GD['size'] / 2 + GD.get('margin', 0.0)
        def grass_ok_(x_, z_):                          # v83 (Saint-Georges v28): world ft
            lx_, lz_ = x_ - LT.STT_ORIGIN[0], z_ - LT.STT_ORIGIN[1]
            if getattr(LT, 'ROADS', None) and float(B.road_dist(np.array([lx_]), np.array([lz_]))[0]) < 8.0 + mg_: return False
            LD_ = getattr(LT, 'LIGHT_DIRT', None)
            if LD_ and LD_['x'][0] - mg_ < lx_ < LD_['x'][1] + mg_ and LD_['z'][0] - mg_ < lz_ < LD_['z'][1] + mg_: return False
            for b_ in getattr(LT, 'BUILDINGS', []):
                if max(b_.get('half', (0, 0))) > 0 and np.hypot(lx_ - b_['c'][0], lz_ - b_['c'][1]) < max(b_['half']) + mg_: return False
            return True
        for sv in np.arange(0, Lr[-1], 13.0):
            k_ = min(int(np.searchsorted(Lr, sv)), len(ring) - 1); z_, x_ = ring[k_]
            if not grass_ok_(x_, z_): continue
            dec.append(f'[{x_:.6f} {z_:.6f}] {rg.uniform(-np.pi, np.pi):.6f} {GD["size"]:.6f} 1.000000 {P}/decal/grass_dvdb.png'); ng += 1
        for zz in np.arange(GD['step'] / 2, side, GD['step']):
            for xx in np.arange(GD['step'] / 2, side, GD['step']):
                x_, z_ = xx + rg.uniform(-0.4, 0.4) * GD['step'], zz + rg.uniform(-0.4, 0.4) * GD['step']
                i_, j_ = min(int(z_ / 2.0), dd.shape[0] - 1), min(int(x_ / 2.0), dd.shape[1] - 1)
                if dd[i_, j_] < GD['clear'] or not (0 < x_ < side and 0 < z_ < side) or not grass_ok_(x_, z_): continue
                dec.append(f'[{x_:.6f} {z_:.6f}] {rg.uniform(-np.pi, np.pi):.6f} {GD["size"]:.6f} 1.000000 {P}/decal/grass_dvdb.png'); ng += 1
        GN_ = GD.get('near')
        if GN_:                                     # v85 (Saint-Georges v30, user): real grass right up to the fence where the path was
            for d_, sz_, stp_ in GN_['rows']:       # removed (west / south): rows parallel to the fence, small patches near it
                for cr_ in find_contours(DF, d_):
                    Lc_ = np.r_[0, np.cumsum(np.hypot(*np.diff(cr_, axis=0).T))]
                    for sv in np.arange(0, Lc_[-1], stp_):
                        k_ = min(int(np.searchsorted(Lc_, sv)), len(cr_) - 1); z_, x_ = cr_[k_]
                        lx_, lz_ = x_ - LT.STT_ORIGIN[0], z_ - LT.STT_ORIGIN[1]
                        if not any(x0_ < lx_ < x1_ and z0_ < lz_ < z1_ for x0_, x1_, z0_, z1_ in GN_['zones']): continue
                        GRn_ = getattr(LT, 'GRAVEL_RING', None)
                        if GN_.get('not_paths') and GRn_ and GRn_['d'][0] - 1.0 < d_ < GRn_['d'][1] + 3.0 and not any(
                                x0_ < lx_ < x1_ and z0_ < lz_ < z1_ for x0_, x1_, z0_, z1_ in GRn_.get('skip', [])): continue   # dirt path there
                        if not grass_ok_(x_, z_): continue
                        dec.append(f'[{x_:.6f} {z_:.6f}] {rg.uniform(-np.pi, np.pi):.6f} {sz_:.6f} 1.000000 {P}/decal/grass_dvdb.png'); ng += 1
        GA_ = GD.get('auto')
        if GA_:                                     # v86 (Saint-Georges v33, user: no bare ground anywhere, clean joins)
            from scipy.ndimage import distance_transform_edt as dte2_
            gi2_ = sum(1 for l in open(f'{ROOT}/tracks/USLAND2026SX1/tileinfo') if l.strip() == 'addtile')
            grass_ = tiles == gi2_; dg_ = dte2_(grass_) * 2 * S                          # ft to the nearest non-grass cell
            na_ = 0
            for lo_, hi_, size_, step_ in GA_:
                for zz in np.arange(step_ / 2, side, step_):
                    for xx in np.arange(step_ / 2, side, step_):
                        x_, z_ = xx + rg.uniform(-0.35, 0.35) * step_, zz + rg.uniform(-0.35, 0.35) * step_
                        i_, j_ = int(z_ / (2 * S)), int(x_ / (2 * S))
                        if not (0 <= i_ < dg_.shape[0] and 0 <= j_ < dg_.shape[1]): continue
                        if GD.get('auto_max_df') and DF[min(int(z_), DF.shape[0] - 1), min(int(x_), DF.shape[1] - 1)] > GD['auto_max_df']: continue   # only round the ground
                        sl_ = float(np.hypot(*(np.array([h_at(H, x_ + 2, z_) - h_at(H, x_ - 2, z_), h_at(H, x_, z_ + 2) - h_at(H, x_, z_ - 2)]) / 4.0)))
                        if sl_ > GD.get('max_slope', 9.0): continue
                        if grass_[i_, j_] and lo_ <= dg_[i_, j_] < hi_:
                            dec.append(f'[{x_:.6f} {z_:.6f}] {rg.uniform(-np.pi, np.pi):.6f} {size_:.6f} 1.000000 {P}/decal/grass_dvdb.png'); na_ += 1
            print('grass decals (auto from the tile map)', na_)
        print('grass decals', ng)
    RL_ = [r_ for r_ in (getattr(LT, 'ROADS', None) or []) if r_.get('lines')]
    if RL_:                                         # v82 (Saint-Georges v26): white road markings, French departmental style
        from PIL import Image as ImM_
        for nm_, w_ in (('road_dash', 0.06), ('road_edge', 0.05)):
            mk = np.zeros((256, 256, 4), np.uint8); hw = int(256 * w_ / 2); L0 = 0 if nm_ == 'road_edge' else 40
            mk[L0:256 - L0, 128 - hw:128 + hw] = (236, 236, 230, 235); ImM_.fromarray(mk, 'RGBA').save(f'{OUT}/decal/{nm_}.png')
        nmk = 0
        for r_ in RL_:
            Pr = np.array(r_['pts'], float) + LT.STT_ORIGIN
            for p0_, p1_ in zip(Pr[:-1], Pr[1:]):
                dv_ = p1_ - p0_; Lr = np.linalg.norm(dv_); dv_ /= Lr; nv_ = np.array([-dv_[1], dv_[0]]); a_ = ang_of(dv_[0], dv_[1])
                for t_ in np.arange(6.0, Lr - 6.0, 33.0):     # centre: 10 ft dashes every 33 ft
                    q_ = p0_ + dv_ * t_; dec.append(f'[{q_[0]:.6f} {q_[1]:.6f}] {a_:.6f} 10.000000 1.000000 {P}/decal/road_dash.png'); nmk += 1
                for sd_ in (1, -1):
                    for t_ in np.arange(5.0, Lr - 5.0, 9.5):  # edges: continuous (overlapping 10 ft pieces)
                        q_ = p0_ + dv_ * t_ + nv_ * sd_ * (r_['w'] / 2 - 1.2); dec.append(f'[{q_[0]:.6f} {q_[1]:.6f}] {a_:.6f} 10.000000 1.000000 {P}/decal/road_edge.png'); nmk += 1
        print('road markings', nmk)
    if getattr(LT, 'LIGHT_TRACK', None) and getattr(LT, 'LIGHT_DECALS', None):   # v83 (Saint-Georges v28): same colour as the dirt
        kL2_ = np.array(LT.LIGHT_TRACK if np.ndim(LT.LIGHT_TRACK) else (LT.LIGHT_TRACK,) * 3, float); os.makedirs(f'{OUT}/decal', exist_ok=True)
        for nm_ in LT.LIGHT_DECALS:
            src_ = f'{ROOT}/tracks/USLAND2026SX1/decal/{nm_}.png'
            if not os.path.exists(src_): continue
            q_ = np.asarray(Image.open(src_).convert('RGBA')).astype(float); q_[..., :3] *= kL2_
            Image.fromarray(np.clip(q_, 0, 255).astype(np.uint8), 'RGBA').save(f'{OUT}/decal/{nm_}_lt.png')
            for e_ in ('_tnorm', '_tspec'):
                if os.path.exists(f'{ROOT}/tracks/USLAND2026SX1/decal/{nm_}{e_}.png'): shutil.copy(f'{ROOT}/tracks/USLAND2026SX1/decal/{nm_}{e_}.png', f'{OUT}/decal/{nm_}_lt{e_}.png')
            dec = [l_.replace(f'{SH}/decal/{nm_}.png', f'{P}/decal/{nm_}_lt.png') for l_ in dec]
    open(f'{OUT}/decals', 'w', newline='\n').write('\n'.join(dec) + '\n')
    RG_ = getattr(LT, 'ROUGH', None)
    if RG_:                                         # v83 (Saint-Georges v28, user: "un peu de roughness"): subtle grain on our own
        from scipy.ndimage import gaussian_filter as gfr_   # prop textures written by this run + half the specular strength
        rgr_ = np.random.default_rng(83); nr_ = 0
        for f_ in sorted(os.listdir(f'{OUT}/statue')):
            pth_ = f'{OUT}/statue/{f_}'
            if os.path.getmtime(pth_) < T0_RUN or not any(f_.startswith(k_) for k_ in RG_['prefix']): continue
            SH_ = RG_.get('shiny', {}); sh_ = any(f_.startswith(k_) for k_ in SH_.get('prefix', ()))   # v86 (user): the boudins shinier
            gr_, spc_ = (SH_['grain'], SH_['spec']) if sh_ else (RG_['grain'], RG_['spec'])
            if f_.endswith('.png') and not f_.endswith(('_norm.png', '_spec.png')):
                im_ = Image.open(pth_); md_ = im_.mode; q_ = np.asarray(im_.convert('RGBA')).astype(float); h_, w_ = q_.shape[:2]
                nz_ = gfr_(rgr_.normal(0, 1, (h_, w_)), 6) * 9.0 + gfr_(rgr_.normal(0, 1, (h_, w_)), 0.8) * 0.6
                q_[..., :3] *= (1 + gr_ * nz_)[..., None]
                Image.fromarray(np.clip(q_, 0, 255).astype(np.uint8), 'RGBA').convert(md_ if md_ in ('RGB', 'RGBA') else 'RGBA').save(pth_); nr_ += 1
            elif f_.endswith('.jm'):
                L_ = open(pth_).read().split('\n'); m_ = L_[1].split()
                if len(m_) == 5 and float(m_[1]) > 0: m_[1] = f'{float(m_[1]) * spc_:.6f}'; L_[1] = ' '.join(m_); open(pth_, 'w', newline='\n').write('\n'.join(L_)); nr_ += 1
        print('roughness pass', nr_, 'files')
    # v46 (user): the finish flagger = the 'RF' animated photo flagger of the 2024 Boot's House tracks (22 frames waving the
    # checkered flag + green / halfway / last lap), referenced from @2024Bh1Conway (not copied). Still a sprite: MX flaggers are.
    FLAG_FILES_ = lambda: [f"{LT.FLAG_STAND['rf']['size']} {LT.FLAG_STAND['rf'].get('flip', LT.FLAG_STAND.get('flip', 1))}"] + [f"{LT.FLAG_STAND['rf']['src']}/{n_}" for n_ in
                          ('defaultflag.png', 'halfway.png', 'lastlap.png', 'rf.flagger_waving.seq')]
    # flaggers: 30 s board behind the gate row, finish flagger beside the finish line on flat ground away from the lanes
    smp = p.samples(1.0); tr = cKDTree(np.c_[smp['x'], smp['z']])
    fr = np.array([-np.sin(fa), -np.cos(fa)]); nr = np.array([-fr[1], fr[0]]); half = (LS.N_GATES - 1) / 2 * LS.GATE_PITCH
    B30 = getattr(LT, 'BOARD30', None)              # v54 (user): stands in the middle in front of the gates, runs off to the side
    if B30 and B30.get('done') == 'blank':          # v56: empty last picture (he disappears once arrived)
        from PIL import Image as Im_; os.makedirs(f'{OUT}/billboard', exist_ok=True)
        Im_.new('RGBA', (64, 64), (0, 0, 0, 0)).save(f'{OUT}/billboard/blank.png')
    if B30:
        b1 = np.array([gx, gz]) + fr * B30['stand'][0] + nr * B30['stand'][1]
        b2 = np.array([gx, gz]) + fr * B30['hide'][0] + nr * (B30['hide'][1] * (half + B30['hide_out']))
    else:
        b1 = np.array([gx, gz]) - fr * 25 + nr * (half - 15); b2 = np.array([gx, gz]) - fr * 25 - nr * (half - 15)
    cands = [c + n * sg * o_ + f * a_ for sg in (1, -1) for o_ in (24.0, 28.0, 32.0) for a_ in (6.0, -6.0)]
    fl = max(cands, key=lambda q: tr.query(q)[0] - 50 * float(h_at(H, *q) > 0.1))
    if getattr(LT, 'FLAG_STAND', None):            # v40 (user): the finish flagger on his platform, in a steel cage
        fl = B.flag_stand_geom(p)[4]
        st_ = open(f'{OUT}/statues').read().rstrip('\n') + '\n' + f'[{fl[0]:.6f} 0.000000 {fl[1]:.6f}] 0.000000 {P}/statue/flag_cage.jm {P}/statue/flag_cage.png null' + '\n'
        open(f'{OUT}/statues', 'w', newline='\n').write(st_)
    open(f'{OUT}/flaggers', 'w', newline='\n').write('\n'.join([f'[{b1[0]:.6f} 0.000 {b1[1]:.6f}]', f'[{b2[0]:.6f} 0.000 {b2[1]:.6f}]', '8.4 1', str(B30['speed'] if B30 else 9),
        '@30sec_30.png', '@30sec_turn.seq', '@30sec_5.png', '@30sec_run.seq',
        f'{P}/billboard/blank.png' if B30 and B30.get('done') == 'blank' else '@30sec_done.png', '',
        f'[{fl[0]:.6f} 0.000 {fl[1]:.6f}]', *(FLAG_FILES_() if (getattr(LT, 'FLAG_STAND', None) or {}).get('rf') else
        [f"8 {(getattr(LT, 'FLAG_STAND', None) or {}).get('flip', -1)}", '@finish_green.png', '@finish_crossed.png', '@finish_white.png', '@checkerwave.seq']), '', '', '', '[0.00000000 0.000 0.00000000]', '9.6 1', '3 4 5 -1', '@flagger_resting.png', '@flagger_waving.seq', '']))
    # minimap over the whole terrain (the game stretches map.png over it), this track only
    M = 1024; N = H.shape[0]; side = (N - 1) * S; g1 = (np.arange(M) + 0.5) * side / M
    Hc = H[np.ix_((g1 / S).astype(int), (g1 / S).astype(int))]
    shade = LightSource(300, 40).hillshade(Hc, vert_exag=3 / (side / M)); col = cm.terrain(np.clip(Hc / 12.0, 0, 1))[:, :, :3]
    base = np.dstack([shade] * 3) * 0.75 + 0.25
    rgb = np.where((Hc > 0.15)[:, :, None], base * (0.65 + 0.35 * col), base * np.array([0.78, 0.62, 0.45]))
    gxx, gzz = np.meshgrid(g1, g1); d, _ = tr.query(np.c_[gxx.ravel(), gzz.ravel()]); m = (d.reshape(M, M) < 40)   # v24: thicker ribbon (bigger on the in-game map)
    a = ndi.gaussian_filter(m.astype(float), 1.5)
    Image.fromarray((np.clip(np.dstack([rgb, a]), 0, 1) * 255).astype(np.uint8), 'RGBA').save(f'{OUT}/map.png')
    return dict(lap=p.s, gates=len(G), checkpoints=len(cps), first=len(first), normal=len(normal), statues=len(st), decals=len(dec),
                gate_y=round(float(np.mean([g[1] for g in G])), 2), grate_y=round(float(np.mean([float(l.split()[1]) for l in st])), 2),
                flagger=[round(v, 1) for v in fl], flagger_dist=round(float(tr.query(fl)[0]), 1))

if __name__ == '__main__':
    print(main())
