"""Saint-Georges v30: the user's two logos cleaned up for the props (user: "tu le revectorises, tu mets les lettres en rouge").
- logo_supercross.jpg (800 px, black and white): redrawn 4x larger with clean edges (smooth upscale + threshold), the big
  letters (SUPER sx CROSS FREESTYLE) filled red instead of white, outlines / disc / town name kept black, background
  transparent -> assets/logos/supercross_sgm.png (RGBA)
- logo_mxshopmoto.jpg (447 px): same clean-up (black / white, the "MX" kept red), background transparent, the white parts
  of the drawing kept white (wings, tyre) -> assets/logos/mxshopmoto.png (RGBA)
Run: python scripts/sgm_logos.py"""
import os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as nd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = f'{ROOT}/assets/sgm/user'; OUT = f'{ROOT}/assets/logos'
RED = np.array([206, 28, 34.0]); BLACK = np.array([16, 16, 18.0]); WHITE = np.array([250, 250, 248.0])

def clean(path, k=4, sig=1.6):
    a = np.asarray(Image.open(path).convert('RGB')).astype(float)
    big = np.asarray(Image.fromarray(a.astype(np.uint8)).resize((a.shape[1] * k, a.shape[0] * k), Image.BICUBIC)).astype(float)
    L = nd.gaussian_filter(big.mean(2), sig)
    return a, big, L

def edge_alpha(L, thr=128.0, soft=10.0):
    """0 = black ink, 1 = white paper, a 2-3 px anti-aliased edge (no jpeg noise)."""
    return np.clip((L - thr) / soft + 0.5, 0, 1)

def supercross(letters='red', name='supercross_sgm.png'):
    a, big, L = clean(f'{SRC}/logo_supercross.jpg'); k = big.shape[0] // a.shape[0]
    w = edge_alpha(L)
    lab, n = nd.label(w > 0.5); sizes = nd.sum(np.ones_like(L), lab, range(1, n + 1))
    bg = 1 + int(np.argmax(sizes))
    sl = nd.find_objects(lab)
    red = np.zeros(L.shape, bool)
    for i, s in enumerate(sl):
        if s is None or i + 1 == bg: continue
        y0, y1, x0, x1 = s[0].start / k, s[0].stop / k, s[1].start / k, s[1].stop / k
        big_letter = sizes[i] > 500 * k * k and 150 < y0 and y1 < 615             # the big lettering, not the swoosh arcs (top) / town name counters
        if big_letter: red |= lab == i + 1
    redw = nd.binary_dilation(red, iterations=2) & (w > 0.02)                   # red right up to the black outline (soft edge)
    col = BLACK * (1 - w[..., None]) + WHITE * w[..., None]
    LET = RED if letters == 'red' else WHITE                                    # v33 (user): white letters on the sign (stand out better)
    col = np.where(redw[..., None], BLACK * (1 - w[..., None]) + LET * w[..., None], col)
    # alpha: everything inside the outer white background is opaque; the background itself transparent (soft edge)
    bgm = lab == bg; inside = nd.binary_fill_holes(~bgm)
    alpha = np.where(inside, 1.0, 1 - w)
    # keep the white halo of the disc (the thin white ring around it is part of the background in the jpeg): opaque white
    # band 6 px (source) around the ink so the logo reads on a dark tarp
    halo = nd.binary_dilation(alpha > 0.5, iterations=6 * k) & ~(alpha > 0.5)
    alpha = np.maximum(alpha, nd.gaussian_filter(halo.astype(float), 2))
    col = np.where((halo & ~inside)[..., None], WHITE, col)
    im = Image.fromarray(np.dstack([np.clip(col, 0, 255), np.clip(alpha, 0, 1) * 255]).astype(np.uint8), 'RGBA')
    im = im.crop(im.getbbox()); os.makedirs(OUT, exist_ok=True); im.save(f'{OUT}/{name}', optimize=True)
    print('supercross_sgm.png', im.size, 'red letters px', int(redw.sum()))
    return im

