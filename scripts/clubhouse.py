"""Small club house (Saint-Georges v23, user's circled building on the aerial photo): white rendered walls, a door and
windows, a flat roof slab with overhangs (v26). v28 (user): a second storey, smaller than the ground floor and SET BACK from
the main facade (local +z, UP['front']) so it reads as a two-storey building: mostly glass (a glazing band all round), its own
flat roof with a small overhang; the front part of the ground-floor roof becomes a terrace with a steel railing. The ground
floor (footprint, position, frame, look) is unchanged. props_usland.Mesh (1 ft units, y up, baked shades), origin = middle of
the floor, long axis = local x.
Run: python scripts/clubhouse.py [--no-preview] -> assets/props/clubhouse.jm / .png (+ ../apercus_sgm/clubhouse_3d.png)"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
from props_usland import Mesh, palette, OUTD, glass

CH = dict(L=64.0, W=34.0, wall=11.0, ridge=12.0, over=1.5)   # v26 (user): the buvette, flat roof, turned (user's rectangle ~64 x 34 ft); v24 60 x 54 gable
# v28 (user): upper storey. x0..x1 / z0..z1 = its walls (ground floor walls: x +-32, z +-17); front = the side of the terrace
# (+1 = local +z: set back 11 ft from that facade, 3 ft from the back one, 11 ft from each end); h = wall height above the
# ground-floor roof (y = CH['ridge']), roof = slab thickness, over = roof overhang, rail = terrace railing height
UP = dict(x0=-21.0, x1=21.0, back=3.0, depth=20.0, front=1, h=9.0, roof=0.9, over=1.2, rail=3.4)
WALL, ROOF, FRAME, GLASS, DOOR = (226, 224, 216), (52, 104, 62), (70, 72, 76), (60, 78, 92), (96, 70, 48)
UPL, UPE = (0, 640, 1023, 849), (620, 320, 1019, 499)          # v28 atlas: upper long wall (42 x 9 ft), upper end wall (20 x 9 ft)

def up_z():
    """z range of the upper storey walls."""
    hz = CH['W'] / 2
    return (hz - UP['back'] - UP['depth'], hz - UP['back']) if UP['front'] < 0 else (-hz + UP['back'], -hz + UP['back'] + UP['depth'])

def glazing_band(d, rect, w_ft, h_ft, pane_ft=3.5, lo=1.4, hi=8.0):
    """v28: upper storey wall = a band of tall windows (frame + glass with a sky reflection), thin flashing at the bottom."""
    x0, y0, x1, y1 = rect; sx = (x1 - x0 + 1) / w_ft; sy = (y1 - y0 + 1) / h_ft
    yb = lambda h: y1 - h * sy
    d.rectangle([x0, yb(0.35), x1, y1], fill=(150, 148, 142))                       # flashing on the roof
    d.rectangle([x0, yb(hi), x1, yb(lo)], fill=FRAME)
    n = max(1, int(round(w_ft / pane_ft))); pw = (x1 - x0 + 1) / n; m = max(3, int(0.17 * sx))
    for k in range(n):
        a, b = x0 + k * pw + m, x0 + (k + 1) * pw - m
        glass(d, (int(a), int(yb(hi) + m), int(b), int(yb(lo + 1.6) - m // 2)), (112, 136, 156), (60, 78, 92))   # tall pane
        glass(d, (int(a), int(yb(lo + 1.6) + m // 2), int(b), int(yb(lo) - m)), (70, 88, 102), (52, 66, 78), streak=False)   # low pane

def texture():
    img = Image.new('RGB', (1024, 1024), WALL); d = ImageDraw.Draw(img)
    # long wall atlas (0..1023 x 0..299): door + 3 windows, plinth
    d.rectangle([0, 270, 1023, 299], fill=(150, 148, 142))
    for x0 in (120, 380, 640):
        d.rectangle([x0, 70, x0 + 150, 190], fill=FRAME); d.rectangle([x0 + 8, 78, x0 + 142, 182], fill=GLASS)
        d.line([x0 + 75, 78, x0 + 75, 182], fill=FRAME, width=5)
    d.rectangle([860, 60, 960, 270], fill=DOOR); d.rectangle([940, 160, 948, 176], fill=(200, 190, 120))
    # gable end atlas (0..599 x 320..619): one window
    d.rectangle([250, 400, 350, 480], fill=FRAME); d.rectangle([256, 406, 344, 474], fill=GLASS)
    # v28: upper storey walls, mostly glass
    glazing_band(d, UPL, UP['x1'] - UP['x0'], UP['h']); glazing_band(d, UPE, UP['depth'], UP['h'])
    pal = palette(img, ['roof', 'wall', 'frame', 'steel'], [ROOF, WALL, FRAME, (150, 152, 156)])
    return img, pal

def model(pal):
    m = Mesh(1024, 1024); L, W, h, r, o = CH['L'], CH['W'], CH['wall'], CH['ridge'], CH['over']
    hx, hz = L / 2, W / 2
    m.box(-hx, hx, 0.0, h, -hz, hz, {'+z': ('r', (0, 0, 1023, 299)), '-z': ('r', (0, 0, 1023, 299)),
                                      '+x': ('r', (0, 320, 599, 619)), '-x': ('r', (0, 320, 599, 619)), '+y': pal['wall']})
    # v26 (user): flat roof - a slab with a small overhang (green top, dark underside / edges)
    uvr = m.uv_px(*pal['roof'][1]); uvf = m.uv_px(*pal['frame'][1])
    m.box(-hx - o, hx + o, h, r, -hz - o, hz + o, {'+y': pal['roof'], '-y': pal['frame'], '+x': pal['frame'], '-x': pal['frame'], '+z': pal['frame'], '-z': pal['frame']})
    upper(m, pal)
    return m

def upper(m, pal):
    """v28 (user): the second storey (set back, glazed, own flat roof) + the terrace railing round the front of the roof."""
    r = CH['ridge']; x0, x1 = UP['x0'], UP['x1']; z0, z1 = up_z(); yt = r + UP['h']; o = UP['over']
    m.box(x0, x1, r, yt, z0, z1, {'+z': ('r', UPL), '-z': ('r', UPL), '+x': ('r', UPE), '-x': ('r', UPE)})
    m.box(x0 - o, x1 + o, yt, yt + UP['roof'], z0 - o, z1 + o, {'+y': pal['roof'], '-y': pal['frame'], '+x': pal['frame'], '-x': pal['frame'], '+z': pal['frame'], '-z': pal['frame']})
    # railing along the exposed roof edges (front, both ends): posts + top rail + mid rail, 0.6 ft in from the roof edge
    hx, hz = CH['L'] / 2 + CH['over'] - 0.6, CH['W'] / 2 + CH['over'] - 0.6; f = UP['front']; zf = f * hz
    zb = -zf                                                                    # the ends are open (upper storey set back 11 ft): railing to the back corner
    runs = [((-hx, zf), (hx, zf)), ((-hx, zf), (-hx, zb)), ((hx, zf), (hx, zb))]
    for (ax, az), (bx, bz) in runs:
        Lr = np.hypot(bx - ax, bz - az); n = max(1, int(np.ceil(Lr / 6.0)))
        for k in range(n + 1):
            px, pz = ax + (bx - ax) * k / n, az + (bz - az) * k / n
            m.tube((px, r, pz), (px, r + UP['rail'], pz), 0.07, pal['steel'])
        for y in (UP['rail'], UP['rail'] * 0.5):
            m.tube((ax, r + y, az), (bx, r + y, bz), 0.06 if y < UP['rail'] else 0.08, pal['steel'])

# ------------------------------------------------------------------ preview (software z-buffer, NOT a game render)
def preview(out_path):
    from preview_stt_scene import Cam, raster, load_jm
    from rider_gate import scale_person
    V, I = load_jm(f'{OUTD}/clubhouse.jm'); tex = np.asarray(Image.open(f'{OUTD}/clubhouse.png').convert('RGBA'), np.float32) / 255
    objs = [(V, I, tex), scale_person((4.0, 0, CH['W'] / 2 + 6.0)), scale_person((-6.0, CH['ridge'], 13.0))]
    Lg = np.array([-0.45, 0.8, 0.4]); Lg /= np.linalg.norm(Lg)
    def shot(eye, tgt, W=900, H=640, fov=55):
        cam = Cam(eye, tgt, W, H, fov); img = np.zeros((H, W, 3), np.float32)
        sky = np.linspace(0, 1, H)[:, None, None]; img[:] = np.array([0.55, 0.70, 0.90]) * (1 - sky) + np.array([0.82, 0.86, 0.90]) * sky
        zb = np.full((H, W), np.inf, np.float32)
        gs = np.arange(-120, 121, 8.0); GX, GZ = np.meshgrid(gs, gs); P = np.stack([GX, np.zeros_like(GX), GZ], -1).reshape(-1, 3)
        n = len(gs); ii, jj = np.meshgrid(np.arange(n - 1), np.arange(n - 1), indexing='ij'); a = (ii * n + jj).ravel()
        Ig = np.concatenate([np.stack([a, a + 1, a + n], 1), np.stack([a + 1, a + n + 1, a + n], 1)])
        rg = np.random.default_rng(0); C = np.array([0.40, 0.50, 0.30]) * (0.92 + 0.12 * rg.random((len(P), 1)))
        raster(img, zb, cam, P, Ig, lambda ti, B: (C[Ig[ti]] * B[:, :, None]).sum(1))
        for V_, I_, t_ in objs:
            th, tw = t_.shape[:2]
            def uvpx(ti, B, V_=V_, I_=I_, tw=tw, th=th):
                uv = (V_[I_[ti], 6:8][None] * B[:, :, None]).sum(1)
                return np.clip((1 - uv[:, 1]) * th, 0, th - 1).astype(int), np.clip(uv[:, 0] * tw, 0, tw - 1).astype(int)
            def col(ti, B, V_=V_, I_=I_, t_=t_):
                py, px = uvpx(ti, B); nn = (V_[I_[ti], 3:6][None] * B[:, :, None]).sum(1)
                return t_[py, px, :3] * (0.62 + 0.45 * np.clip(nn @ Lg, 0, 1))[:, None]
            raster(img, zb, cam, V_[:, :3], I_, col)
        return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    f = UP['front']
    views = [shot((48.0, 16.0, f * 70.0), (0.0, 9.0, 0.0)),                    # front 3/4 (terrace side)
             shot((-52.0, 6.0, f * 78.0), (-2.0, 11.0, 0.0), fov=45),          # front, low, from the left
             shot((-62.0, 13.0, -f * 62.0), (0.0, 10.0, 0.0), fov=52),         # back 3/4
             shot((26.0, 52.0, f * 58.0), (0.0, 8.0, 0.0), fov=55)]            # high: the set-back upper storey and the terrace
    W_, H_ = views[0].size; sheet = Image.new('RGB', (W_ * 2, H_ * 2), (255, 255, 255))
    for k, v in enumerate(views): sheet.paste(v, ((k % 2) * W_, (k // 2) * H_))
    os.makedirs(os.path.dirname(out_path), exist_ok=True); sheet.save(out_path); print('preview', out_path)

if __name__ == '__main__':
    img, pal = texture(); os.makedirs(OUTD, exist_ok=True); m = model(pal)
    nv, nt = m.write(f'{OUTD}/clubhouse.jm', (0, 0, 0, 0, 0)); img.save(f'{OUTD}/clubhouse.png'); print('clubhouse', nv, nt)
    P = np.array([v[:3] for v in m.V]); print('bbox', P.min(0).round(2), '..', P.max(0).round(2), 'ft')
    if '--no-preview' not in sys.argv: preview(os.path.join(os.path.dirname(ROOT), 'apercus_sgm', 'clubhouse_3d.png'))
