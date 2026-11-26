"""v23c : sponsors de l'utilisateur (commun/assets/logos/user, copiés de son dossier Logo) : couleur de fond + logo détouré, « la couleur du logo
que je t'ai envoyé » (Yamaha fond bleu logo blanc, Moto Verte fond blanc logo rouge, Honda fond rouge logo blanc, ...)."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
U = os.path.join(ROOT, "commun/assets", "logos", "user")
FILES = dict(mxsim='logo mxsim racing.png', motoverte='logo motoverte.png', milwaukee='logo milwaukee.jpg', honda='logo honda.jpeg',
             automoto='logo automoto.png', yamaha='yamaha.png', amv='amv.webp', minerva='LOGO-MINERVA-2022.png')
_C = {}


def _detour(path, plate=False):
    """fond = couleur médiane du bord ; si le logo est sur une plaque de couleur (Milwaukee, Yamaha), la plaque devient le fond."""
    im = Image.open(path).convert('RGBA'); a = np.asarray(im, float)
    if a[..., 3].min() < 10:                                         # PNG transparent (Minerva) : fond blanc
        al = a[..., 3]; ys, xs = np.nonzero(al > 10)
        return (14, 14, 15), im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))   # v23e : Minerva sur fond noir
    rgb = a[..., :3]; bd = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]]); b0 = np.median(bd, 0)
    m0 = np.linalg.norm(rgb - b0, axis=-1) > 45; ys, xs = np.nonzero(m0); c = rgb[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    mc = m0[ys.min():ys.max() + 1, xs.min():xs.max() + 1]; c1 = np.median(c[mc], 0)
    k_ = max(3, int(0.08 * min(mc.shape))); corners = [mc[k_, k_], mc[k_, -k_ - 1], mc[-k_ - 1, k_], mc[-k_ - 1, -k_ - 1]]
    if plate and sum(corners) >= 3:                                  # plaque de couleur (coins remplis) : elle devient le fond
        b0, mk = c1, np.linalg.norm(c - c1, axis=-1) > 70
        e_ = max(3, int(0.04 * min(mk.shape))); mk[:e_] = False; mk[-e_:] = False; mk[:, :e_] = False; mk[:, -e_:] = False   # pas le cadre
    else:
        mk = mc
    ys, xs = np.nonzero(mk); c = c[ys.min():ys.max() + 1, xs.min():xs.max() + 1]; mk = mk[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    from scipy.ndimage import gaussian_filter
    al = np.clip(gaussian_filter(mk.astype(float), 0.6) * 255, 0, 255)
    return tuple(int(v) for v in b0), Image.fromarray(np.dstack([c, al]).astype(np.uint8), 'RGBA')


def panel(key):
    """(couleur de fond, logo RGBA) d'un sponsor ; None -> noir sans logo."""
    if key in _C:
        return _C[key]
    import hab_kit as K
    if key is None:
        r = ((22, 22, 24), None)
    elif key == 'honda':                                             # fond rouge, logo blanc
        _, lg = _detour(os.path.join(U, FILES['honda'])); r = ((204, 8, 18), K.tint(lg, (245, 245, 245)))
    elif key == 'five':                                              # logo FIVE landscape de l'utilisateur (5 rouge + FIVE noir)
        r = ((246, 246, 244), _detour(os.path.join(U, 'five landscape.jpg'))[1])
    elif key == 'five5':                                             # « juste le 5 » : le 5 rouge du logo FIVE landscape
        _, lg = _detour(os.path.join(U, 'five landscape.jpg')); a = np.asarray(lg, float)
        red = (a[..., 0] > 150) & (a[..., 1] < 90) & (a[..., 3] > 40); ys, xs = np.nonzero(red)
        c = lg.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)); m_ = red[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        c = np.asarray(c).copy(); c[..., 3] = np.where(m_, c[..., 3], 0); r = ((246, 246, 244), Image.fromarray(c, 'RGBA'))
    elif key == '50factory':
        r = ((249, 229, 42), K.logo('50factory'))
    elif key == 'mv':                                                # Moto Verte : « juste le MV » (le symbole, ~le premier quart du logo)
        bg, lg = _detour(os.path.join(U, FILES['motoverte'])); w_ = int(0.295 * lg.size[0]); c_ = lg.crop((0, 0, w_, lg.size[1]))
        from scipy.ndimage import label   # v25c (« le petit point rouge ») : on enlève les morceaux de lettre coupés au bord droit
        a_ = np.asarray(c_).copy(); lab_, n_ = label(a_[..., 3] > 30)
        for i_ in range(1, n_ + 1):
            if (lab_[:, -3:] == i_).any():
                a_[lab_ == i_, 3] = 0
        c_ = Image.fromarray(a_, 'RGBA'); r = (bg, c_.crop(c_.getbbox()))
    elif key == 'amv_plaque':                                        # la plaque AMV entière (texte + personnages) : bâche de la réception du freestyle
        im = Image.open(os.path.join(U, FILES['amv'])).convert('RGB'); a = np.asarray(im, float)
        ys, xs = np.nonzero(np.linalg.norm(a - 255, axis=-1) > 40); c = im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)).convert('RGBA')
        r = ((0, 166, 81), c)
    elif key == 'amv':                                               # ballots : « juste les 3 lettres AMV, pas le dessin »
        im = Image.open(os.path.join(U, FILES['amv'])).convert('RGB'); W_, H_ = im.size; a = np.asarray(im, float)
        x0, x1, y0, y1 = int(0.30 * W_), int(0.70 * W_), int(0.06 * H_), int(0.42 * H_); sub = a[y0:y1, x0:x1]
        g_ = (sub[..., 1] > 120) & (sub[..., 0] < 100) & (sub[..., 2] < 140)
        from scipy.ndimage import label
        lab, n_ = label(g_); sizes = [(lab == i_).sum() for i_ in range(1, n_ + 1)]
        keep = np.isin(lab, [i_ + 1 for i_, sz in enumerate(sizes) if sz > 0.02 * g_.sum()])   # les lettres, pas les miettes
        ys, xs = np.nonzero(keep); c = np.dstack([sub, np.where(keep, 255, 0)])[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        r = ((246, 246, 244), Image.fromarray(c.astype(np.uint8), 'RGBA'))
    else:
        r = _detour(os.path.join(U, FILES[key]), plate=key in ('milwaukee', 'yamaha'))
    _C[key] = r
    return r