def mxshopmoto():
    a, big, L = clean(f'{SRC}/logo_mxshopmoto.jpg', k=5, sig=1.8); k = 5
    w = edge_alpha(L)
    sat = big.max(2) - big.min(2); redm = nd.gaussian_filter(((big[..., 0] > 140) & (sat > 70)).astype(float), 1.5) > 0.5   # "MX"
    lab, n = nd.label(w > 0.5)
    edge_ids = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]]).tolist()) - {0}
    bgm = np.isin(lab, list(edge_ids))                         # every white region touching the border (the wings split it)
    col = BLACK * (1 - w[..., None]) + WHITE * w[..., None]
    col = np.where(redm[..., None], RED, col)
    inside = nd.binary_fill_holes(~bgm | redm)
    alpha = np.where(inside, 1.0, 1 - w)
    halo = nd.binary_dilation(alpha > 0.5, iterations=4 * k) & ~(alpha > 0.5)
    alpha = np.maximum(alpha, nd.gaussian_filter(halo.astype(float), 2)); col = np.where(halo[..., None], WHITE, col)
    im = Image.fromarray(np.dstack([np.clip(col, 0, 255), np.clip(alpha, 0, 1) * 255]).astype(np.uint8), 'RGBA')
    im = im.crop(im.getbbox()); im.save(f'{OUT}/mxshopmoto.png', optimize=True); print('mxshopmoto.png', im.size)
    return im

def bazowurx():
    """v31 (user: 'le Baselworks' = the user's BAZOWURX logo, C:/Users/basil/OneDrive/Logo/bazowurx.png, black on light grey):
    clean black letters (assets/logos/bazowurx_clean.png) and the same with a white outline round every letter
    (assets/logos/bazowurx_outline.png, for the black tarp of the sign: 'avec les contours blancs')."""
    a = np.asarray(Image.open(f'{ROOT}/assets/logos/bazowurx.png').convert('RGB')).astype(float); k = 2
    big = np.asarray(Image.fromarray(a.astype(np.uint8)).resize((a.shape[1] * k, a.shape[0] * k), Image.BICUBIC)).astype(float)
    L = nd.gaussian_filter(big.mean(2), 1.2); ink = np.clip((140 - L) / 30 + 0.5, 0, 1)
    im = Image.fromarray(np.dstack([np.zeros(L.shape + (3,)) + BLACK, ink * 255]).astype(np.uint8), 'RGBA'); im = im.crop(im.getbbox())
    pad = 60; c = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0)); c.paste(im, (pad, pad)); im = c
    im.save(f'{OUT}/bazowurx_clean.png', optimize=True)
    al = np.asarray(im)[..., 3] / 255.0; m = al > 0.5
    ring = nd.gaussian_filter(nd.binary_dilation(m, iterations=14).astype(float), 1.2)
    col = np.where((al > 0.5)[..., None], BLACK, WHITE)
    ao = np.maximum(ring, al)
    out = Image.fromarray(np.dstack([col * np.ones(al.shape + (3,)), ao * 255]).clip(0, 255).astype(np.uint8), 'RGBA')
    out.save(f'{OUT}/bazowurx_outline.png', optimize=True); print('bazowurx', im.size)

if __name__ == '__main__':
    bazowurx(); supercross('white', 'supercross_sgm_white.png')
    s = supercross(); m = mxshopmoto()
    sheet = Image.new('RGBA', (s.width + m.width * s.height // m.height + 40, s.height), (60, 60, 64, 255))
    sheet.alpha_composite(s, (0, 0)); mm = m.resize((m.width * s.height // m.height, s.height)); sheet.alpha_composite(mm, (s.width + 40, 0))
    sheet.convert('RGB').resize((sheet.width // 3, sheet.height // 3)).save(os.path.join(os.path.dirname(ROOT), 'apercus_sgm', 'logos_v30.png'))
