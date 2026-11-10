"""Relevé IGN LiDAR HD (MNS/MNT 0,5 m) ramené dans le repère local de l'arène.

Repère local (mètres) :
  X : axe long, vers le NNE (azimut vrai 25,5°), vers le mur de scène et les bureaux
  Y : vers l'ONO (façade Ouest, entrée 33)
  Z : hauteur au-dessus du sol de référence 54,60 m NGF
Origine : point L93 (643518.2 ; 6866462.9) décalé de 3 m vers -v pour centrer l'axe du bâtiment
(les rives longues mesurées sont à v = +79,5 et v = -85,5).
"""
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PUB = os.path.join(ROOT, "references", "public")

XMIN, YMIN, RES, N = 643393.0, 6866322.0, 0.5, 520
CX, CY = 643518.2, 6866462.9
AZ_TRUE, CONV = 25.5, -0.58
GREF = 54.60
V_OFFSET = -3.0          # axe du bâtiment = v de -3 m dans le repère du relevé

_ang = np.radians(90.0 - (AZ_TRUE - CONV))
_cu, _su = np.cos(_ang), np.sin(_ang)


def _load(name):
    a = np.fromfile(os.path.join(PUB, name), dtype="<f4").reshape(N, N).astype(np.float64)
    a[a < -100] = np.nan
    return a


_MNS = None
_MNT = None


def rasters():
    global _MNS, _MNT
    if _MNS is None:
        _MNS, _MNT = _load("MNS.bil"), _load("MNT.bil")
    return _MNS, _MNT


def local_to_l93(X, Y):
    u = np.asarray(X, float)
    v = np.asarray(Y, float) + V_OFFSET
    return CX + u * _cu - v * _su, CY + u * _su + v * _cu


def _bilinear(a, x, y):
    c = (x - XMIN) / RES - 0.5
    r = (YMIN + N * RES - y) / RES - 0.5
    c0 = np.clip(np.floor(c).astype(int), 0, N - 2)
    r0 = np.clip(np.floor(r).astype(int), 0, N - 2)
    fc = np.clip(c - c0, 0, 1)
    fr = np.clip(r - r0, 0, 1)
    v00 = a[r0, c0]; v01 = a[r0, c0 + 1]; v10 = a[r0 + 1, c0]; v11 = a[r0 + 1, c0 + 1]
    out = (v00 * (1 - fc) + v01 * fc) * (1 - fr) + (v10 * (1 - fc) + v11 * fc) * fr
    inside = (c >= 0) & (c <= N - 1) & (r >= 0) & (r <= N - 1)
    return np.where(inside, out, np.nan)


def dsm(X, Y):
    """Hauteur du MNS au-dessus de GREF au point local (X, Y)."""
    mns, _ = rasters()
    x, y = local_to_l93(X, Y)
    return _bilinear(mns, x, y) - GREF


def dtm(X, Y):
    _, mnt = rasters()
    x, y = local_to_l93(X, Y)
    return _bilinear(mnt, x, y) - GREF


def local_grid(xmin, xmax, ymin, ymax, step):
    xs = np.arange(xmin, xmax + 1e-9, step)
    ys = np.arange(ymin, ymax + 1e-9, step)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    return xs, ys, dsm(X, Y), dtm(X, Y)


def smooth2d(a, sigma_px):
    """Flou gaussien séparable qui ignore les NaN."""
    if sigma_px <= 0:
        return a
    r = int(3 * sigma_px + 1)
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma_px) ** 2)
    m = np.isfinite(a).astype(float)
    v = np.where(np.isfinite(a), a, 0.0)

    def conv(z, axis):
        return np.apply_along_axis(lambda s: np.convolve(s, k, mode="same"), axis, z)

    num = conv(conv(v, 0), 1)
    den = conv(conv(m, 0), 1)
    with np.errstate(invalid="ignore", divide="ignore"):
        out = num / den
    out[den < 1e-6] = np.nan
    return out
