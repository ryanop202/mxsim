"""v22h : VRAIES motos (modèles moddés installés dans MX Simulator, textures EN CLAIR) en statues pour le paddock.

Ryan : « pas les motos de base (moches), pas les tiennes, un entre-deux ». Les livrées d'équipe protégées (.png.scram, pack AMA 2026)
ne sont PAS utilisées (protection de leur auteur). On prend les motos moddées dont la texture est un .png normal, toutes sur la base
fc450v2016 du jeu (même assemblage) : Pack team USLAND (KTM #151 #16 #202 #348 #47 #9), Honda In So Cal (#16, #151), GasGas team,
Husqvarna violette, DewIsland KTM, KTM USLAND EVO3, CRF of Troy, 2026 RYAN BIKE. Usage privé : copies dans la piste ; pour une version
publique, demander l'accord de leurs auteurs.

Assemblage fc450v2016 (calé à l'œil sur des vues de profil, repère moto du jeu : pieds, avant = -z) : cadre (0, 0), bras oscillant
(dz 1,475, dy -0,25), fourche haute et basse (-1,70, +0,40), roue avant (-2,17, -0,27), roue arrière (2,50, -0,55). Statue : sol à
y = 0 (moto posée sur une béquille noire, roues juste au-dessus du sol), avant = +z (demi-tour), centrée entre les roues.
Texture unique 2048 : livrée réduite à 1792 px + roues (wheels.png du jeu) à 256 px. Maillage allégé (regroupement des sommets
proches de même UV) : ~200 000 -> ~25 000 triangles par moto.
"""
import os
import re
import gzip
import numpy as np
from PIL import Image

MXS = r"C:/Program Files (x86)/MX Simulator"
CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "mx_motos")   # hors dépôt
OFF = {"frame": (0.0, 0.0), "swingarm": (1.475, -0.25), "fork_upper": (-1.70, 0.40), "fork_lower": (-1.70, 0.40),
       "front_wheel": (-2.17, -0.27), "rear_wheel": (2.50, -0.55)}
Y_SOL = -1.75                                                              # sol sous la béquille (repère moto du jeu)
Z_MID = (OFF["front_wheel"][0] + OFF["rear_wheel"][0]) / 2
# nom -> (source : .saf ou dossier, suffixe des pièces, livrée)
MOTOS = {
    "ktm_usland_202": ("Pack team USLAND.saf", "-2025 KTM USLAND", "fc450v2016-2025 KTM USLAND-#202.png"),
    "ktm_usland_151": ("Pack team USLAND.saf", "-2025 KTM USLAND", "fc450v2016-2025 KTM USLAND-#151.png"),
    "ktm_usland_16": ("Pack team USLAND.saf", "-2025 KTM USLAND", "fc450v2016-2025 KTM USLAND-#16.png"),
    "ktm_usland_348": ("Pack team USLAND.saf", "-2025 KTM USLAND", "fc450v2016-2025 KTM USLAND-#348.png"),
    "ktm_usland_47": ("Pack team USLAND.saf", "-2025 KTM USLAND", "fc450v2016-2025 KTM USLAND-#47.png"),
    "ktm_usland_9": ("Pack team USLAND.saf", "-2025 KTM USLAND", "fc450v2016-2025 KTM USLAND-#9.png"),
    "honda_16": ("Honda BP in so cal X Elbouk.saf", "-2025 Honda In So Cal", "fc450v2016-2025 Honda In So Cal-16.png"),
    "honda_151": ("Honda BP in so cal X Elbouk.saf", "-2025 Honda In So Cal", "fc450v2016-2025 Honda In So Cal-151.png"),
}
LOCAL = os.path.join(os.environ.get("LOCALAPPDATA", ""), "MX Simulator")
MOTOS["stark"] = ("@local/2023 Stark Varg by Julien113.saf", "-Stark Varg", "@peint")   # forme du jeu, NOTRE texture peinte
_EXTRA = (("GasGAS Team 2023.saf", "gasgas"), ("husqy team maximus land 2023.saf", "husqvarna"), ("DewIslandKTM.saf", "ktm_dew"),
          ("EVO3 by fosure.saf", "ktm_evo3"), ("pack team otrt sx 2024.saf", "crf_troy"), ("2026 RYAN BIKE", "ryan"))


def _path(src):
    return os.path.join(LOCAL, src[7:]) if src.startswith("@local/") else os.path.join(MXS, src)


def _saf_files(src):
    """{nom de base: (taille, décalage) } d'un .saf (en-tête texte « taille chemin », « - », données concaténées)."""
    p = _path(src); f = open(p, "rb"); E = []
    while True:
        l = f.readline(); m = re.match(rb"^(\d+) (\S.*?)\r?\n$", l)
        if not m:
            break
        E.append((int(m.group(1)), m.group(2).decode("utf-8", "replace")))
    off = f.tell(); out = {}
    for size, n in E:
        out[os.path.basename(n)] = (size, off); off += size
    return out


