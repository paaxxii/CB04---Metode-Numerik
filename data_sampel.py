import numpy as np
from PIL import Image

def buat_ellipse(ukuran=200, a=60, b=40):
    yy, xx = np.mgrid[0:ukuran, 0:ukuran]
    c = ukuran / 2.0
    return ((xx - c) / a) ** 2 + ((yy - c) / b) ** 2 <= 1.0

def buat_danau_tidak_beraturan(ukuran=200):
    yy, xx = np.mgrid[0:ukuran, 0:ukuran]
    def el(cx, cy, a, b):
        return ((xx - cx) / a) ** 2 + ((yy - cy) / b) ** 2 <= 1.0
    return el(90, 100, 55, 35) | el(125, 85, 35, 28) | el(70, 125, 30, 22)

def muat_mask_dari_citra(path, ambang=128, objek_gelap=True):
    g = np.asarray(Image.open(path).convert("L"))
    return (g < ambang) if objek_gelap else (g >= ambang)