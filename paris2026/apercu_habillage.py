"""Aperçu de l'habillage de Paris AVANT mise en jeu (ce n'est pas un rendu du jeu) :
  1. vue de dessus avec l'emprise de chaque objet, une couleur par type  -> apercu/vue_dessus_habillage.png
  2. les objets posés dans l'aperçu 3D de l'arène (stade_paris/build/obj/_habillage.obj + textures + vues)

  py -3.12 -I paris2026/build_paris.py && py -3.12 -I paris2026/preview_track.py
  py -3.12 -I paris2026/apercu_habillage.py && py -3.12 -I stade_paris/src/preview_web.py
"""
import os
import re
import sys
import json
import shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "scripts")); sys.path.insert(0, os.path.join(ROOT, "stade_paris", "src"))
import layout_paris as LP   # noqa: E402

FOLDER = "USLAND2026SupercrossParis"
T = os.path.join(ROOT, "tracks", FOLDER)
SB = os.path.join(ROOT, "stade_paris", "build")
FT = LP.FT


def read_jm(path):
    L = open(path).read().splitlines(); nv, nt = map(int, L[2].split())
    V = np.array([[float(t) for t in l.split()[:8]] for l in L[3:3 + nv]]); I = np.array([int(l) for l in L[3 + nv:3 + nv + 3 * nt]]).reshape(-1, 3)
    return V, I


def statues():
    out = []
    for l in open(os.path.join(T, "statues")):
        m = re.match(r'\[([-\d.]+) ([-\d.]+) ([-\d.]+)\] ([-\d.]+) @%s/(\S+) @%s/(\S+) (\S+)' % (FOLDER, FOLDER), l)
        if m and (m.group(5).startswith('statue/paris/') or 'ramp_50' in m.group(5)):
            out.append((float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4)), m.group(5), m.group(6)))
    return out


def terrain():
    n, s, hmin, hmax = open(os.path.join(T, "terrain.hf")).read().split(); s, hmin, hmax = float(s), float(hmin), float(hmax)
    H = np.asarray(Image.open(os.path.join(T, "terrain.png")), np.float64) / 65535 * (hmax - hmin) + hmin
    return np.maximum(H, 0.0), s


def world(V, x, y, z, a, g):
    """repère du modèle -> monde MX : +z local vers (sin a, cos a), +x local vers (cos a, -sin a) ; posé sur le sol sous l'origine."""
    c, s = np.cos(a), np.sin(a); P = np.empty((len(V), 3)); N = np.empty((len(V), 3))
    P[:, 0] = x + V[:, 0] * c + V[:, 2] * s; P[:, 2] = z - V[:, 0] * s + V[:, 2] * c; P[:, 1] = g + y + V[:, 1]
    N[:, 0] = V[:, 3] * c + V[:, 5] * s; N[:, 2] = -V[:, 3] * s + V[:, 5] * c; N[:, 1] = V[:, 4]
    return P, N


COL = [('tuff_arc_honda', (220, 30, 36), 'tuffs Honda'), ('tuff_arc_yamaha', (30, 70, 200), 'tuffs Yamaha'), ('tuff_arc_seong', (0, 190, 200), 'tuffs Seong'),
       ('tuff_arc_amv', (120, 220, 120), 'tuffs AMV'), ('tuff_arc_monster', (20, 20, 20), 'tuffs Monster'), ('tuff_arc_motul', (255, 120, 120), 'tuffs Motul'),
       ('boudin3_r', (160, 0, 0), 'boudins « R » (whoops)'), ('boudin_motul', (255, 60, 60), 'boudins Motul'), ('boudin_thor', (130, 130, 130), 'boudins Thor'),
       ('mur_', (255, 255, 255), 'murs de virage (sponsor écrit)'), ('filet', (255, 0, 255), 'filets'), ('pylone', (255, 200, 0), 'poteaux ronds'),
       ('amv_jupe', (0, 150, 64), 'bâche AMV (saut du milieu)'), ('rampe_honda', (255, 0, 0), 'rampe + coins Honda'), ('ramp_50', (60, 60, 60), 'tremplins FMX (Venum)'),
       ('minerva', (0, 220, 90), 'portique Minerva Oil'), ('arche_50', (250, 224, 22), 'arche 50 Factory'), ('depart', (0, 0, 0), 'bandeau START + mur de fond'),
       ('finish', (0, 255, 255), 'panneau FINISH suspendu'), ('canette', (90, 255, 0), 'canettes Monster'), ('semi_', (40, 90, 200), 'camions du paddock'),
       ('start_grids', (90, 90, 90), 'grilles de départ'), ('flag_cage', (255, 160, 0), 'cage du drapeau')]


