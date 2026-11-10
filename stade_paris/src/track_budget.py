"""Mesure le poids géométrique d'une piste MX installée (somme sur toutes les statues placées).

  py -3.12 -I src/track_budget.py <dossier_de_piste> [<dossier_racine_du_jeu>]
Les modèles introuvables sur disque (dans des .saf) sont comptés à part.
"""
import os
import re
import sys
import gzip
from collections import Counter

track = sys.argv[1]
roots = [os.path.dirname(track.rstrip("/\\"))] + sys.argv[2:]
pat = re.compile(r"^\[[^\]]*\]\s+\S+\s+(\S+)\s+(\S+)")
cache = {}


def find(ref):
    rel = ref[1:]
    for r in roots:
        for cand in (rel, rel + ".gz"):
            p = os.path.join(r, cand)
            if os.path.exists(p):
                return p
            # recherche insensible à la casse
            d, f = os.path.split(p)
            if os.path.isdir(d):
                for x in os.listdir(d):
                    if x.lower() == f.lower():
                        return os.path.join(d, x)
    return None


def count(path):
    if path in cache:
        return cache[path]
    op = gzip.open if path.endswith(".gz") else open
    nv = nt = 0
    with op(path, "rt", errors="ignore") as f:
        lines = f.read().split("\n")
    i = 0
    if lines and lines[0].startswith("JM"):
        i = 1
        if lines[0] == "JM2":
            i = 3
    while i < len(lines) - 1:
        head = lines[i].split()
        if len(head) == 5:
            i += 1
        parts = lines[i].split()
        if len(parts) != 2:
            break
        v, t = int(parts[0]), int(parts[1])
        nv += v; nt += t
        i += 1 + v
        # indices : 3 par ligne ou 1 par ligne
        if i < len(lines) and len(lines[i].split()) == 3:
            i += t
        else:
            i += 3 * t
    cache[path] = (nv, nt)
    return nv, nt


tv = tt = n = miss = 0
tex = Counter()
for line in open(os.path.join(track, "statues"), errors="ignore"):
    m = pat.match(line.strip())
    if not m:
        continue
    n += 1
    p = find(m.group(1))
    tex[m.group(2)] += 1
    if p is None:
        miss += 1
        continue
    v, t = count(p)
    tv += v; tt += t
print("%s : %d statues, %d sommets, %d triangles (%d modèles introuvables / .saf), %d textures distinctes"
      % (os.path.basename(track.rstrip('/\\')), n, tv, tt, miss, len(tex)))
