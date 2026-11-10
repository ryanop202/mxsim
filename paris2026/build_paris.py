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


def render(path, st):
    jumps = np.zeros((N, N)); whoops = np.zeros((N, N)); berms = np.zeros((N, N)); fmx = np.zeros((N, N))
    import layouts_sx as LS
    secs = []
    for g in path.segs:
        if g['kind'] == 'S':
            for prof, u0, name in g['sections']:
                render_lane_block(G, whoops if 'whoops' in name else jumps, g, prof, u0, TW)
                if name == LP.L3_SEC:                          # butte ZION 2025 : sa largeur mesurée (68 ft à mi-hauteur, 110 au pied)
                    it = [i for i in LS.COMBOS[name]['items'] if 'butte' in i[0]][0]
                    i0, i1 = int(it[1] / 0.1), int(it[2] / 0.1)
                    render_wide(jumps, g, prof[i0:i1], u0 + it[1], *LP.Z25_BUTTE_W)
                secs.append(dict(lane=g['tag'], name=name, u0=round(u0, 1), s0=round(g['s0'] + u0, 1),
                                 L=round(len(prof) * 0.1, 1), H=round(float(prof.max()), 2), seg_L=round(g['L'], 1),
                                 items=[(i[0], round(i[1], 1), round(i[2], 1)) for i in LS.COMBOS[name]['items']]))
        elif g.get('berm'):
            # berms : 90° plus hauts (BERM90_GAIN 1,4 de Saint-Thibéry / Saint-Georges), 180° tels que mesurés
            gain = LP.BERM90_GAIN if abs(abs(g['ang']) - 90) < 1 else 1.0
            tmp = np.zeros((N, N))
            sl = render_berm_stamp(G, tmp, g['berm'], g['cx'], g['cz'], turn_mid_angle(g),
                                   ang_scale=berm_ang_scale(g['berm'], g['ang']))
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
    sh = SL.shading(H, S, floor_mx)
    ppm(os.path.join(OUT, "shading.ppm"), sh)
    ppm(os.path.join(OUT, "shadingx2.ppm"), (sh // 2).astype(np.uint8))
    # statues de l'arène : même repère (origine OX, OZ), hauteur compensée si une origine tombe sur une bosse
    import importlib
    mxt = importlib.import_module("arena.mxtrack")
    dx, dz = LP.OX - mxt.OX, LP.OZ - mxt.OZ
    nfix = 0

    def fix(line):
        nonlocal nfix
        m = re.match(r"\[([-\d.]+) ([-\d.]+) ([-\d.]+)\] (.*)$", line)
        if not m:
            return line
        x, y, z = float(m.group(1)) + dx, float(m.group(2)), float(m.group(3)) + dz
        h = float(H[int(round(z / S)), int(round(x / S))])
        if h > 0.01:
            nfix += 1
        rest = m.group(4).replace("@ParisLaDefenseArena/", "@%s/" % FOLDER)
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
    dec, n_dirt = SL.decals(PATH, StartRoute(START, LP.N_GATES, LP.GATE_PITCH), floor_mx, S, FOLDER, LS.COMBOS)
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
