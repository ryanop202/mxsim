"""Contrôle du dossier de piste exporté (sans lancer le jeu).

  py -3.12 -I src/validate_mx.py [dossier]
Vérifie : syntaxe JM1 (blocs, nombres, indices dans les bornes, triangles dégénérés, normales unitaires),
références des statues (modèle .jm/.jm.gz et texture présents), textures en puissance de 2,
fichiers terrain cohérents (terrain.hf / terrain.png / tilemap / shading), fins de ligne LF.
"""
import os
import re
import sys
import gzip
import json
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TRACK_DIR = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "export", "ParisLaDefenseArena")
TRACK = os.path.basename(TRACK_DIR.rstrip("/\\"))
problems, notes = [], []


def resolve(ref):
    assert ref.startswith("@" + TRACK + "/"), ref
    p = os.path.join(TRACK_DIR, ref[len(TRACK) + 2:])
    if os.path.exists(p):
        return p
    if os.path.exists(p + ".gz"):
        return p + ".gz"
    return None


def read_jm(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt") as f:
        txt = f.read()
    if "\r" in txt:
        problems.append("CRLF dans %s" % path)
    tok = txt.split()
    assert tok[0] == "JM1", path
    i = 1
    blocks = []
    while i < len(tok):
        head = list(map(float, tok[i:i + 5])); i += 5
        nv, nt = int(tok[i]), int(tok[i + 1]); i += 2
        V = np.array(tok[i:i + nv * 8], float).reshape(nv, 8); i += nv * 8
        F = np.array(tok[i:i + nt * 3], int).reshape(nt, 3); i += nt * 3
        blocks.append((head, V, F))
    return blocks


stats = dict(models=0, blocks=0, verts=0, tris=0, max_verts=0, degenerate=0, bad_normals=0)
for f in sorted(os.listdir(os.path.join(TRACK_DIR, "statue"))):
    p = os.path.join(TRACK_DIR, "statue", f)
    try:
        bl = read_jm(p)
    except Exception as e:
        problems.append("JM illisible %s : %s" % (f, e))
        continue
    stats["models"] += 1
    for head, V, F in bl:
        stats["blocks"] += 1
        stats["verts"] += len(V); stats["tris"] += len(F)
        stats["max_verts"] = max(stats["max_verts"], len(V))
        if len(V) > 65535:
            problems.append("%s : %d sommets (> 65535)" % (f, len(V)))
        if len(F) and (F.min() < 0 or F.max() >= len(V)):
            problems.append("%s : indice hors bornes" % f)
        if not np.isfinite(V).all():
            problems.append("%s : valeurs non finies" % f)
        nl = np.linalg.norm(V[:, 3:6], axis=1)
        stats["bad_normals"] += int(np.sum(np.abs(nl - 1) > 0.02))
        a, b, c = V[F[:, 0], :3], V[F[:, 1], :3], V[F[:, 2], :3]
        stats["degenerate"] += int(np.sum(np.linalg.norm(np.cross(b - a, c - a), axis=1) < 1e-8))

nst = 0
missing = set()
with open(os.path.join(TRACK_DIR, "statues"), "rb") as fh:
    raw = fh.read()
if b"\r" in raw:
    problems.append("CRLF dans statues")
pat = re.compile(r"^\[\s*(\S+)\s+(\S+)\s+(\S+)\s*\]\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)$")
for line in raw.decode().splitlines():
    m = pat.match(line.strip())
    if not m:
        problems.append("ligne statues invalide : %s" % line[:80]); continue
    nst += 1
    for ref in (m.group(5), m.group(6)):
        if resolve(ref) is None:
            missing.add(ref)
if missing:
    problems.append("%d références introuvables : %s" % (len(missing), sorted(missing)[:5]))

npo2 = []
for f in os.listdir(os.path.join(TRACK_DIR, "tex")):
    w, h = Image.open(os.path.join(TRACK_DIR, "tex", f)).size
    if (w & (w - 1)) or (h & (h - 1)):
        npo2.append("%s %dx%d" % (f, w, h))
if npo2:
    problems.append("textures non puissance de 2 : %s" % npo2)

n, sp, lo, hi = open(os.path.join(TRACK_DIR, "terrain.hf")).read().split()
n = int(n); size = 2 ** (n + 1) + 1
im = Image.open(os.path.join(TRACK_DIR, "terrain.png"))
if im.size != (size, size):
    problems.append("terrain.png %s au lieu de %d²" % (im.size, size))
tm = os.path.getsize(os.path.join(TRACK_DIR, "tilemap"))
if tm != (2 ** n) ** 2:
    problems.append("tilemap %d octets au lieu de %d" % (tm, (2 ** n) ** 2))
ntiles = open(os.path.join(TRACK_DIR, "tileinfo")).read().count("addtile")
tmax = int(np.fromfile(os.path.join(TRACK_DIR, "tilemap"), np.uint8).max())
if tmax >= ntiles:
    problems.append("tilemap utilise la tuile %d mais tileinfo n'en a que %d" % (tmax, ntiles))
for f in ("shading.ppm", "shadingx2.ppm"):
    with open(os.path.join(TRACK_DIR, f), "rb") as fh:
        hdr = fh.read(20).split(b"\n")
    if hdr[1] != b"%d %d" % (size, size):
        problems.append("%s : taille %s" % (f, hdr[1]))
for f in ("terrain.hf", "terrain.png", "tilemap", "tileinfo", "shading.ppm", "shadingx2.ppm", "lighting",
          "statues", "decals", "timing_gates", "desc"):
    if not os.path.exists(os.path.join(TRACK_DIR, f)):
        problems.append("fichier requis absent : " + f)

stats.update(statues=nst, textures=len(os.listdir(os.path.join(TRACK_DIR, "tex"))), problems=problems)
print(json.dumps(stats, indent=1, ensure_ascii=False))
with open(os.path.join(ROOT, "build", "validate_mx.json"), "w", encoding="utf8") as f:
    json.dump(stats, f, indent=1, ensure_ascii=False)
sys.exit(1 if problems else 0)
