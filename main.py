import argparse
import importlib
import json
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from integral import hitung_luas, luas_referensi, profil_lebar, METODE
from data_sampel import (buat_danau_tidak_beraturan, buat_ellipse,
                         muat_mask_dari_citra)

FOLDER_HASIL = "hasil"


def muat_data(args):
    if args.citra:
        return muat_mask_dari_citra(args.citra, args.ambang,
                                    objek_gelap=not args.objek_terang), None
    if args.bentuk == "elips":
        return buat_ellipse(200, 60, 40), np.pi * 60 * 40   # luas analitik
    return buat_danau_tidak_beraturan(200), None


def hitung_semua(mask, step, ukuran_piksel):
    ref = luas_referensi(mask, ukuran_piksel)
    baris = []
    for nama in METODE:
        est = hitung_luas(mask, nama, step, ukuran_piksel)
        baris.append({"metode": nama, "luas": est,
                      "galat_absolut": abs(est - ref),
                      "galat_relatif_persen": abs(est - ref) / ref * 100})
    return ref, baris


def buat_grafik(mask, step, ukuran_piksel, path):
    w = profil_lebar(mask)
    x = np.arange(len(w))
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    ax[0].imshow(mask, cmap="gray_r")
    ax[0].set_title("Objek hasil segmentasi (mask)")
    ax[0].set_xlabel("x (piksel)"); ax[0].set_ylabel("y (piksel)")
    ax[1].fill_between(x, w, alpha=0.3, label="Luas = ∫ w(x) dx")
    ax[1].plot(x, w, lw=1.2)
    ax[1].plot(x[::step], w[::step], "ro", ms=3, label=f"Titik sampel (step={step})")
    ax[1].set_title("Profil lebar objek w(x)")
    ax[1].set_xlabel("x (piksel)"); ax[1].set_ylabel("w(x) (piksel)")
    ax[1].legend()
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


def jalankan_modul_teman(nama, mask, step, ukuran_piksel):
    """Panggil <nama>.jalankan(mask, folder_hasil) bila modulnya ada."""
    try:
        modul = importlib.import_module(nama)
    except ModuleNotFoundError:
        print(f"[lewati] {nama}.py belum ada di repositori.")
        return
    print(f"[jalan ] {nama}.jalankan(...)")
    try:
        modul.jalankan(mask, FOLDER_HASIL)
    except Exception as e:
        print(f"[galat ] {nama}.jalankan gagal: {type(e).__name__}: {e}")


def main():
    p = argparse.ArgumentParser(description="LK-04 Metode Numerik")
    p.add_argument("--citra", help="path citra segmentasi (PNG/JPG)")
    p.add_argument("--ambang", type=int, default=128, help="ambang threshold 0-255")
    p.add_argument("--objek-terang", action="store_true",
                   help="objek lebih terang dari latar (default: objek gelap)")
    p.add_argument("--bentuk", choices=["elips", "danau"], default="danau",
                   help="bentuk data sintetis bila --citra tidak diberikan")
    p.add_argument("--resolusi", type=float, default=1.0,
                   help="sisi 1 piksel dalam meter (default 1.0)")
    p.add_argument("--step", type=int, default=1, help="lompatan kolom (h = step*resolusi)")
    args = p.parse_args()

    os.makedirs(FOLDER_HASIL, exist_ok=True)
    mask, analitik = muat_data(args)
    ref, baris = hitung_semua(mask, args.step, args.resolusi)

    print(f"Ukuran citra      : {mask.shape[1]} x {mask.shape[0]} piksel")
    print(f"Resolusi          : {args.resolusi} m/piksel, step = {args.step}")
    print(f"Luas referensi    : {ref:,.2f} m²  (jumlah piksel x luas piksel)")
    if analitik is not None:
        print(f"Luas analitik     : {analitik * args.resolusi**2:,.2f} m²")
    print(f"\n{'Metode':<14}{'Luas (m²)':>14}{'Galat abs':>12}{'Galat rel (%)':>16}")
    for b in baris:
        print(f"{b['metode']:<14}{b['luas']:>14,.2f}{b['galat_absolut']:>12,.2f}"
              f"{b['galat_relatif_persen']:>16.4f}")

    with open(os.path.join(FOLDER_HASIL, "hasil_integral.json"), "w") as f:
        json.dump({"luas_referensi": ref, "luas_analitik": analitik,
                   "resolusi": args.resolusi, "step": args.step,
                   "hasil": baris}, f, indent=2)
    buat_grafik(mask, args.step, args.resolusi,
                os.path.join(FOLDER_HASIL, "grafik_luas_integral.png"))
    print(f"\nHasil disimpan di folder '{FOLDER_HASIL}/'")

    jalankan_modul_teman("diferensial", mask, args.step, args.resolusi)      
    jalankan_modul_teman("analisis_galat", mask, args.step, args.resolusi)   


if __name__ == "__main__":
    main()