"""Register the user's Google satellite views onto the drone photo (which is already registered to the layout:
drone px = (212 + 1.63 x, 428 + 1.63 z), local ft). Similarity search (rotation, scale) + FFT translation on bare-dirt and
tree masks. Usage: python register_sat.py <sat.webp> -> prints the 2x3 matrix sat px -> local ft, saves an overlay."""
import sys, json, numpy as np
from PIL import Image
from scipy import ndimage as ndi

DRONE = '../../mxsim/assets/sgm/vue_aerienne.jpg'

def masks(a):
    a = a.astype(float); R, G, B = a[..., 0], a[..., 1], a[..., 2]; L = a.mean(2)
    dirt = (R > G) & (G > B) & (R - B > 35) & (L > 90)
    tree = (G >= R - 5) & (G > B) & (L < 95) & (L > 15)
    return ndi.binary_opening(dirt, iterations=1).astype(float), ndi.binary_opening(tree, iterations=1).astype(float)

def warp(m, A, shape):
    """A: 2x3 maps OUTPUT (drone) px -> INPUT (sat) px."""
    return ndi.affine_transform(m, A[:, :2][::-1, ::-1], offset=A[:, 2][::-1], output_shape=shape, order=1, cval=0.0)

def main(sat_path, crop_bottom=0):
    D = np.asarray(Image.open(DRONE).convert('RGB'))[:1450]           # drop the phone UI at the bottom
    S_ = np.asarray(Image.open(sat_path).convert('RGB'))
    if crop_bottom: S_ = S_[:-crop_bottom]
    k = 3; Dd, Dt = [m[::k, ::k] for m in masks(D)]; Sd, St = masks(S_)
    H, W = Dd.shape; PH, PW = H * 2, W * 2                           # padded canvas (the sat view is wider than the drone one)
    Fd = np.fft.rfft2(np.pad(Dd, ((0, PH - H), (0, PW - W)))); Ft = np.fft.rfft2(np.pad(Dt, ((0, PH - H), (0, PW - W))))
    best = None
    def score(th, sc):
        c, s = np.cos(th), np.sin(th)
        # canvas px (in drone/k units, centred at canvas centre) -> sat px: rotate, scale
        M = np.array([[c, -s], [s, c]]) * (k / sc)
        cy, cx = PH / 2, PW / 2; sy, sx = S_.shape[0] / 2, S_.shape[1] / 2
        A = np.zeros((2, 3)); A[:, :2] = M; A[:, 2] = np.array([sx, sy]) - M @ np.array([cx, cy])
        wd = warp(Sd, A, (PH, PW)); wt = warp(St, A, (PH, PW))
        cd = np.fft.irfft2(np.fft.rfft2(wd).conj() * Fd, s=(PH, PW)); ct = np.fft.irfft2(np.fft.rfft2(wt).conj() * Ft, s=(PH, PW))
        cc = cd / (wd.sum() ** 0.5 * Dd.sum() ** 0.5 + 1e-9) + 0.7 * ct / (wt.sum() ** 0.5 * Dt.sum() ** 0.5 + 1e-9)
        i = int(np.argmax(cc)); dy, dx = np.unravel_index(i, cc.shape)
        return cc.flat[i], dy, dx, A
    for th in np.radians(np.arange(-80, 81, 3)):
        for sc in np.arange(1.0, 3.2, 0.1):
            v = score(th, sc)
            if best is None or v[0] > best[0]: best = (v[0], th, sc) + v[1:]
    v0, th0, sc0 = best[:3]
    for th in th0 + np.radians(np.arange(-3, 3.1, 0.5)):
        for sc in sc0 + np.arange(-0.12, 0.121, 0.02):
            v = score(th, sc)
            if v[0] > best[0]: best = (v[0], th, sc) + v[1:]
    v0, th, sc, dy, dx, A = best
    # drone px (full res) -> sat px: canvas q = drone/k shifted by (dy, dx) (circular): drone/k = q + (dy, dx) -> q = drone/k - (dy,dx)
    dy = dy - PH if dy > PH / 2 else dy; dx = dx - PW if dx > PW / 2 else dx
    Ad = np.zeros((2, 3)); Ad[:, :2] = A[:, :2] / k; Ad[:, 2] = A[:, 2] - A[:, :2] @ np.array([dx, dy])
    # local (x, z) -> drone px -> sat px; invert for sat -> local
    Ld = np.array([[1.63, 0, 212.0], [0, 1.63, 428.0]])
    M3 = np.vstack([Ad, [0, 0, 1]]) @ np.vstack([Ld, [0, 0, 1]])     # local -> sat px
    inv = np.linalg.inv(M3)[:2]                                       # sat px -> local ft
    print('score %.3f rot %.1f deg scale %.2f drone px / sat px' % (v0, np.degrees(th), sc))
    # overlay: the sat image warped into the drone frame, blended
    Dfull = np.asarray(Image.open(DRONE).convert('RGB'))[:1450].astype(float)
    Af = np.zeros((2, 3)); Af[:, :2] = Ad[:, :2]; Af[:, 2] = Ad[:, 2]
    ws = np.dstack([ndi.affine_transform(S_[..., ch].astype(float), Af[:, :2][::-1, ::-1], offset=Af[:, 2][::-1], output_shape=Dfull.shape[:2], order=1) for ch in range(3)])
    Image.fromarray((0.5 * Dfull + 0.5 * ws).astype(np.uint8)).save(sat_path.rsplit('/', 1)[-1].split('.')[0] + '_overlay.png')
    return inv

if __name__ == '__main__':
    inv = main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 0)
    json.dump(inv.tolist(), open(sys.argv[3] if len(sys.argv) > 3 else 'sat_to_local.json', 'w'))
    print(json.dumps(inv.round(4).tolist()))