def _get(src, name):
    """fichier d'un pack du jeu (copié dans le cache hors dépôt)."""
    os.makedirs(CACHE, exist_ok=True); c = os.path.join(CACHE, name)
    if os.path.exists(c):
        return c
    if os.path.isdir(os.path.join(MXS, src)):
        import shutil
        shutil.copy(os.path.join(MXS, src, name), c); return c
    F = _saf_files(src); key = name if name in F else name + ".gz"
    size, off = F[key]; f = open(_path(src), "rb"); f.seek(off); d = f.read(size)
    if key.endswith(".gz"):
        d = gzip.decompress(d)
    assert not key.endswith(".scram"), "texture protégée : non utilisée"
    open(c, "wb").write(d); return c


def _find_extra():
    """complète MOTOS avec les autres packs fc450v2016 à texture en clair (première livrée trouvée)."""
    for src, key in _EXTRA:
        try:
            names = os.listdir(os.path.join(MXS, src)) if os.path.isdir(os.path.join(MXS, src)) else list(_saf_files(src))
        except OSError:
            continue
        fr = [n for n in names if n.startswith("fc450v2016_frame-") and n.endswith(".jm")]
        if not fr:
            continue
        suf = fr[0][len("fc450v2016_frame"):-3]
        sk = sorted(n for n in names if n.startswith("fc450v2016" + suf) and n.endswith(".png") and not n.endswith(("_norm.png", "_spec.png")))
        if sk:
            MOTOS[key] = (src, suf, sk[0])


def _peindre(parts, N=1792):
    """texture faite ici (la livrée Stark du jeu est protégée) : chaque triangle est peint dans ses UV d'une couleur choisie
    d'après sa place sur la moto (repère moto du jeu, avant = -z) : plastiques blancs, selle noire, cadre / batterie gris foncé,
    bras oscillant alu, fourche noire. Style « Stark Varg Snow White » (forme créée, pas leur texture)."""
    from PIL import ImageDraw
    im = Image.new("RGB", (N, N), (48, 50, 54)); d = ImageDraw.Draw(im)
    WHITE, BLACK, DARK, ALU, GREY = (236, 236, 236), (22, 22, 24), (48, 50, 54), (172, 174, 178), (110, 112, 116)
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    for part, V, I in parts:
        # v22k : une couleur par PIÈCE (triangles reliés), d'après le centre de la pièce : plus de bords en dents de scie
        r_ = np.r_[I[:, 0], I[:, 1]]; c_ = np.r_[I[:, 1], I[:, 2]]
        _, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(len(V), len(V))), directed=False)
        tl = lab[I[:, 0]]; Cc = np.zeros((tl.max() + 1, 3)); np.add.at(Cc, tl, V[I, :3].mean(1)); Cc /= np.bincount(tl)[:, None]
        C = Cc[tl]; x, y, z = np.abs(C[:, 0]), C[:, 1], C[:, 2]
        if part == "frame":
            col = np.where(((y > 0.85) & (x > 0.22)) | ((z > 1.9) & (y > 0.75)), 0, np.where((y > 1.05) & (x <= 0.22), 1, np.where(y < 0.15, 2, 3)))
        elif part == "swingarm":
            col = np.full(len(I), 4)
        elif part == "fork_upper":
            col = np.where((C[:, 2] < -2.0) & (y < 0.75) & (y > 0.2), 0, np.where(y > 1.2, 1, 2))
        else:
            col = np.full(len(I), 1)
        pal = [WHITE, BLACK, DARK, GREY, ALU]
        for t, c in zip(I, col):
            uv = V[t, 6:8]; d.polygon([(u * N, (1 - v) * N) for u, v in uv], fill=pal[c])
    return im


def read_blocks(path):
    """blocs (matériau, V (n x 8), I (m x 3)) d'un .jm (avec ou sans en-tête JM1)."""
    T = open(path).read().split(); i = 1 if T[0] == "JM1" else 0; out = []
    while i < len(T):
        mat = "0 0 0 0 0"
        if "." in T[i]:
            mat = " ".join(T[i:i + 5]); i += 5
        nv, nt = int(T[i]), int(T[i + 1]); i += 2
        V = np.array(T[i:i + 8 * nv], float).reshape(nv, 8); i += 8 * nv
        I = np.array(T[i:i + 3 * nt], int).reshape(nt, 3); i += 3 * nt
        out.append((mat, V, I))
    return out


def decimate(V, I, eps=0.16, q=48):                                  # v22j : ~19 000 triangles / moto (Ryan : « pas trop lourd »)
    """regroupe les sommets proches (cellule eps en position ET même cellule d'UV) ; enlève les triangles dégénérés / en double."""
    key = np.c_[np.floor(V[:, :3] / eps).astype(np.int64), np.floor(V[:, 6:8] * q).astype(np.int64)]
    uk, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel(); n = len(uk)
    S = np.zeros((n, 8)); np.add.at(S, inv, V); cnt = np.bincount(inv, minlength=n)[:, None]; W = S / cnt
    W[:, 3:6] /= np.linalg.norm(W[:, 3:6], axis=1, keepdims=True) + 1e-9
    J = inv[I]; ok = (J[:, 0] != J[:, 1]) & (J[:, 1] != J[:, 2]) & (J[:, 0] != J[:, 2])
    J = np.unique(J[ok], axis=0)
    used = np.unique(J); remap = -np.ones(n, int); remap[used] = np.arange(len(used))
    return W[used], remap[J]


