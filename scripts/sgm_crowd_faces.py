"""Saint-Georges (user idea): Mr Beast's face on every face of the crowd sprites - only the inside of the face (brows, both
eyes, nose, moustache, mouth, beard), no hair. Three source photos used in turn (the Saint-Thibery VIP cut-out + 2 portraits
the user sent, assets/crowd/beast_face2.png / beast_face3.png).
v31c (user: "applique-toi, chaque personne"): every person's face measured on zoomed crops of the 256 px sprites: eye line,
chin, middle between the eyes, half width, head tilt, where he / she looks. Mr Beast's face is then fitted on those points
with an affine map (his eye line on the eye line, his beard bottom on the chin, his cheek width on the face width: the
face is stretched or narrowed per person, turned with the head, mirrored when the person looks the other way), its skin
tone pulled towards the person's and its edge faded into the person's face.
Run: python scripts/sgm_crowd_faces.py [--mockup]   -> assets/crowd/beast/crowd_<name>.png (+ ../apercus_sgm/crowd_beast_*.png)"""
import os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as nd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = f'{ROOT}/assets/crowd/beast/orig'   # the untouched crowd sprites (as the export crops them)
OUT = f'{ROOT}/assets/crowd/beast'
# source faces: file, eye line y, middle between the eyes x, beard bottom y, cheek half width, face oval (centre, rx, ry) =
# what is kept (forehead under the hair -> beard, cheek to cheek), where he looks (0 front, 1 to the right of the picture)
FACES = [dict(f='vip_mrbeast.png', eye=127, cx=290, chin=272, hw=58, oval=((291, 178), 66, 104), look=0),
         dict(f='beast_face2.png', eye=238, cx=602, chin=515, hw=140, oval=((588, 345), 152, 200), look=1),
         dict(f='beast_face3.png', eye=245, cx=507, chin=480, hw=122, oval=((513, 330), 130, 172), look=1)]
# people: sprite, eye line y, middle x, chin y, half width, tilt (deg, + = counter-clockwise), look (-1 left, 0, 1 right)
PEOPLE = [('Crowd1', 32, 49, 52, 12.0, 0, 0), ('Crowd1', 17, 169, 32, 9.0, -10, 1),
          ('Crowd2', 44, 20, 58, 8.0, 12, -1), ('Crowd2', 50, 185, 67, 12.5, 0, 0),
          ('Crowd3', 75, 41, 92, 11.0, 0, 0), ('Crowd3', 54, 187, 73, 13.0, 0, -1),
          ('Crowd4', 35, 35, 54, 12.5, 0, 0), ('Crowd4', 20, 208, 40, 10.0, 0, 0),
          ('Crowd5', 38, 68, 53, 12.0, 0, 0), ('Crowd5', 24, 213, 42, 12.5, 0, -1),
          ('Crowd6', 36, 55, 51, 13.0, -4, 1), ('Crowd6', 25, 206, 40, 9.5, 0, 0),
          ('Crowd8', 25, 187, 55, 37.0, 8, 1),
          ('Crowd9', 30, 52, 48, 11.5, 8, -1), ('Crowd9', 25, 215, 42, 10.5, 0, 0)]
SS = 4                         # supersampling of the sprite while pasting
TONE = 0.45                    # how much of the skin tone difference is removed
FADE = 0.16                    # width of the faded edge (fraction of the oval)

def src_image(F):
    im = Image.open(f"{ROOT}/assets/crowd/{F['f']}").convert('RGBA'); a = np.asarray(im).astype(float)
    (ox, oy), rx, ry = F['oval']; H, W = a.shape[:2]; yy, xx = np.mgrid[:H, :W]
    d = np.sqrt(((xx - ox) / rx) ** 2 + ((yy - oy) / ry) ** 2)
    m = np.clip((1 - d) / FADE, 0, 1) ** 1.2                                  # soft oval: 1 inside, fades to 0 at the edge
    a[..., 3] = a[..., 3] * m
    skin = (m > 0.6) & (a[..., 0] > a[..., 2] + 20)
    tone = a[..., :3][skin].mean(0)
    a[..., :3] *= a[..., 3:4] / 255.0                                         # premultiplied (no bright ring when resampled)
    return a, tone

