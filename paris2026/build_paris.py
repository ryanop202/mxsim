"""Piste MX Simulator « USLAND: Supercross Paris 2026 » : tracé (layout_paris.py) + arène agrandie (stade_paris).

  py -3.15 -I stade_paris/src/build.py --mx      (arène, une fois : stade_paris/export/ParisLaDefenseArena)
  py -3.15 -I paris2026/build_paris.py           (terrain, tuiles, portes, assemblage -> tracks/USLAND2026SupercrossParis)

Terrain : grille JGSX 0,28975 ft, 4097 x 4097 (1187 ft), comme les pistes SX du dépôt ; le bâtiment est centré dessus.
Physique / textures du sol : celles des pistes USLAND SX (tracks/USLAND2026SX1 : blocs JGSX), copiées dans le dossier.
Pas de tuff blocks : ils sont posés par Ryan (règle du projet). Non testé en jeu.
"""
import os
import sys
import json
import shutil
import re
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "stade_paris", "src"))
from engine import Grid, render_lane_block, render_berm_stamp, turn_mid_angle, berm_ang_scale, LIB   # noqa: E402
from shading import lambert_shadow   # noqa: E402
import layout_paris as LP            # noqa: E402

FOLDER = "USLAND2026SupercrossParis"
DESC = "USLAND: Supercross Paris 2026"
ARENA = os.path.join(ROOT, "stade_paris", "export", "ParisLaDefenseArena")
SX_ASSETS = os.path.join(ROOT, "tracks", "USLAND2026SX1")
OUT = os.path.join(ROOT, "tracks", FOLDER)
AP = os.path.join(HERE, "apercu")
G = Grid(11, 0.28975); N = G.N; S = G.s
TW = LIB['sx_lateral']['top_width']
T_MAIN, T_JUMP, T_WHOOP, T_BERM, T_ROAD = 0, 1, 2, 3, 8      # indices de export_sx.TILES
REPORT = {}


def arena_dims():
    """cotes de l'arène agrandie (mêmes valeurs que le build de stade_paris)."""
    from arena import dims
    if getattr(dims, "PLAN_SCALE", 1) != LP.PLAN_K:
        for name in ("HALF_W", "X_SOUTH", "R_CORNER", "X_CORNER", "Y_CORNER", "X_STAGE", "X_RIBBON_END",
                     "X_OFFICE_N", "NORTH_X0", "FLOOR_HALF_W", "FLOOR_X_SOUTH", "FLOOR_R"):
            setattr(dims, name, getattr(dims, name) * LP.PLAN_K)
        dims.OUTLINE = [(x * LP.PLAN_K, y * LP.PLAN_K) for x, y in dims.OUTLINE]
        dims.OUTLINE_R = [r * LP.PLAN_K for r in dims.OUTLINE_R]
        dims.PLAN_SCALE = LP.PLAN_K
    return dims


def zion_look(OUT):
    """v10 (« mets la texture ZION, la couleur de la texture ZION ») : la terre de ZION 2025 (tile/2.png de son archive) sur les
    tuiles de terre, et les décals de terre de Saint-Thibéry recolorés à sa teinte moyenne (motif et transparence gardés)."""
    zt = os.path.join(ROOT, "paris2026", "refs", "zion25_full", "ZION.2025.SupercrossParis", "tile", "2.png")
    os.makedirs(os.path.join(OUT, "tiles"), exist_ok=True); shutil.copy(zt, os.path.join(OUT, "tiles", "zion_dirt.png"))
    ti = os.path.join(OUT, "tileinfo"); s = open(ti).read()
    s = s.replace("@%s/ext/USLAND2026SX1/tiles/dirt.ppm" % FOLDER, "@%s/tiles/zion_dirt.png" % FOLDER)
    open(ti, "w", newline=chr(10)).write(s)
    zm = np.asarray(Image.open(zt).convert("RGB"), float).reshape(-1, 3).mean(0)
    dd = os.path.join(OUT, "ext", "USLAND2026SX1", "decal")
    for n in ("track", "180", "90", "single", "table", "tripleface", "whoops"):
        f = os.path.join(dd, n + ".png"); a = np.asarray(Image.open(f).convert("RGBA"), float); m = a[..., 3] > 10
        k = zm / a[..., :3][m].mean(0); a[..., :3] = np.clip(a[..., :3] * k, 0, 255)
        Image.fromarray(a.astype(np.uint8), "RGBA").save(f)
    REPORT['terre_zion'] = [round(float(v)) for v in zm]


ZD = os.path.join(ROOT, "paris2026", "refs", "zion25_full", "ZION.2025.SupercrossParis")


