"""v62d (user: "exactly this style", the PRECISION KARTING main logo): BAZO in a heavy, wide, italic face with a chrome
(silver gradient) fill, a black outline and a blue outer rim; WURX under it on the right in a thin, wide, spaced italic,
with the slanted wedge + base line running out to the left. Transparent background.
usage: python scripts/logo_bazo.py <out.png>"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

HEAVY = 'C:/Windows/Fonts/ariblk.ttf'
THIN = 'C:/Windows/Fonts/segoeuisl.ttf'
BLUE = np.array([42, 93, 176.0]); DARK = np.array([22, 22, 24.0])
K = 0.26                                           # italic slant


def mask_text(txt, font, size, sx=1.0, spacing=0):
    """alpha mask (float 0..1) of the text, stretched sx in width, letters spaced `spacing` px, slanted K."""
    f = ImageFont.truetype(font, size); d0 = ImageDraw.Draw(Image.new('L', (1, 1)))
    ws = [d0.textbbox((0, 0), c, font=f) for c in txt]; asc, desc = f.getmetrics()
    W = sum(b[2] - b[0] for b in ws) + spacing * (len(txt) - 1) + 20; H = asc + desc + 20
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im); x = 10
    for c, b in zip(txt, ws):
        d.text((x - b[0], 10), c, font=f, fill=255); x += b[2] - b[0] + spacing
    im = im.crop(im.getbbox()); im = im.resize((int(im.width * sx), im.height), Image.LANCZOS)
    w, h = im.size; dx = int(round(K * h)); pad = 4
    im = im.transform((w + dx + 2 * pad, h + 2 * pad), Image.AFFINE, (1, K, -dx - pad + K * pad, 0, 1, -pad), Image.BICUBIC)
    return np.asarray(im, float) / 255


def chrome(h, w, y0, y1):
    """silver gradient over rows y0..y1 (light top, darker break under the middle, lighter again at the bottom)."""
    t = np.clip((np.arange(h)[:, None] - y0) / max(1, y1 - y0), 0, 1)
    v = np.where(t < 0.48, 246 - 40 * t / 0.48, np.where(t < 0.56, 168 + 0 * t, 172 + 52 * (t - 0.56) / 0.44))
    return np.repeat(np.dstack([v, v, v * 1.02])[:, :, :], 1, axis=1) * np.ones((1, w, 1))


def dil(a, r):
    return np.clip(r + 0.5 - ndi.distance_transform_edt(a < 0.5), 0, 1)


def logo():
    big = mask_text('BAZO', HEAVY, 420, sx=1.18)
    thin = mask_text('WURX', THIN, 150, sx=1.45, spacing=40)
    Hc, Wc = 900, 2600; A = np.zeros((Hc, Wc))                 # letters (chrome)
    bx, by = 140, 60; A[by:by + big.shape[0], bx:bx + big.shape[1]] = np.maximum(A[by:by + big.shape[0], bx:bx + big.shape[1]], big)
    tx = bx + big.shape[1] - thin.shape[1] - 20; ty = by + big.shape[0] + 34
    T = np.zeros((Hc, Wc)); T[ty:ty + thin.shape[0], tx:tx + thin.shape[1]] = thin
    # wedge + base line under / left of WURX (like the K of KARTING)
    wedge = Image.new('L', (Wc, Hc), 0); dw = ImageDraw.Draw(wedge)
    yb = ty + thin.shape[0] - 6; hgt = thin.shape[0] * 0.55
    xr = tx + 18; xl = bx + 520
    dw.polygon([(xl, yb), (xr, yb), (xr + K * hgt, yb - hgt), (xr - 60 + K * hgt, yb - hgt)], fill=255)
    dw.rectangle((xl - 260, yb - 3, tx + thin.shape[1] + 10, yb + 3), fill=255)                     # base line
    Wg = np.asarray(wedge, float) / 255
    allm = np.maximum(np.maximum(A, T), Wg)
    rim = dil(allm, 20); dark = dil(allm, 12)
    img = np.zeros((Hc, Wc, 4))
    img[..., :3] = BLUE; img[..., 3] = rim
    img[..., :3] = img[..., :3] * (1 - dark[..., None]) + DARK * dark[..., None]; img[..., 3] = np.maximum(img[..., 3], dark)
    C = chrome(Hc, Wc, by + 10, by + big.shape[0] - 10)
    img[..., :3] = img[..., :3] * (1 - A[..., None]) + C * A[..., None]
    Ct = chrome(Hc, Wc, ty, ty + thin.shape[0]); W2 = np.maximum(T, Wg)
    img[..., :3] = img[..., :3] * (1 - W2[..., None]) + Ct * W2[..., None]
    img[..., 3] = np.clip(img[..., 3], 0, 1)
    out = Image.fromarray(np.clip(np.dstack([img[..., :3], img[..., 3:] * 255]), 0, 255).astype(np.uint8), 'RGBA')
    bb = out.getbbox(); return out.crop((bb[0] - 6, bb[1] - 6, bb[2] + 6, bb[3] + 6))


def style_user(src, scale=3.0):
    """v62e (user sent the BAZOWURX logo): his black-on-grey drawing -> the same chrome style (silver gradient fill, black
    outline, blue rim), transparent background."""
    g = np.asarray(Image.open(src).convert('L'), float); m = np.clip((170 - g) / 110, 0, 1)
    ys, xs = np.where(m > 0.5); m = m[ys.min() - 4:ys.max() + 5, xs.min() - 4:xs.max() + 5]
    mi = Image.fromarray((m * 255).astype(np.uint8)); mi = mi.resize((int(mi.width * scale), int(mi.height * scale)), Image.LANCZOS)
    pad = 40; A = np.pad(np.asarray(mi, float) / 255, pad); Hc, Wc = A.shape
    rim = dil(A, 22); dark = dil(A, 13)
    img = np.zeros((Hc, Wc, 4)); img[..., :3] = BLUE; img[..., 3] = rim
    img[..., :3] = img[..., :3] * (1 - dark[..., None]) + DARK * dark[..., None]; img[..., 3] = np.maximum(img[..., 3], dark)
    ys, _ = np.where(A > 0.5); C = chrome(Hc, Wc, ys.min(), ys.max())
    img[..., :3] = img[..., :3] * (1 - A[..., None]) + C * A[..., None]
    out = Image.fromarray(np.clip(np.dstack([img[..., :3], np.clip(img[..., 3:], 0, 1) * 255]), 0, 255).astype(np.uint8), 'RGBA')
    bb = out.getbbox(); return out.crop((bb[0] - 4, bb[1] - 4, bb[2] + 4, bb[3] + 4))


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'assets/map/bazo_wurx.png'
    lg = style_user(sys.argv[2]) if len(sys.argv) > 2 else logo(); lg.save(out); print('logo', lg.size, out)