def build():
    os.makedirs(OUT, exist_ok=True); srcs = [src_image(F) for F in FACES]; ims = {}
    for i, (nm, ey, cx, ch, hw, tilt, look) in enumerate(PEOPLE):
        if nm not in ims: ims[nm] = Image.open(f'{SRC}/crowd_{nm}.png').convert('RGBA')
        k = i % len(FACES); F = FACES[k]; a, tone = srcs[k]
        flip = look != 0 and look != F['look']
        sx = hw / F['hw']; sy = (ch - ey) / (F['chin'] - F['eye'])            # source px -> sprite px (per axis)
        th = np.radians(tilt); c, s = np.cos(th), np.sin(th)
        base = np.asarray(ims[nm]).astype(float); H, W = base.shape[:2]
        ys, xs = np.mgrid[0:H * SS, 0:W * SS] / SS + 0.5 / SS                  # target pixel grid -> source coordinates
        dx, dy = xs - cx, ys - ey
        u = c * dx - s * dy; v = s * dx + c * dy                                 # undo the head tilt (image y down)
        if flip: u = -u
        X = F['cx'] + u / sx; Y = F['eye'] + v / sy
        ok = (X >= 0) & (X < a.shape[1] - 1) & (Y >= 0) & (Y < a.shape[0] - 1)
        pat = np.zeros((H * SS, W * SS, 4))
        for ch_ in range(4):
            pat[..., ch_][ok] = nd.map_coordinates(a[..., ch_], [Y[ok], X[ok]], order=1)
        pat = pat.reshape(H, SS, W, SS, 4).mean(axis=(1, 3))                   # back to the sprite resolution
        al = pat[..., 3:4] / 255.0
        ring = (al[..., 0] > 0.02) & (al[..., 0] < 0.9) & (base[..., 3] > 200) & (base[..., 0] > base[..., 2] + 10)
        tgt = base[..., :3][ring].mean(0) if ring.sum() > 6 else tone          # the person's skin round the face
        col = pat[..., :3] / np.maximum(al, 1e-3) + TONE * (tgt - tone)[None, None, :]   # un-premultiply
        out = base.copy(); out[..., :3] = base[..., :3] * (1 - al) + np.clip(col, 0, 255) * al
        ims[nm] = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), 'RGBA')
    for nm, im in ims.items(): im.save(f'{OUT}/crowd_{nm}.png')
    print('beast faces on', len(PEOPLE), 'people,', len(ims), 'sprites'); return ims

def mockup(out):
    names = sorted(out); W = 256
    sheet = Image.new('RGB', (W * 4 * 2, W * 2 * 2 + 520), (60, 62, 66))
    for i, nm in enumerate(names):
        bg = Image.new('RGBA', (W, W), (60, 62, 66, 255)); bg.alpha_composite(out[nm])
        sheet.paste(bg.convert('RGB').resize((W * 2, W * 2), Image.LANCZOS), ((i % 4) * W * 2, (i // 4) * W * 2))
    rg = np.random.default_rng(3); strip = Image.new('RGBA', (W * 8, 520), (24, 26, 32, 255))
    for row in range(6):
        for k in range(26):
            nm = names[int(rg.integers(len(names)))]; s = int(150 + row * 18)
            sp = out[nm].resize((s, s), Image.LANCZOS); strip.alpha_composite(sp, (int(k * 80 + rg.uniform(-20, 20) - 40), int(row * 55 - 20)))
    sheet.paste(strip.convert('RGB'), (0, W * 4))
    cl = Image.new('RGB', (len(PEOPLE) * 150, 300), (60, 62, 66))           # every face, before (top) / after (bottom)
    for i, (nm, ey, cx, ch, hw, _, _) in enumerate(PEOPLE):
        r_ = hw * 1.6; box = (int(cx - r_), int(ey - r_ * 1.0), int(cx + r_), int(ey + r_ * 1.2))
        for row, im in enumerate((Image.open(f'{SRC}/crowd_{nm}.png').convert('RGBA'), out[nm])):
            c = im.crop(box); bg = Image.new('RGBA', c.size, (60, 62, 66, 255)); bg.alpha_composite(c)
            cl.paste(bg.convert('RGB').resize((150, 150), Image.LANCZOS), (i * 150, row * 150))
    d = os.path.join(os.path.dirname(ROOT), 'apercus_sgm'); os.makedirs(d, exist_ok=True)
    sheet.save(f'{d}/crowd_beast_mockup.png'); cl.save(f'{d}/crowd_beast_faces.png')

if __name__ == '__main__':
    o = build()
    if '--mockup' in sys.argv: mockup(o)