def zion_tileinfo(OUT):
    """v13 (« je veux la texture ZION, là c'est la texture Saint-Tib avec la couleur ZION ») : les tuiles de terre (Main, Jumps,
    Whoops, Berm) prennent la texture, les projections et les traces de pneus de ZION 2025 (bloc « dirtappel » de son tileinfo) ;
    la physique reste celle des pistes USLAND."""
    shutil.copytree(os.path.join(ZD, "tile"), os.path.join(OUT, "ztile"), dirs_exist_ok=True)
    zb = open(os.path.join(ZD, "tileinfo")).read().split("addtile")[0].splitlines()
    look = [l.replace("@ZION.2025.SupercrossParis/roost/", "@%s/ztile/" % FOLDER).replace("@ZION.2025.SupercrossParis/tile/", "@%s/ztile/" % FOLDER)
            for l in zb if l.startswith(("texture", "roost", "treadmark"))]
    ti = os.path.join(OUT, "tileinfo"); blocks = open(ti).read().split("addtile"); out = []
    for b in blocks:
        name = next((l for l in b.splitlines() if l.startswith("name ")), "")
        if name[5:].strip() in ("Main", "Jumps Sx", "WhoopsV2", "Berm Exit Sx"):
            keep = [l for l in b.splitlines() if not l.startswith(("texture", "roost", "treadmark"))]
            while keep and not keep[-1].strip():
                keep.pop()
            b = chr(10).join(keep + look) + chr(10)
        out.append(b)
    open(ti, "w", newline=chr(10)).write("addtile".join(out))
    REPORT['tuiles_zion'] = look


def zion_decals(path, start_route, combos):
    """v13 : décals de ZION 2025 posés comme sur sa piste : un grand « overlay » sur tout le tracé, des bandes « Straight » le long
    des couloirs (135 ft, une tous les ~110 ft), les décals d'obstacles (single / Table / triplemiddle / Whoops) et de virages
    (90 / 180), « startgate » devant chaque grille."""
    from engine import turn_mid_angle
    shutil.copytree(os.path.join(ZD, "decal"), os.path.join(OUT, "zdecal"), dirs_exist_ok=True)
    SH = "@%s/zdecal" % FOLDER
    ang_ = lambda fx, fz: float(np.arctan2(-fx, -fz))
    dec = lambda x, z, a, size, tex: "[%.6f %.6f] %.6f %.6f 1.000000 %s/%s.png" % (x, z, a, size, SH, tex)
    out = []
    smp = path.samples(2.0); cx, cz = (smp['x'].min() + smp['x'].max()) / 2, (smp['z'].min() + smp['z'].max()) / 2
    size = max(smp['x'].max() - smp['x'].min(), smp['z'].max() - smp['z'].min()) + 80.0
    out.append(dec(cx, cz, 0.0, size, 'overlay'))
    for g in path.segs:
        if g['kind'] == 'S':
            c, s_ = np.cos(g['t']), np.sin(g['t']); a = ang_(c, s_)
            n_ = max(1, int(round(g['L'] / 110.0)))
            for k in range(n_):
                u = (k + 0.5) * g['L'] / n_; out.append(dec(g['x0'] + u * c, g['z0'] + u * s_, a, 135.4, 'Straight'))
            for prof, u0, name in g['sections']:
                for it in combos[name]['items']:
                    nm, st, en, hh = it[0], it[1], it[2], it[3]; L = en - st; uu = u0 + (st + en) / 2
                    if nm.startswith('whoops'):
                        for k in range(max(1, int(L / 60))):
                            u_ = u0 + st + (k + 0.5) * L / max(1, int(L / 60)); out.append(dec(g['x0'] + u_ * c, g['z0'] + u_ * s_, a, 130.0, 'Whoops'))
                        continue
                    tex = 'triplemiddle' if hh >= 6.6 and L < 52 else ('Table' if L >= 52 else 'single')
                    out.append(dec(g['x0'] + uu * c, g['z0'] + uu * s_, a, 125.0 if tex == 'single' else 130.0, tex))
        elif g['kind'] == 'T' and g.get('berm'):
            m = turn_mid_angle(g); fx, fz = np.cos(m), np.sin(m)
            if abs(g['ang']) > 120:
                out.append(dec(g['cx'] + fx * 9, g['cz'] + fz * 9, ang_(fx, fz), 135.1, '180'))
            else:
                out.append(dec(g['cx'] + fx * 14, g['cz'] + fz * 14, ang_(fx, fz), 110.0, '90'))
    gx, gz = START['gate']; h = np.radians(START['heading']); nn = np.array([-np.sin(h), np.cos(h)])
    for k in range(LP.N_GATES):
        v = (k - (LP.N_GATES - 1) / 2) * LP.GATE_PITCH
        out.append(dec(gx + nn[0] * v, gz + nn[1] * v, ang_(np.cos(h), np.sin(h)), 8.0, 'startgate'))
    return out, 0


