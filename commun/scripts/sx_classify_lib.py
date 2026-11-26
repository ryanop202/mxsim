import numpy as np
from scipy import ndimage as ndi
def rot_patch(P, s, ang, step=0.1):
    h,w=P.shape; cy,cx=(h-1)/2,(w-1)/2
    R=np.hypot(h,w)*s/2
    u=np.arange(-R,R,step); U,V=np.meshgrid(u,u,indexing='xy')
    ca,sa=np.cos(ang),np.sin(ang)
    X=U*ca-V*sa; Z=U*sa+V*ca
    return u, ndi.map_coordinates(P,[Z/s+cy,X/s+cx],order=1,cval=0)
