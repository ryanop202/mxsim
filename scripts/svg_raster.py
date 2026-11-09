"""Tiny SVG path rasterizer (M L H V C S Q Z, absolute and relative), even-odd fill, for single-colour logos given as SVG
(v35: the Fly Racing logo the user sent). Only the paths whose class has a visible fill are drawn."""
import re, numpy as np
from PIL import Image, ImageDraw

def _paths(svg):
    styles = dict(re.findall(r'\.(\w+)\{fill:([^;}]+)', svg))
    out = []
    for cls, d in re.findall(r'<path class="(\w+)" d="([^"]+)"', svg, re.S):
        if styles.get(cls, '#000') != 'none': out.append(d)
    return out

def _subpaths(d, steps=12):
    toks = re.findall(r'[MmLlHhVvCcSsQqZz]|-?(?:\d+\.?\d*|\.\d+)(?:e-?\d+)?', d)
    i, cmd, cur, start, last_c, subs, pts = 0, None, np.zeros(2), np.zeros(2), None, [], []
    def num():
        nonlocal i; v = float(toks[i]); i += 1; return v
    while i < len(toks):
        if re.match(r'[A-Za-z]', toks[i]): cmd = toks[i]; i += 1
        rel = cmd.islower(); C = cmd.upper(); base = cur.copy() if rel else np.zeros(2)
        if C == 'Z':
            if pts: subs.append(pts); pts = []
            cur = start.copy(); last_c = None; continue
        if C == 'M':
            p = base + [num(), num()]
            if pts: subs.append(pts)
            pts = [p]; cur = start = p; cmd = 'l' if rel else 'L'; last_c = None
        elif C == 'L': cur = base + [num(), num()]; pts.append(cur); last_c = None
        elif C == 'H': cur = np.array([(cur[0] if rel else 0) + num(), cur[1]]); pts.append(cur); last_c = None
        elif C == 'V': cur = np.array([cur[0], (cur[1] if rel else 0) + num()]); pts.append(cur); last_c = None
        elif C in 'CS':
            if C == 'C': c1 = base + [num(), num()]
            else: c1 = 2 * cur - last_c if last_c is not None else cur.copy()
            c2 = base + [num(), num()]; e = base + [num(), num()]
            for t in np.linspace(0, 1, steps)[1:]:
                pts.append((1 - t) ** 3 * cur + 3 * (1 - t) ** 2 * t * c1 + 3 * (1 - t) * t ** 2 * c2 + t ** 3 * e)
            last_c = c2; cur = e
        elif C == 'Q':
            c1 = base + [num(), num()]; e = base + [num(), num()]
            for t in np.linspace(0, 1, steps)[1:]: pts.append((1 - t) ** 2 * cur + 2 * (1 - t) * t * c1 + t ** 2 * e)
            last_c = None; cur = e
    if pts: subs.append(pts)
    return subs

def rasterize(svg_path, width_px, pad=0.02):
    """RGBA white logo on transparent, `width_px` wide, cropped to the ink + pad."""
    svg = open(svg_path, encoding='utf-8').read()
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', svg).group(1).split()]
    ss = 4; s = width_px * ss / vb[2]; W, H = int(vb[2] * s), int(vb[3] * s)
    mask = np.zeros((H, W), bool)
    for d in _paths(svg):
        for sp in _subpaths(d):
            im = Image.new('1', (W, H), 0); ImageDraw.Draw(im).polygon([((x - vb[0]) * s, (y - vb[1]) * s) for x, y in sp], fill=1)
            mask ^= np.array(im)                                     # even-odd
    ys, xs = np.nonzero(mask); p = int(pad * W)
    mask = mask[max(0, ys.min() - p):ys.max() + p + 1, max(0, xs.min() - p):xs.max() + p + 1]
    a = Image.fromarray((mask * 255).astype(np.uint8)).resize((mask.shape[1] // ss, mask.shape[0] // ss), Image.LANCZOS)
    out = Image.new('RGBA', a.size, (255, 255, 255, 0)); out.putalpha(a); return out

if __name__ == '__main__':
    import sys; rasterize(sys.argv[1], int(sys.argv[3])).save(sys.argv[2])