def mx_poly(P):
    x, z = LP.arena_to_mx(P[:, 0], P[:, 1])
    return np.c_[x, z]


# ---------------------------------------------------------------- terrain
def render_wide(out, g, prof, u0, w_half_h, w_foot):
    """bloc dont la coupe en travers suit la butte de ZION 2025 : plein sur le dessus, flancs en cosinus du demi-largeur
    à mi-hauteur jusqu'au pied (largeurs mesurées)."""
    L = len(prof) * 0.1; c, s_ = np.cos(g['t']), np.sin(g['t']); half = w_foot / 2 + 2.0
    pts = np.array([(g['x0'] + uu * c - vv * s_, g['z0'] + uu * s_ + vv * c) for uu in (u0, u0 + L) for vv in (-half, half)])
    sl, X, Z = G.window(pts[:, 0].min(), pts[:, 0].max(), pts[:, 1].min(), pts[:, 1].max())
    dx, dz = X - g['x0'], Z - g['z0']; u = dx * c + dz * s_ - u0; v = np.abs(-dx * s_ + dz * c)
    pu = np.interp(u / 0.1, np.arange(len(prof)), prof, left=0, right=0)
    a_, b_ = w_half_h / 2 - (w_foot - w_half_h) / 2, w_foot / 2          # plein jusqu'à a_, 0 au pied b_ (1/2 à mi-largeur)
    lat = np.where(v <= a_, 1.0, np.where(v >= b_, 0.0, 0.5 * (1 + np.cos(np.pi * (v - a_) / (b_ - a_)))))
    out[sl] = np.maximum(out[sl], pu * lat)


def berm_seg(g):
    """partie du virage qui porte le berm (tout le virage, ou à partir de la fraction g['berm_from'])."""
    f = g.get('berm_from', 0.0)
    if not f:
        return g
    a = np.radians(g['ang']) * f
    return dict(g, t0=g['t0'] - a, ang=g['ang'] * (1 - f), s0=g['s0'] + g['L'] * f, L=g['L'] * (1 - f))


def whoops_rails(out, g, prof, u0, it):
    """v14 : muret continu de chaque côté des whoops, comme 25 Paris SX : dessus plat à la hauteur des crêtes entre |v| = 15,5 et
    19 ft, face intérieure de 1 ft qui tombe dans les creux, talus extérieur en cosinus sur 3,5 ft ; rampes de 6 ft aux deux bouts."""
    R = LP.RAIL; a, b = R['top']; Hr = float(np.max(prof[int(it[1] / 0.1):int(it[2] / 0.1)]))
    ua, ub = u0 + it[1], u0 + it[2]; c, s_ = np.cos(g['t']), np.sin(g['t']); half = b + R['outer'] + 1.0
    pts = np.array([(g['x0'] + uu * c - vv * s_, g['z0'] + uu * s_ + vv * c) for uu in (ua, ub) for vv in (-half, half)])
    sl, X, Z = G.window(pts[:, 0].min(), pts[:, 0].max(), pts[:, 1].min(), pts[:, 1].max())
    dx, dz = X - g['x0'], Z - g['z0']; u = dx * c + dz * s_; v = np.abs(-dx * s_ + dz * c)
    ss = lambda t: np.clip(t, 0, 1) ** 2 * (3 - 2 * np.clip(t, 0, 1))
    lat = np.where(v < a, ss((v - (a - R['inner'])) / R['inner']), np.where(v <= b, 1.0, 0.5 * (1 + np.cos(np.pi * np.clip((v - b) / R['outer'], 0, 1)))))
    lon = ss((u - ua) / R['ramp']) * ss((ub - u) / R['ramp'])
    # les whoops pleine largeur jusque sous le muret (comme 25 Paris SX : pas d'encoche à la jonction whoops / muret)
    wu = np.interp((u - u0) / 0.1, np.arange(len(prof)), prof, left=0, right=0) * (u >= ua) * (u <= ub)
    new = np.maximum(out[sl], np.maximum(Hr * lat * lon, wu * (v <= b)))
    # jonction creux / muret arrondie (25 Paris SX : creux qui remontent en rond contre le muret, pas en pointe)
    from scipy.ndimage import gaussian_filter
    wgt = np.exp(-((v - (a - 0.5)) / 1.6) ** 2) * (lon > 0)
    out[sl] = new * (1 - wgt) + gaussian_filter(new, 1.2 / S) * wgt


