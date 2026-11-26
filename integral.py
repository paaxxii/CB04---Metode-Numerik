import numpy as np

# Aturan Simpson
def simpson_1_3(y, h):
    """Simpson 1/3 komposit.
    I = h/3 [ y0 + 4*(y1+y3+...) + 2*(y2+y4+...) + yn ],  n genap.
    """
    y = np.asarray(y, dtype=float)
    n = len(y) - 1                      # jumlah subinterval
    if n < 2 or n % 2 != 0:
        raise ValueError(f"Simpson 1/3 butuh n genap >= 2 (n sekarang = {n}).")
    return h / 3.0 * (y[0] + y[-1]
                      + 4.0 * y[1:-1:2].sum()
                      + 2.0 * y[2:-1:2].sum())


def simpson_3_8(y, h):  
    y = np.asarray(y, dtype=float)
    n = len(y) - 1
    if n < 3 or n % 3 != 0:
        raise ValueError(f"Simpson 3/8 butuh n kelipatan 3 (n sekarang = {n}).")
    idx = np.arange(1, n)
    kelipatan3 = idx % 3 == 0
    return 3.0 * h / 8.0 * (y[0] + y[-1] + 3.0 * y[1:-1][~kelipatan3].sum() + 2.0 * y[1:-1][kelipatan3].sum())


def trapesium(y, h):
    y = np.asarray(y, dtype=float)
    return h * (y[0] / 2.0 + y[1:-1].sum() + y[-1] / 2.0)


def simpson_gabungan(y, h):
    y = np.asarray(y, dtype=float)
    n = len(y) - 1
    if n < 1:
        raise ValueError("Minimal butuh 2 titik data.")
    if n == 1:
        return trapesium(y, h)
    if n % 2 == 0:
        return simpson_1_3(y, h)
    hasil = simpson_3_8(y[:4], h)       # 3 subinterval pertama
    if n > 3:
        hasil += simpson_1_3(y[3:], h)  # sisa n-3 (genap)
    return hasil


METODE = {
    "simpson_1_3": simpson_1_3,
    "simpson_3_8": simpson_3_8,
    "gabungan": simpson_gabungan,
}

# Luas objek dari mask biner
def profil_lebar(mask):
    return np.asarray(mask, dtype=bool).sum(axis=0).astype(float)


def luas_referensi(mask, ukuran_piksel=1.0):
    return float(np.asarray(mask, dtype=bool).sum()) * ukuran_piksel ** 2


def _siapkan_titik(y, metode):
    n = len(y) - 1
    if metode == "simpson_1_3" and n % 2 != 0:
        y = y[:-1]
    elif metode == "simpson_3_8":
        y = y[: n - (n % 3) + 1]
    return y


def hitung_luas(mask, metode="gabungan", step=1, ukuran_piksel=1.0):   
    if metode not in METODE:
        raise ValueError(f"metode harus salah satu dari {list(METODE)}")
    w = profil_lebar(mask)[::step] * ukuran_piksel   # w(x) dalam satuan nyata
    h = step * ukuran_piksel
    w = _siapkan_titik(w, metode)
    return float(METODE[metode](w, h))