def vue_dessus(ST, models):
    import build_paris as B
    im = Image.open(os.path.join(HERE, "apercu", "vue_dessus.png")).convert("RGB")
    dims = B.arena_dims(); floor = B.mx_poly(dims.floor_outline(1.0)); S = 0.28975; k = 1 / (S * 4)
    xs, zs = floor[:, 0] * k, floor[:, 1] * k
    box = (int(xs.min()) - 30, int(zs.min()) - 30, int(xs.max()) + 30, int(zs.max()) + 30); W, Hh = box[2] - box[0], box[3] - box[1]
    Z = 2                                                   # agrandi x2 pour lire les noms
    im = im.resize((im.size[0] * Z, im.size[1] * Z), Image.LANCZOS)
    P = lambda x, z: ((W - (x * k - box[0])) * 2 * Z, (Hh - (z * k - box[1])) * 2 * Z)      # même cadrage que build_paris.top_view
    d = ImageDraw.Draw(im); f = ImageFont.truetype("arialbd.ttf", 22); fs = ImageFont.truetype("arialbd.ttf", 17)
    seen = set(); labels = {}
    for x, y, z, a, mdl, tex in ST:
        key = tex.split('/')[-1]; col, lab = next(((c, l) for p, c, l in COL if key.startswith(p) or mdl.split('/')[-1].startswith(p)), ((200, 200, 200), key))
        V = models[mdl][0]; x0, x1, z0, z1 = V[:, 0].min(), V[:, 0].max(), V[:, 2].min(), V[:, 2].max()
        c, s = np.cos(a), np.sin(a)
        poly = [P(x + lx * c + lz * s, z - lx * s + lz * c) for lx, lz in ((x0, z0), (x1, z0), (x1, z1), (x0, z1))]
        d.polygon(poly, fill=col, outline=(0, 0, 0)); seen.add(lab)
        if key.startswith('mur_') or key.startswith('semi_'):
            labels.setdefault((key, round(x / 60), round(z / 60)), []).append(P(x, z))
    for (key, _, _), pts in labels.items():                 # nom du sponsor sur les murs et les camions
        px, py = np.mean(pts, axis=0); t = key.replace('mur_', '').replace('semi_', '').replace('.png', '').upper()
        d.text((px, py), t, fill=(255, 255, 255), font=fs, anchor='mm', stroke_width=3, stroke_fill=(0, 0, 0))
    big = Image.new("RGB", (im.size[0] + 380, im.size[1]), (250, 250, 250)); big.paste(im, (380, 0)); im = big; d = ImageDraw.Draw(im)
    y = 12                                                  # légende à côté de la vue (elle ne cache rien)
    for p, c, lab in COL:
        if lab in seen:
            d.rectangle([14, y + 4, 34, y + 20], fill=c, outline=(0, 0, 0)); d.text((42, y), lab, fill=(0, 0, 0), font=f); y += 26
    out = os.path.join(HERE, "apercu", "vue_dessus_habillage.png"); im.save(out); print(out)


def obj_3d(ST, models, H, S):
    tex_dir = os.path.join(SB, "textures"); mats = {}; groups = {}
    for x, y, z, a, mdl, tex in ST:
        g = float(H[int(round(z / S)), int(round(x / S))]); V, I = models[mdl]
        P, N = world(V, x, y, z, a, g)
        A = np.c_[(P[:, 0] - LP.OX) / FT, -(P[:, 2] - LP.OZ) / FT, P[:, 1] / FT]; Nn = np.c_[N[:, 0], -N[:, 2], N[:, 1]]
        key = 'hab_' + tex.split('/')[-1][:-4]
        if key not in mats:
            src = os.path.join(T, tex); shutil.copy(src, os.path.join(tex_dir, key + '.png'))
            al = Image.open(src).mode == 'RGBA'
            mats[key] = dict(tex=key + '.png', alpha=al, two_sided=al)
        groups.setdefault(key, []).append((A, Nn, V[:, 6:8], I))
    with open(os.path.join(SB, "obj", "_habillage.obj"), "w") as f:
        base = 0
        for key, parts in groups.items():
            f.write("o %s\n" % key)
            for A, Nn, UV, I in parts:
                f.write("\n".join("v %.3f %.3f %.3f" % tuple(p) for p in A) + "\n")
                f.write("\n".join("vt %.5f %.5f" % tuple(u) for u in UV) + "\n")
                f.write("\n".join("vn %.4f %.4f %.4f" % tuple(n) for n in Nn) + "\n")
            f.write("usemtl %s\n" % key)
            for A, Nn, UV, I in parts:
                f.write("\n".join("f %d %d %d" % tuple(t + base + 1) for t in I) + "\n"); base += len(A)
    json.dump(mats, open(os.path.join(SB, "extra_mats.json"), "w", encoding="utf-8"), indent=1)
    v = lambda x, y, z: [(x - LP.OX) / FT, y / FT, (z - LP.OZ) / FT]        # monde MX (ft) -> aperçu (m)
    views = {
        'Habillage : saut du milieu (AMV)': [v(600, 45, 760), v(555, 6, 644)],
        'Habillage : tremplins Venum': [v(610, 14, 700), v(562, 5, 650)],
        'Habillage : arrivée (Honda, FINISH)': [v(640, 22, 420), v(566, 12, 474)],
        'Habillage : départ': [v(660, 9, 548), v(737, 8, 548)],
        'Habillage : départ + Minerva Oil': [v(690, 16, 640), v(752, 5, 600)],
        'Habillage : paddock': [v(700, 70, 420), v(790, 0, 590)],
        'Habillage : arche 50 Factory': [v(585, 14, 462), v(659, 12, 431)],
        'Habillage : virage Honda + filet': [v(640, 16, 690), v(735, 4, 730)],
        'Habillage : whoops (boudins R)': [v(720, 12, 751), v(560, 1, 751)],
        'Habillage : virage Seong + filet Venum': [v(430, 16, 520), v(335, 4, 425)],
        'Habillage : premier virage (Automoto, Motul)': [v(470, 18, 600), v(385, 2, 540)],
        'Habillage : vue générale': [v(300, 150, 900), v(560, 0, 590)],
    }
    json.dump(views, open(os.path.join(SB, "extra_views.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("aperçu 3D :", len(ST), "objets,", len(mats), "textures")


if __name__ == "__main__":
    ST = statues(); models = {}
    for *_, mdl, tex in ST:
        if mdl not in models:
            models[mdl] = read_jm(os.path.join(T, mdl))
    H, S = terrain()
    vue_dessus(ST, models); obj_3d(ST, models, H, S)