def render(path, st):
    jumps = np.zeros((N, N)); whoops = np.zeros((N, N)); berms = np.zeros((N, N)); fmx = np.zeros((N, N))
    import layouts_sx as LS
    secs = []
    for g in path.segs:
        if g['kind'] == 'S':
            for prof, u0, name in g['sections']:
                render_lane_block(G, whoops if 'whoops' in name else jumps, g, prof, u0, TW)
                for it in LS.COMBOS[name]['items']:            # v14 : bord des whoops (muret de 25 Paris SX)
                    if it[0].startswith('whoops 25 Paris'):
                        whoops_rails(whoops, g, prof, u0, it)
                if name == LP.L3_SEC:                          # butte ZION 2025 : sa largeur mesurée (68 ft à mi-hauteur, 110 au pied)
                    it = [i for i in LS.COMBOS[name]['items'] if 'butte' in i[0]][0]
                    i0, i1 = int(it[1] / 0.1), int(it[2] / 0.1)
                    render_wide(jumps, g, prof[i0:i1], u0 + it[1], *LP.Z25_BUTTE_W)
                secs.append(dict(lane=g['tag'], name=name, u0=round(u0, 1), s0=round(g['s0'] + u0, 1),
                                 L=round(len(prof) * 0.1, 1), H=round(float(prof.max()), 2), seg_L=round(g['L'], 1),
                                 items=[(i[0], round(i[1], 1), round(i[2], 1)) for i in LS.COMBOS[name]['items']]))
        elif g.get('berm'):
            # berms : 90° tels que mesurés (BERM90_GAIN), 180° un peu plus gros (v9, BERM180_GAIN) ;
            # v9 : 180 L3 -> L2 de rayon 32 ft, berm sur sa 2e moitié seulement (berm_seg), croissant décalé de r - 21,5 ft
            gb = berm_seg(g)
            gain = LP.BERM90_GAIN if abs(abs(gb['ang']) - 90) < 1 else LP.BERM180_GAIN
            gain = LP.BERM_GAIN_TAG.get(g['tag'][:4], gain)                 # v13 : réglage par virage (T_D moins haut)
            tmp = np.zeros((N, N))
            sl = render_berm_stamp(G, tmp, g['berm'], g['cx'], g['cz'], turn_mid_angle(gb),
                                   ang_scale=berm_ang_scale(g['berm'], gb['ang']), r_shift=max(0.0, g['r'] - LP.RB))
            berms[sl] = np.maximum(berms[sl], tmp[sl] * gain)
    # pieds des bosses arrondis (SOFT_FEET de Saint-Georges : pas de cassure de pente au pied)
    from scipy.ndimage import gaussian_filter
    sf = LP.SOFT_FEET
    for A_ in (jumps, whoops):
        t_ = np.clip(A_ / sf['h'], 0, 1); w_ = t_ * t_ * (3 - 2 * t_)
        A_[:] = A_ * w_ + gaussian_filter(A_, sf['sigma'] / S) * (1 - w_)
    REPORT['sections'] = secs
    return jumps, whoops, berms, fmx


def checks(path, st, H, jumps, whoops, berms, fmx, floor_mx):
    from engine import Path   # noqa
    from geo_tools import inside
    out = []
    # 1. boucle fermée
    e = np.hypot(path.x - path.segs[0]['x0'], path.z - path.segs[0]['z0'])
    out.append(("boucle fermée (écart de fin de tour)", e < 0.01, "%.3f ft" % e))
    # 2. chaque obstacle tient dans sa ligne droite, sans chevauchement
    bad = []
    for g in path.segs:
        if g['kind'] != 'S':
            continue
        iv = sorted((u0, u0 + len(p) * 0.1, n) for p, u0, n in g['sections'])
        for a, b, n in iv:
            if a < -0.05 or b > g['L'] + 0.05:
                bad.append("%s hors ligne droite (%.1f..%.1f / %.1f)" % (n, a, b, g['L']))
        for (a1, b1, n1), (a2, b2, n2) in zip(iv, iv[1:]):
            if a2 < b1 - 0.3:
                bad.append("%s chevauche %s (%.1f ft)" % (n1, n2, b1 - a2))
    out.append(("obstacles dans leur ligne droite, sans chevauchement", not bad, "; ".join(bad) or "ok"))
    # 3. tout le relief du tracé est sur le sol de l'arène
    ii, jj = np.nonzero(H[::4, ::4] > 0.05)
    pts = np.c_[jj * 4 * S, ii * 4 * S]
    ok = inside(pts, floor_mx)
    out.append(("relief entièrement sur le sol de l'arène", bool(ok.all()), "%d points hors sol" % int((~ok).sum())))
    # 4. hauteurs
    hj = float(max(jumps.max(), whoops.max())); hb = float(berms.max())
    out.append(("bosses <= 25 ft (gros saut rond ZION 2025 24,2 ft)", hj <= 25.0, "%.2f ft" % hj))
    out.append(("berms <= 10 ft (90° x1,4 comme Saint-Thibéry)", hb <= 10.0, "%.2f ft" % hb))
    # 5. départ : grilles et couloir de départ sur le sol, plat
    from starts import StartRoute
    R = StartRoute(st, LP.N_GATES, LP.GATE_PITCH)
    X, Z, _, _ = R.area_points(2.0, 2.0)
    okf = inside(np.c_[X, Z], floor_mx)
    hs = H[np.clip((Z / S).astype(int), 0, N - 1), np.clip((X / S).astype(int), 0, N - 1)]
    out.append(("couloir de départ sur le sol", bool(okf.all()), "%d points hors sol" % int((~okf).sum())))
    out.append(("ligne de départ plate (grilles)", float(hs[:200].max()) < 0.05, "max %.2f ft" % float(hs[:200].max())))
    return out


