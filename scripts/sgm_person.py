"""Saint-Georges v30 (user): the person of the user's stage photo (assets/sgm/user/person_src.png) cut out of the dark stage
background, for a billboard on top of the freestyle landing that only shows up on the last lap (nofrills.js, night export).
Cut-out: random walker segmentation on the crop around the person (seeds: the dark navy background, the light stage floor
and its shadow = background; shirt / skin / pants / gold shoes / head core / microphone = person), soft edge from the
probability, small holes filled, then cropped to the person and saved as an RGBA billboard texture.
Run: python scripts/sgm_person.py  -> assets/sgm/person.png (+ ../apercus_sgm/person_cutout.png)"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd
from skimage.segmentation import random_walker
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOX = (380, 140, 860, 962)            # crop of the source photo around the person (x0, y0, x1, y1)
FLOOR_Y = 703                         # crop row where the stage floor starts (the shoes / lower legs go below it)

def cutout():
    src = Image.open(f'{ROOT}/assets/sgm/user/person_src.png').convert('RGB').crop(BOX)
    a = np.asarray(src).astype(float); R, G, B = a[..., 0], a[..., 1], a[..., 2]; L = a.mean(2)
    h, w = L.shape; yy, xx = np.mgrid[:h, :w]
    gold = (R > 110) & (R - B > 35) & (yy > 600)
    floor = (yy > FLOOR_Y)
    lab = np.zeros((h, w), np.int32)
    # background seeds
    lab[(L < 16) & (B - R > 5)] = 1
    lab[:, :4] = 1; lab[:, -4:] = 1; lab[:4, :] = 1
    lab[floor & ~gold & (L > 92) & (np.abs(R - B) < 28)] = 1                     # light grey floor
    lab[floor & ~gold & (xx < 150) & (yy > 735)] = 1                               # the shadow on the floor, left
    lab[(yy > 790) & ~gold] = 1                                                     # the bright floor edge at the bottom
    # person seeds
    fg = np.zeros((h, w), bool)
    fg |= (L > 70) & (yy < FLOOR_Y) & (xx > 25) & (xx < 455) & ~((yy > 600) & (xx > 330))
    fg |= gold
    fg |= (G > B - 10) & (L > 40) & (L < 110) & (yy > 380) & (yy < 770) & (xx > 95) & (xx < 285)   # pants
    fg |= ((xx - 152) / 30.0) ** 2 + ((yy - 62) / 34.0) ** 2 < 1                   # head core (dark hair)
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).line([(86, 78), (108, 168)], fill=255, width=9)   # microphone handle
    fg |= np.asarray(m) > 0
    lab[fg] = 2
    feat = np.dstack([a / 255.0, ((R - B) / 255.0 * 2)[..., None]])
    pr = random_walker(feat, lab, beta=180, mode='cg_j', channel_axis=-1, return_full_prob=True)[1]
    alpha = np.clip((pr - 0.35) / 0.3, 0, 1)
    core = nd.binary_fill_holes(alpha > 0.5)
    lb, n = nd.label(core); sz = nd.sum(core, lb, range(1, n + 1)); keep = lb == 1 + int(np.argmax(sz))   # one blob: the person
    alpha = np.where(keep | (nd.binary_dilation(keep, iterations=2) & (alpha > 0)), np.maximum(alpha, core * keep), 0)
    bgcol = (L < 22) & (B - R > 4) & ~fg                                           # clear navy background (between the legs...)
    pantsc = (G > B - 12) & (B > R + 5) & (L > 38) & (L < 125) & (xx > 170) & (xx < 270)   # bluish green (the floor is warm grey)
    from skimage.morphology import remove_small_holes
    alpha = np.where(bgcol & ~remove_small_holes(~bgcol, 600), 0.0, alpha)          # only real gaps (> 600 px), not dark folds
    alpha = np.where(floor & ~(gold | pantsc), 0.0, alpha)                         # nothing of the stage floor under the shoes
    keep2 = nd.binary_opening(alpha > 0.5, iterations=1); lb, n = nd.label(keep2); sz = nd.sum(keep2, lb, range(1, n + 1))
    big = np.isin(lb, 1 + np.nonzero(sz > 300)[0]); alpha = np.where(nd.binary_dilation(big, iterations=2), alpha, 0.0)
    alpha = nd.gaussian_filter(alpha, 0.7)
    rgb = a.copy()
    # despill: the edge pixels carry the navy background; pull them towards the inner colour
    inner = nd.grey_erosion(alpha, size=5) > 0.95
    near = nd.distance_transform_edt(~inner, return_indices=True)[1]
    edge = (alpha > 0.02) & ~inner
    rgb[edge] = rgb[near[0][edge], near[1][edge]] * 0.6 + rgb[edge] * 0.4
    out = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), alpha * 255]).astype(np.uint8), 'RGBA')
    out = out.crop(out.getchannel('A').point(lambda v: 255 if v > 8 else 0).getbbox())
    pad = Image.new('RGBA', (out.width + 8, out.height + 4), (0, 0, 0, 0)); pad.paste(out, (4, 0)); out = pad
    out.save(f'{ROOT}/assets/sgm/person.png'); print('person.png', out.size)
    prev = Image.new('RGBA', (out.width * 2 + 20, out.height), (200, 140, 70, 255)); prev.alpha_composite(out, (0, 0))
    g = Image.new('RGBA', out.size, (40, 120, 60, 255)); g.alpha_composite(out); prev.paste(g, (out.width + 20, 0))
    os.makedirs(os.path.join(os.path.dirname(ROOT), 'apercus_sgm'), exist_ok=True)
    prev.convert('RGB').save(os.path.join(os.path.dirname(ROOT), 'apercus_sgm', 'person_cutout.png'))
    return out

if __name__ == '__main__':
    cutout()