def build(name, out_dir):
    """écrit <out_dir>/vraie_<name>.jm + .png ; renvoie (jm, png, triangles)."""
    if name not in MOTOS:
        _find_extra()
    src, suf, skin = MOTOS[name]
    blocks = []; peint = []
    for part in ("frame", "swingarm", "fork_upper", "fork_lower"):
        for mat, V, I in read_blocks(_get(src, "fc450v2016_%s%s.jm" % (part, suf))):
            V = V.copy(); V[:, 2] += OFF[part][0]; V[:, 1] += OFF[part][1]
            if skin.startswith("@peint"):
                peint.append((part, V.copy(), I))
            V[:, 6] = V[:, 6] * 0.875; V[:, 7] = 0.125 + V[:, 7] * 0.875           # livrée : coin haut gauche, 1792 / 2048
            blocks.append((mat, V, I))
    for w in ("front_wheel", "rear_wheel"):
        for mat, V, I in read_blocks(_get("zzzz.saf", w + ".jm")):
            V = V.copy(); V[:, 2] += OFF[w][0]; V[:, 1] += OFF[w][1]
            V[:, 6] = 0.875 + V[:, 6] * 0.125; V[:, 7] = 0.875 + V[:, 7] * 0.125      # roues : 256 px en haut à droite
            blocks.append((mat + " roue", V, I))                            # v22k : roues JAMAIS allégées (jantes déformées)
    # béquille noire sous le moteur (couleur unie : carré noir de l'atlas, x 1800-1840, y 300-340)
    u0, v0 = 1820 / 2048, 1 - 320 / 2048
    bx = [(-0.42, 0.42), (Y_SOL, -0.88), (-0.05, 0.75)]
    P = np.array([[x, y, z] for x in bx[0] for y in bx[1] for z in bx[2]])
    F = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 2, 6, 4), (1, 5, 7, 3), (2, 3, 7, 6)]          # -x, +x, -z, +z, haut
    Vb, Ib = [], []
    for f in F:
        a, b, c, d = (P[k] for k in f); n_ = np.cross(b - a, c - a); n_ /= np.linalg.norm(n_); k0 = len(Vb)
        for p in (a, b, c, d):
            Vb.append([*p, *n_, u0, v0])
        Ib += [(k0, k0 + 1, k0 + 2), (k0, k0 + 2, k0 + 3)]
    blocks.append(("0 0 0 0 0", np.array(Vb, float), np.array(Ib)))
    # repère statue : sol y = 0, centré entre les roues, avant = +z (demi-tour autour de y)
    L = ["JM1"]; nt = 0
    for mat, V, I in blocks:
        roue = mat.endswith(" roue"); mat = mat.replace(" roue", "")
        if len(I) > 500 and not roue:
            V, I = decimate(V, I)
        if len(I) == 0 or len(V) == 0:                                      # bloc vidé par l'allègement : pas écrit
            continue
        V = V.copy(); V[:, 1] -= Y_SOL; V[:, 2] -= Z_MID; V[:, [0, 2, 3, 5]] *= -1
        L += [mat, "%d %d" % (len(V), len(I))] + [" ".join("%.5f" % x for x in r) for r in V] + ["%d %d %d" % tuple(t) for t in I]
        nt += len(I)
    jm = "vraie_%s.jm" % name
    with gzip.open(os.path.join(out_dir, jm + ".gz"), "wt", newline="\n") as fh:          # le jeu lit les .jm.gz (comme le stade)
        fh.write("\n".join(L) + "\n")
    A = Image.new("RGB", (2048, 2048), (20, 20, 22))
    if skin.startswith("@uni:"):                                            # texture protégée : on n'y touche pas, couleur unie
        A.paste(Image.new("RGB", (1792, 1792), tuple(int(c) for c in skin[5:].split(","))), (0, 0))
    elif skin.startswith("@peint"):                                         # v22k : NOTRE texture, peinte d'après la forme
        A.paste(_peindre(peint), (0, 0))
    else:
        A.paste(Image.open(_get(src, skin)).convert("RGB").resize((1792, 1792), Image.LANCZOS), (0, 0))
    A.paste(Image.open(_get("zzzz.saf", "wheels.png")).convert("RGB").resize((256, 256), Image.LANCZOS), (1792, 0))
    png = "vraie_%s.png" % name; A.save(os.path.join(out_dir, png), optimize=True)
    return jm, png, nt


if __name__ == "__main__":
    import sys
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    for n in sys.argv[2:]:
        print(build(n, out))