# ---------------------------------------------------------------- export
def ppm(path, img):
    with open(path, "wb") as fh:
        fh.write(b"P6\n%d %d\n255\n" % (img.shape[1], img.shape[0])); fh.write(np.repeat(img[:, :, None], 3, 2).tobytes())


def export(H, tiles, gates_txt, floor_mx, inside_mx):
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    hmin, hmax = float(H.min()) - 0.5, float(H.max()) + 0.5
    raw = np.round((H - hmin) / (hmax - hmin) * 65535).astype(np.uint16)
    open(os.path.join(OUT, "terrain.hf"), "w", newline="\n").write("11 %.6f %.6f %.6f\n" % (S, hmin, hmax))
    Image.fromarray(raw).save(os.path.join(OUT, "terrain.png"))
    tiles.astype(np.uint8).tofile(os.path.join(OUT, "tilemap"))
    # sol, textures, ciel et éclairage de Saint-Thibéry à l'identique (stt_look.py)
    import stt_look as SL
    SL.copy_assets(OUT, FOLDER)
    zion_tileinfo(OUT)
    sh = SL.shading(H, S, floor_mx)
    ppm(os.path.join(OUT, "shading.ppm"), sh)
    ppm(os.path.join(OUT, "shadingx2.ppm"), (sh // 2).astype(np.uint8))
    # statues de l'arène : même repère (origine OX, OZ), hauteur compensée si une origine tombe sur une bosse
    import importlib
    mxt = importlib.import_module("arena.mxtrack")
    dx, dz = LP.OX - mxt.OX, LP.OZ - mxt.OZ
    nfix = 0
    RELOC = {}                     # v10 : modèle -> décalage (ft) de son origine vers un sol plat

    def bumpy(x, z, r=4.0):
        i0, i1 = int((z - r) / S), int((z + r) / S) + 1; j0, j1 = int((x - r) / S), int((x + r) / S) + 1
        if i0 < 0 or j0 < 0 or i1 > N or j1 > N:
            return False
        return float(H[i0:i1, j0:j1].max()) > 0.005

    def flat_spot(x, z):
        for rad in np.arange(2.0, 300.0, 2.0):
            for a in np.linspace(0, 2 * np.pi, int(2 * np.pi * rad / 2.0) + 1, endpoint=False):
                xx, zz = x + rad * np.cos(a), z + rad * np.sin(a)
                if 5 < xx < (N - 1) * S - 5 and 5 < zz < (N - 1) * S - 5 and not bumpy(xx, zz):
                    return round(float(xx), 3), round(float(zz), 3)
        raise RuntimeError("pas de sol plat près de (%.0f, %.0f)" % (x, z))

    def fix(line):
        nonlocal nfix
        m = re.match(r"\[([-\d.]+) ([-\d.]+) ([-\d.]+)\] ([-\d.]+) (\S+)(.*)$", line)
        if not m:
            return line
        x, y, z = float(m.group(1)) + dx, float(m.group(2)), float(m.group(3)) + dz
        rest = (m.group(4) + " " + m.group(5) + m.group(6)).replace("@ParisLaDefenseArena/", "@%s/" % FOLDER)
        # v10 (le jeu penche une statue selon la pente du sol sous son origine : rampes d'éclairage et charpente posées sur des
        # bosses partaient en travers) : origine déplacée sur le sol plat le plus proche, modèle décalé d'autant (même place)
        if bumpy(x, z):
            assert abs(float(m.group(4))) < 1e-6, line
            mdl = m.group(5).split("/")[-1]
            if mdl not in RELOC:
                nx_, nz_ = flat_spot(x, z); RELOC[mdl] = (nx_ - x, nz_ - z)
            ox_, oz_ = RELOC[mdl]; nfix += 1
            return "[%.4f %.4f %.4f] %s" % (x + ox_, y, z + oz_, rest)
        h = float(H[int(round(z / S)), int(round(x / S))])
        return "[%.4f %.4f %.4f] %s" % (x, y - h, z, rest)
    for name in ("statues",):
        L = open(os.path.join(ARENA, name)).read().splitlines()
        open(os.path.join(OUT, name), "w", newline="\n").write("\n".join(fix(l) for l in L if l.strip()) + "\n")
    os.makedirs(os.path.join(OUT, "variants"))
    for f in os.listdir(os.path.join(ARENA, "variants")):
        src = open(os.path.join(ARENA, "variants", f)).read()
        if f.startswith("statues"):
            src = "\n".join(fix(l) for l in src.splitlines() if l.strip()) + "\n"
        open(os.path.join(OUT, "variants", f), "w", newline="\n").write(src)
    shutil.copytree(os.path.join(ARENA, "statue"), os.path.join(OUT, "statue"))
    import gzip
    for mdl, (ox_, oz_) in RELOC.items():                  # v10 : sommets décalés à l'inverse de l'origine
        fn = os.path.join(OUT, "statue", mdl + ".gz") if os.path.exists(os.path.join(OUT, "statue", mdl + ".gz")) else os.path.join(OUT, "statue", mdl)
        gz = fn.endswith(".gz"); L = (gzip.open(fn, "rt") if gz else open(fn)).read().split(chr(10))
        nv = int(L[2].split()[0])
        for k in range(3, 3 + nv):
            v = L[k].split(); v[0] = "%.5f" % (float(v[0]) - ox_); v[2] = "%.5f" % (float(v[2]) - oz_); L[k] = " ".join(v)
        (gzip.open(fn, "wt", newline=chr(10)) if gz else open(fn, "w", newline=chr(10))).write(chr(10).join(L))
        print("origine déplacée sur sol plat : %s (%+.1f, %+.1f) ft" % (mdl, ox_, oz_))
    # tremplins FMX : le modèle acier de Ryan (ramp_50, collision .shp), comme à Saint-Thibéry / Saint-Georges ; le modèle a son
    # pied à l'origine et va vers son -z local, lèvre à model_len : la lèvre est posée au point du visuel, face à la grande table
    m_ = LP.FMX_MODEL['model']; src_ = os.path.join(ROOT, "assets", "fmx_ramp_user")
    for e in (".jm", ".png", "_norm.png", ".shp"):
        shutil.copy(os.path.join(src_, m_ + e), os.path.join(OUT, "statue", m_ + e))
    sys.path.insert(0, os.path.join(ROOT, "scripts")); import props_place as PP
    ramps = []
    for r in LP.fmx_ramps(PATH):
        (x, z), h = r['lip'], r['heading']; d = np.array([np.cos(h), np.sin(h)])
        fx, fz = x - d[0] * LP.FMX_MODEL['model_len'], z - d[1] * LP.FMX_MODEL['model_len']
        ramps.append("[%.6f 0.000000 %.6f] %.6f @%s/statue/%s.jm @%s/statue/%s.png @%s/statue/%s.shp"
                     % (fx, fz, PP.statue_ang(-d[0], -d[1]), FOLDER, m_, FOLDER, m_, FOLDER, m_))
    # étape 3 (v3) : habillage « comme en vrai » (habillage.py, d'après les photos du Supercross de Paris) ; plus rien de ZION
    import habillage as HB
    import layouts_sx as LS_
    from starts import finish_s
    ob, gate_model, REPORT['objets'] = HB.build(OUT, FOLDER, H, S, PATH, START, LS_.COMBOS, finish_s(PATH, START, LS_.COMBOS))
    with open(os.path.join(OUT, "statues"), "a", newline="\n") as f_:
        f_.write("\n".join(ramps + ob) + "\n")
    # (h) le long tuff block de la ligne de départ : enterré jusqu'à ~20 s après la chute de la grille (comme les boudins de départ
    #     de Saint-Thibéry, mais à l'envers). Indices = rang de la statue dans le fichier statues.
    allst = [l for l in open(os.path.join(OUT, "statues")).read().split("\n") if l.strip()]
    late = set(HB.LATE); rows = []
    for i_, l_ in enumerate(allst):
        if l_ in late:
            v_ = l_.split(']')[0][1:].split(); rows.append("[%d, %.3f, %.3f, %.6f]" % (i_, float(v_[0]), float(v_[2]), float(l_.split(']')[1].split()[0])))
    js = ['/*', 'USLAND: Supercross Paris 2026 - long tuff block le long de la ligne de depart reprise par le tour.',
          'Enterre au depart (il generait le depart), il sort du sol LATE_AFTER s apres la chute de la grille.',
          'Sans chute de grille (entrainement libre) il est la (v9). Texte ASCII expres.', '*/', '',
          'var g_lt = [' + ', '.join(rows) + '];', 'var LATE_AFTER = 20.0;', 'var g_lt_shown = -1;', 'var g_lt_t = -1.0;', '',
          'function ltSet(show) {', '    var i, s;', '    for (i = 0; i < g_lt.length; i++) {', '        s = g_lt[i];',
          '        mx.move_statue(s[0], s[1], show ? 0.0 : -200.0, s[2], s[3]);', '    }', '    g_lt_shown = show;', '}', '',
          'function lateTuff(seconds) {', '    var d = mx.get_gate_drop_time();', '    var show = (d < 0 || mx.seconds >= d + LATE_AFTER);',
          '    if (show != g_lt_shown || mx.seconds < g_lt_t || mx.seconds - g_lt_t > 1.0) {', '        ltSet(show);', '        g_lt_t = mx.seconds;', '    }',
          '    if (lateTuffPrev)', '        lateTuffPrev(seconds);', '}', '', 'var lateTuffPrev = mx.frame_handler;', 'mx.frame_handler = lateTuff;', '']
    open(os.path.join(OUT, "nofrills.js"), "w", newline="\n", encoding="ascii").write("\n".join(js))
    REPORT['long_tuff_apres_depart'] = len(rows)
    # v10 : le vrai quartier autour du bâtiment (photo IGN, agrandie comme l'arène) - ajouté en fin de fichier (indices ci-dessus inchangés)
    import ign_ville as IV
    poly_ = mx_poly(np.asarray(arena_dims().outline(offset=1.0)["p"], float))
    REPORT['quartier_ign_dalles'] = IV.add(OUT, FOLDER, H, S, poly_, LP.OX, LP.OZ, LP.PLAN_K, LP.FT)
    shutil.copytree(os.path.join(ARENA, "tex"), os.path.join(OUT, "tex"))
    gl = gates_txt.split("\n"); i_ = gl.index("startinggate:"); j_ = gl.index("checkpoints:")
    for k_ in range(i_ + 1, j_):                         # le cadre rouge de Saint-Georges sur chaque grille
        if gl[k_].strip():
            gl[k_] = gl[k_].rstrip() + " " + gate_model
    gates_txt = "\n".join(gl)
    open(os.path.join(OUT, "timing_gates"), "w", newline="\n").write(gates_txt)
    open(os.path.join(OUT, "desc"), "w", newline="\n").write(DESC + "\n")
    # décals de Saint-Thibéry (terre sur tout le sol, surface du tour, obstacles, virages)
    import layouts_sx as LS
    from starts import StartRoute
    dec, n_dirt = zion_decals(PATH, StartRoute(START, LP.N_GATES, LP.GATE_PITCH), LS.COMBOS)   # v13 : décals de ZION (plus ceux de STT)
    open(os.path.join(OUT, "decals"), "w", newline="\n").write("\n".join(dec) + "\n")
    # étape 4 : public dans les tribunes (silhouettes de Saint-Thibéry), public.py
    import public as PB
    bb = PB.build(OUT, FOLDER, LP.arena_to_mx, LP.FT)
    open(os.path.join(OUT, "billboards"), "w", newline="\n").write("\n".join(bb) + "\n")
    REPORT['public'] = len(bb)
    open(os.path.join(OUT, "flaggers"), "w").close()
    REPORT['export'] = dict(hmin=hmin, hmax=hmax, statues_relevees=nfix, decals=len(dec), decals_terre=n_dirt)


def top_view(H, path, st, floor_mx, gates):
    """vue de dessus : relief ombré + sol de l'arène + ligne de course + départ + portes."""
    from PIL import ImageDraw
    sub = 4
    h = H[::sub, ::sub]
    lam, _ = lambert_shadow(h, S * sub, [-0.5, 0.7, 0.5], shadow=False)
    img = np.clip(70 + 185 * lam, 0, 255)
    rgb = np.stack([img * 0.93, img * 0.80, img * 0.62], -1)
    rgb[h > 0.05] *= np.array([1.0, 0.92, 0.78])
    im = Image.fromarray(rgb.astype(np.uint8)); d = ImageDraw.Draw(im)
    k = 1 / (S * sub)
    d.line([tuple(p * k) for p in np.vstack([floor_mx, floor_mx[:1]])], fill=(40, 40, 40), width=2)
    smp = path.samples(2.0)
    d.line(list(zip(smp['x'] * k, smp['z'] * k)), fill=(210, 20, 20), width=2)
    from starts import StartRoute
    R = StartRoute(st, LP.N_GATES, LP.GATE_PITCH); rs = R.samples(2.0)
    d.line(list(zip(rs['x'] * k, rs['z'] * k)), fill=(20, 60, 220), width=2)
    for (x, z) in gates:
        d.ellipse([x * k - 2, z * k - 2, x * k + 2, z * k + 2], fill=(0, 0, 0))
    xs, zs = floor_mx[:, 0] * k, floor_mx[:, 1] * k
    box = (int(xs.min()) - 30, int(zs.min()) - 30, int(xs.max()) + 30, int(zs.max()) + 30)
    im = im.crop(box)
    im = im.rotate(180)                     # même orientation que le visuel officiel (départ à gauche)
    os.makedirs(AP, exist_ok=True)
    im.resize((im.size[0] * 2, im.size[1] * 2), Image.LANCZOS).save(os.path.join(AP, "vue_dessus.png"))


def main():
    dims = arena_dims()
    floor_mx = mx_poly(dims.floor_outline(1.0))
    global PATH, START
    path = LP.paris(); st = LP.start(path); PATH, START = path, st
    jumps, whoops, berms, fmx = render(path, st)
    H = np.maximum.reduce([jumps, whoops, berms, fmx])
    from geo_tools import inside
    jj, ii = np.meshgrid(np.arange(N) * S, np.arange(N) * S)
    pts = np.c_[jj.ravel(), ii.ravel()]
    floor_full = inside(pts, floor_mx).reshape(N, N)
    inside_full = inside(pts, mx_poly(dims.outline(0.0, 2.0)["p"])).reshape(N, N)
    TN = 2 ** 11
    t = lambda a: a[:-1:2, :-1:2][:TN, :TN]
    tiles = np.full((TN, TN), T_ROAD, np.uint8)
    tiles[t(floor_full)] = T_MAIN
    tiles[t(jumps) > 0.05] = T_JUMP; tiles[t(fmx) > 0.05] = T_JUMP
    tiles[t(whoops) > 0.05] = T_WHOOP; tiles[t(berms) > 0.05] = T_BERM
    # v10 (« c'est du sable, le virage après l'arrivée ; mets une partie sable après ») : tuiles sable de Saint-Thibéry / SX1
    # (4 Sand Straight, 5 Sand Bump Straight, 6 Sand Exit) sur les 2 virages après l'arrivée et les 70 premiers ft de LD
    from scipy.spatial import cKDTree
    smp_ = path.samples(1.0); tags_ = [path.segs[int(k)]['tag'] for k in smp_['seg']]
    s_ld = next(g['s0'] for g in path.segs if g['tag'].startswith('LD'))
    sel_ = [i for i, tg in enumerate(tags_) if tg.startswith('T_L5') or (tg.startswith('LD') and smp_['s'][i] < s_ld + 70.0)]
    TJ, TI = np.meshgrid(np.arange(TN) * 2 * S, np.arange(TN) * 2 * S)
    dq, _ = cKDTree(np.c_[smp_['x'][sel_], smp_['z'][sel_]]).query(np.c_[TJ.ravel(), TI.ravel()], distance_upper_bound=20.0)
    sand = (dq < 17.0).reshape(TN, TN)
    tiles[sand & (tiles == T_BERM)] = 6; tiles[sand & (tiles == T_JUMP)] = 5; tiles[sand & (tiles == T_MAIN)] = 4
    REPORT['sable_tuiles'] = int(sand.sum())
    # portes de chrono (timing.py des pistes SX)
    import layouts_sx as LS
    pass                                   # sections déjà dans LS.COMBOS (layout_paris.paris)
    from timing import gates
    gt = gates(path, st)
    gates_txt = gt[0]
    res = checks(path, st, H, jumps, whoops, berms, fmx, floor_mx)
    export(H, tiles, gates_txt, floor_full, inside_full)
    top_view(H, path, st, floor_mx, [])
    REPORT.update(lap_ft=round(path.s, 1), start=dict(gate=st['gate'], merge=st['merge'], length=round(st['length'], 1)),
                  checks=[dict(name=n, ok=bool(o), detail=d) for n, o, d in res],
                  gates=dict(n_checkpoints=len(gt[1]), first=gt[2], normal=gt[3]))
    os.makedirs(AP, exist_ok=True)
    json.dump(REPORT, open(os.path.join(AP, "build_report.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=float)
    n_ok = sum(1 for _, o, _ in res if o)
    for n, o, d in res:
        print("  [%s] %s : %s" % ("OK" if o else "XX", n, d))
    print("contrôles : %d / %d ; tour %.0f ft ; hauteur max %.2f ft ; statues relevées : %d"
          % (n_ok, len(res), path.s, H.max(), REPORT['export']['statues_relevees']))


if __name__ == "__main__":
    main()
