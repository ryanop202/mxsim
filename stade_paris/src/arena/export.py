"""Exports : OBJ (prévisualisation Blender, mètres Z-up) et JM1 (MX Simulator, pieds Y-up).

Conversion JM vérifiée sur les fichiers du jeu (voir docs/03_format_mx_simulator.md) :
  (X, Y, Z)_local  ->  (X, Z, -Y) * 3.28084      rotation propre (det=+1) : sens des triangles conservé
  UV identiques (v=0 en bas de l'image), indices base 0, triangles anti-horaires = face avant.
"""
import os
import json
import numpy as np

from .materials import MATERIALS

FT = 3.28084
MAX_VERTS = 60000          # marge sous 65 535 (indices potentiellement 16 bits, non vérifié)


def _fmt(a):
    return "\n".join(" ".join("%.5f" % x for x in row) for row in a)


def to_mx(V):
    V = np.asarray(V, float)
    return np.column_stack([V[:, 0], V[:, 2], -V[:, 1]]) * FT


def nrm_to_mx(N):
    N = np.asarray(N, float)
    return np.column_stack([N[:, 0], N[:, 2], -N[:, 1]])


def split_mesh(m, max_verts=MAX_VERTS):
    """Découpe un maillage en blocs de <= max_verts sommets (faces consécutives)."""
    if m.nv <= max_verts:
        return [m]
    from .mesh import Mesh
    out = []
    start = 0
    F = m.F
    while start < len(F):
        used = {}
        k = start
        while k < len(F):
            new = [i for i in F[k] if i not in used]
            if len(used) + len(new) > max_verts:
                break
            for i in new:
                used[i] = len(used)
            k += 1
        idx = np.fromiter(used.keys(), int)
        remap = np.full(m.nv, -1)
        remap[idx] = np.arange(len(idx))
        out.append(Mesh(m.V[idx], m.N[idx], m.UV[idx], remap[F[start:k]]))
        start = k
    return out


def jm_text(m, material):
    mat = MATERIALS[material]
    blocks = []
    V = to_mx(m.V); N = nrm_to_mx(m.N)
    vert = np.column_stack([V, N, m.UV])
    if mat.get("unlit"):
        head = "-2 0 1 1 1"
    else:
        head = " ".join("%g" % x for x in mat.get("jm", (0, 0, 0, 0, 0)))
    blocks.append("%s\n%d %d\n%s\n%s" % (head, len(V), m.nf, _fmt(vert), "\n".join("%d %d %d" % tuple(f) for f in m.F)))
    if mat.get("env", 0) > 0 and not mat.get("unlit"):
        e = mat["env"]
        blocks.append("-1 %g 1 1 1\n%d %d\n%s\n%s" % (e, len(V), m.nf, _fmt(vert), "\n".join("%d %d %d" % tuple(f) for f in m.F)))
    return "JM1\n" + "\n".join(blocks) + "\n"


def write_jm(m, material, path):
    with open(path, "w", newline="\n") as f:
        f.write(jm_text(m, material))


def write_obj(meshes_by_mat, path, mtl_name="arena.mtl"):
    """meshes_by_mat : dict matériau -> Mesh. Un objet OBJ par matériau."""
    lines = ["mtllib %s" % mtl_name]
    off = 1
    for mat, m in meshes_by_mat.items():
        lines.append("o %s" % mat)
        lines.append(_fmt_prefixed("v", m.V))
        lines.append(_fmt_prefixed("vt", m.UV))
        lines.append(_fmt_prefixed("vn", m.N))
        lines.append("usemtl %s" % mat)
        F = m.F + off
        lines.append("\n".join("f %d/%d/%d %d/%d/%d %d/%d/%d" % (a, a, a, b, b, b, c, c, c) for a, b, c in F))
        off += m.nv
    with open(path, "w", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def _fmt_prefixed(p, a):
    if len(a) == 0:
        return ""
    return "\n".join(p + " " + " ".join("%.4f" % x for x in row) for row in a)


def write_material_manifest(path, tex_dir):
    out = {}
    for k, v in MATERIALS.items():
        d = dict(v)
        d["tex_path"] = os.path.join(tex_dir, v["tex"])
        out[k] = d
    with open(path, "w") as f:
        json.dump(out, f, indent=1)
