"""IGN z19 orthophoto resampled into the track's local frame (x east, z south, ft), 0.5 ft/px over the whole terrain."""
import json, numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates
M = np.array(json.load(open('sat/sat170_to_local.json')) + [[0, 0, 1]]); Mi = np.linalg.inv(M)
R = json.load(open('ign_to_sat170.json')); k, tx, ty = R['k'], R['tx'], R['ty']
X0, Z0, SPAN, RES = -380.0, -330.0, 1187.0, 0.5
n = int(SPAN / RES); xs = X0 + (np.arange(n) + 0.5) * RES; zs = Z0 + (np.arange(n) + 0.5) * RES
GX, GZ = np.meshgrid(xs, zs)
# v27 (user: our track is not 1:1 with the real one): the real track (dirt x -100..95, z -35..370 in this frame) stretched onto
# ours (arena x -32..175, z -32..534) and the surroundings zoomed with it, even if it distorts
RX, OX = (-100.0, 95.0), (-32.0, 175.0); RZ, OZ = (-35.0, 370.0), (-32.0, 534.0)
GX = RX[0] + (GX - OX[0]) * (RX[1] - RX[0]) / (OX[1] - OX[0]); GZ = RZ[0] + (GZ - OZ[0]) * (RZ[1] - RZ[0]) / (OZ[1] - OZ[0])
sp = Mi @ np.stack([GX.ravel(), GZ.ravel(), np.ones(GX.size)])
u, v = (sp[0] + tx) / k, (sp[1] + ty) / k
A = np.asarray(Image.open('ign_z19.jpg').convert('RGB'), float)
out = np.stack([map_coordinates(A[..., c], [v, u], order=1).reshape(n, n) for c in range(3)], -1)
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save('ign_local.png'); print('ign_local', n)
