import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Citra grayscale yang dipakai; dicari berurutan. Bila tidak ada, dipakai mask dari main.py.
KANDIDAT_CITRA = ["coin.jpeg", os.path.join("data", "coin.jpeg")]


# ---------- A. Persiapan data ----------
def baca_citra(path=None):
    """Baca citra, ubah ke grayscale (matriks 2D, nilai 0-255)."""
    if path is None:
        from skimage import data          # hanya dipakai bila path tidak diberikan
        return data.coins().astype(float)
    from PIL import Image
    return np.array(Image.open(path).convert("L"), dtype=float)


# ---------- B. Central Difference ----------
def gradien_x(f, h=1):
    """f'(x) ~ [f(x+h) - f(x-h)] / 2h ; tepi kiri/kanan pakai beda maju/mundur."""
    baris, kolom = f.shape
    gx = np.zeros_like(f)
    for j in range(h, kolom - h):
        gx[:, j] = (f[:, j + h] - f[:, j - h]) / (2 * h)
    for j in range(0, h):
        gx[:, j] = (f[:, j + h] - f[:, j]) / h
    for j in range(kolom - h, kolom):
        gx[:, j] = (f[:, j] - f[:, j - h]) / h
    return gx


def gradien_y(f, h=1):
    """Sama seperti gradien_x, tapi arah vertikal (baris)."""
    return gradien_x(f.T, h).T


def magnitudo(gx, gy):
    return np.sqrt(gx ** 2 + gy ** 2)


def peta_tepi(mag, persen=0.3):
    """Piksel dianggap tepi jika magnitudo > persen * magnitudo maksimum."""
    ambang = persen * mag.max()
    return (mag > ambang).astype(int), ambang


# ---------- Visualisasi ----------
def visualisasi(f, gx, gy, mag, tepi, nama="hasil_diferensial.png"):
    judul = ["Citra Asli", "Gradien X", "Gradien Y", "Magnitudo", "Peta Tepi"]
    gambar = [f, gx, gy, mag, tepi]
    fig, ax = plt.subplots(1, 5, figsize=(20, 4))
    for a, g, j in zip(ax, gambar, judul):
        a.imshow(g, cmap="gray")
        a.set_title(j)
        a.axis("off")
    plt.tight_layout()
    plt.savefig(nama, dpi=150)
    plt.close()


# ---------- Titik masuk (dipanggil main.py) ----------
def jalankan(mask, folder_hasil, path_citra=None, h=1, persen=0.3):
    os.makedirs(folder_hasil, exist_ok=True)
    path_citra = path_citra or next((p for p in KANDIDAT_CITRA if os.path.exists(p)), None)
    if path_citra:
        f = baca_citra(path_citra)
        print(f"[diferensial] citra: {path_citra}")
    else:
        f = np.asarray(mask, dtype=float) * 255.0
        print("[diferensial] coin.jpeg tidak ditemukan -> memakai mask dari main.py")
    print("Ukuran citra:", f.shape)

    gx = gradien_x(f, h)
    gy = gradien_y(f, h)
    mag = magnitudo(gx, gy)
    tepi, ambang = peta_tepi(mag, persen)

    print("Ambang tepi :", round(ambang, 2))
    print("Jumlah piksel tepi:", int(tepi.sum()))
    keluaran = os.path.join(folder_hasil, "hasil_diferensial.png")
    visualisasi(f, gx, gy, mag, tepi, keluaran)
    print("Grafik tersimpan:", keluaran)
    return {"ambang": float(ambang), "piksel_tepi": int(tepi.sum())}


if __name__ == "__main__":
    jalankan(None, "hasil")