"""v19c (« il n'y a plus la texture, c'est tout lisse, remets la texture ; on voit les gradients, les lignes ») : dalle de terre sans
couture faite à partir de la terre ZION vue en jeu (milieu opaque de decal/180.png + son relief 180_tnorm.png) :
  - on garde le grain fin (rayures, cailloux) et on enlève les grandes formes du virage (passe-haut, flou de 30 px retiré) ;
  - pastilles rondes (bord fondu) tournées au hasard et superposées, toutes à la couleur moyenne de la décal ZION : pas de bord
    visible ni de motif répété (une dalle en miroir faisait un kaléidoscope).
  terre_zion.make(dossier_zdecal, dossier_decal_ZION) -> 'terre.png' (+ 'terre_tnorm.png'), taille de la dalle en ft
"""
import os
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

C0, C1, FT_PX = 600, 1450, 135.1 / 2048          # zone opaque de 180.png ; échelle de la décal ZION (135,1 ft pour 2048 px)


def _hp(a, sig=30.0):
    return a - np.dstack([gaussian_filter(a[..., k], sig) for k in range(a.shape[2])])


def _mirror(a, normal=False):
    h = a[:, ::-1].copy(); v = a[::-1].copy(); hv = a[::-1, ::-1].copy()
    if normal:                                     # écart au plat (128) : x inversé dans les copies retournées en x, y en y
        h[..., 0] = -h[..., 0]; v[..., 1] = -v[..., 1]; hv[..., 0] = -hv[..., 0]; hv[..., 1] = -hv[..., 1]
    return np.vstack([np.hstack([a, h]), np.hstack([v, hv])])


def make(out, zion_decal, alpha=0.9, base=None, gain=1.6):
    """pastille ronde : grain fin (passe-haut) sur la couleur moyenne de la décal ZION, bord fondu en rond ; posée en grand nombre,
    tournée au hasard et superposée : même couleur moyenne partout (pas de bord visible), le motif ne se répète pas."""
    c = np.asarray(Image.open(os.path.join(zion_decal, "180.png")).convert("RGBA"), float)[C0:C1, C0:C1]
    n = np.asarray(Image.open(os.path.join(zion_decal, "180_tnorm.png")).convert("RGBA"), float)[C0:C1, C0:C1]
    # couleur = celle de la tuile de terre (base) : les pastilles ne changent que le grain, jamais la teinte -> aucun bord visible
    mean = np.asarray(base, float) if base is not None else c[..., :3].reshape(-1, 3).mean(0); N = C1 - C0
    yy, xx = np.mgrid[0:N, 0:N]; rr = np.hypot(xx - N / 2, yy - N / 2) / (N / 2)
    f = np.clip((1.0 - rr) / 0.5, 0, 1); f = f * f * (3 - 2 * f)
    A = (255.0 * alpha * f)[..., None]
    col = _hp(c[..., :3]) * gain + mean
    nrm = _hp(n[..., :3]) + np.array([128.0, 128.0, 255.0]); nrm[..., 2] = 255.0
    for arr, name in ((np.dstack([col, A]), "terre.png"), (np.dstack([nrm, A]), "terre_tnorm.png")):
        Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA").resize((1024, 1024), Image.LANCZOS).save(os.path.join(out, name))
    return "terre.png", N * FT_PX
