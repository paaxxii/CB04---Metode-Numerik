import csv
import json
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from integral import (hitung_luas, luas_referensi, profil_lebar, trapesium,
                      simpson_1_3, simpson_3_8, METODE)

STEPS = [1, 2, 3, 4, 5, 6, 8, 10]
NAMA_METODE = list(METODE) + ["trapesium"]
LABEL = {"simpson_1_3": "Simpson 1/3", "simpson_3_8": "Simpson 3/8",
         "gabungan": "Simpson gabungan", "trapesium": "Trapesium"}


# Utilitas
def _bersih(x):
    """Ubah nilai numpy/NaN agar aman ditulis ke JSON."""
    if isinstance(x, dict):
        return {k: _bersih(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_bersih(v) for v in x]
    if isinstance(x, (np.floating, float)):
        x = float(x)
        return None if np.isnan(x) or np.isinf(x) else x
    if isinstance(x, np.integer):
        return int(x)
    return x


def _kemiringan(h, galat):
    """Kemiringan log-log galat terhadap h (= orde konvergensi empiris)."""
    h, galat = np.asarray(h, float), np.asarray(galat, float)
    ok = galat > 0
    if ok.sum() < 3:
        return float("nan")
    return float(np.polyfit(np.log(h[ok]), np.log(galat[ok]), 1)[0])


def _luas_trapesium(mask, step, ukuran_piksel):
    w = profil_lebar(mask)[::step] * ukuran_piksel
    return float(trapesium(w, step * ukuran_piksel))


# Uji variasi h

def taksir_galat_pangkas(mask, step=1, ukuran_piksel=1.0):
    """
    Batas galat pangkas teoretis komposit:
        Simpson 1/3 : |E| <= (b-a)/180 * h^4 * max|f''''|
        Simpson 3/8 : |E| <= (b-a)/80  * h^4 * max|f''''|
    f'''' ditaksir dari data dengan beda hingga orde 4:  max|diff(w,4)| / h^4
    (karena w(x) berbentuk tangga/piksel, taksiran ini kasar -> batas longgar).
    """
    w = profil_lebar(mask)[::step] * ukuran_piksel
    h = step * ukuran_piksel
    if len(w) < 6:
        return {"f4_maks": float("nan"), "batas_simpson_1_3": float("nan"),
                "batas_simpson_3_8": float("nan")}
    f4 = float(np.abs(np.diff(w, 4)).max() / h ** 4)
    panjang = (len(w) - 1) * h
    return {"f4_maks": f4,
            "batas_simpson_1_3": panjang / 180.0 * h ** 4 * f4,
            "batas_simpson_3_8": panjang / 80.0 * h ** 4 * f4}


def uji_variasi_h(mask, ukuran_piksel=1.0, steps=STEPS):
    """Return (referensi, baris_hasil, daftar_dilewati)."""
    ref = luas_referensi(mask, ukuran_piksel)
    baris, dilewati = [], []
    for s in steps:
        h = s * ukuran_piksel
        batas = taksir_galat_pangkas(mask, s, ukuran_piksel)
        for m in NAMA_METODE:
            try:
                if m == "trapesium":
                    est = _luas_trapesium(mask, s, ukuran_piksel)
                else:
                    est = hitung_luas(mask, m, s, ukuran_piksel)
            except ValueError as e:
                dilewati.append({"step": s, "metode": m, "alasan": str(e)})
                continue
            galat = est - ref
            baris.append({
                "step": s, "h": h, "metode": m, "luas": est,
                "galat_bertanda": galat,
                "galat_absolut": abs(galat),
                "galat_relatif_persen": abs(galat) / ref * 100.0,
                "batas_pangkas_teoretis": batas.get(f"batas_{m}", float("nan")),
            })
    return ref, baris, dilewati


def orde_empiris_citra(baris):
    """Kemiringan log-log galat vs h per metode (data citra, kasar)."""
    hasil = {}
    for m in NAMA_METODE:
        r = [b for b in baris if b["metode"] == m]
        hasil[m] = _kemiringan([b["h"] for b in r], [b["galat_absolut"] for b in r])
    return hasil


# Uji konvergensi

def uji_konvergensi(f, a, b, eksak, ns=(6, 12, 24, 48, 96)):
    """
    Bandingkan trapesium, Simpson 1/3, Simpson 3/8 pada f di [a, b].
    n dipilih kelipatan 6 supaya valid untuk 1/3 (genap) dan 3/8 (kelipatan 3).
    """
    baris = []
    for n in ns:
        x = np.linspace(a, b, n + 1)
        h = (b - a) / n
        y = f(x)
        baris.append({
            "n": n, "h": h,
            "galat_trapesium": abs(trapesium(y, h) - eksak),
            "galat_simpson_1_3": abs(simpson_1_3(y, h) - eksak),
            "galat_simpson_3_8": abs(simpson_3_8(y, h) - eksak),
        })
    for kunci in ("trapesium", "simpson_1_3", "simpson_3_8"):
        for i, r in enumerate(baris):
            if i == 0:
                r[f"orde_{kunci}"] = float("nan")
                continue
            e0, e1 = baris[i - 1][f"galat_{kunci}"], r[f"galat_{kunci}"]
            h0, h1 = baris[i - 1]["h"], r["h"]
            r[f"orde_{kunci}"] = (float(np.log(e0 / e1) / np.log(h0 / h1))
                                  if e0 > 0 and e1 > 0 else float("nan"))
    return baris


def uji_sin():
    """Integral sin(x) di [0, pi] = 2 (fungsi mulus -> orde 2 dan 4 muncul jelas)."""
    return uji_konvergensi(np.sin, 0.0, np.pi, 2.0)


def uji_elips_analitik(a=60.0, b=40.0):
    """
    Luas elips = pi*a*b, dengan w(x) = 2b*sqrt(1-((x-c)/a)^2).
    w(x) mempunyai singularitas akar di tepi -> turunan tak terbatas, sehingga
    orde Simpson turun jauh di bawah 4.
    """
    def w(x):
        return 2.0 * b * np.sqrt(np.clip(1.0 - (x / a) ** 2, 0.0, None))
    return uji_konvergensi(w, -a, a, np.pi * a * b)


# Grafik

def _grafik_galat_vs_h(baris, path):
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for m, mk in zip(NAMA_METODE, ["o", "s", "^", "x"]):
        r = [b for b in baris if b["metode"] == m and b["galat_absolut"] > 0]
        if r:
            ax.loglog([b["h"] for b in r], [b["galat_absolut"] for b in r],
                      marker=mk, lw=1.2, label=LABEL[m])
    ax.set_xlabel("h (m)  [h = step x resolusi]")
    ax.set_ylabel("Galat absolut terhadap luas referensi (m²)")
    ax.set_title("Pengaruh ukuran langkah h terhadap galat")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


def _grafik_galat_metode(baris, path):
    steps = sorted({b["step"] for b in baris})
    lebar = 0.2
    x = np.arange(len(steps))
    fig, ax = plt.subplots(figsize=(9, 4.6))
    for i, m in enumerate(NAMA_METODE):
        nilai = []
        for s in steps:
            r = [b for b in baris if b["step"] == s and b["metode"] == m]
            nilai.append(r[0]["galat_relatif_persen"] if r else np.nan)
        ax.bar(x + (i - 1.5) * lebar, nilai, lebar, label=LABEL[m])
    ax.set_xticks(x); ax.set_xticklabels([f"step {s}" for s in steps])
    ax.set_ylabel("Galat relatif (%)")
    ax.set_title("Perbandingan galat relatif antar metode (kosong = n tidak memenuhi syarat)")
    ax.legend(); ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


def _grafik_batas_teoretis(baris, path):
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for m, wrn in (("simpson_1_3", "C0"), ("simpson_3_8", "C1")):
        r = [b for b in baris if b["metode"] == m and b["galat_absolut"] > 0
             and not np.isnan(b["batas_pangkas_teoretis"])]
        if not r:
            continue
        h = [b["h"] for b in r]
        ax.loglog(h, [b["galat_absolut"] for b in r], "o-", color=wrn,
                  label=f"{LABEL[m]} - galat aktual")
        ax.loglog(h, [b["batas_pangkas_teoretis"] for b in r], "--", color=wrn,
                  label=f"{LABEL[m]} - batas teoretis")
    ax.set_xlabel("h (m)"); ax.set_ylabel("Galat (m²)")
    ax.set_title("Galat aktual vs batas galat pangkas teoretis")
    ax.grid(True, which="both", alpha=0.3); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


def _grafik_konvergensi(sin_baris, elips_baris, path):
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.4))
    for a_, baris, judul in ((ax[0], sin_baris, "Fungsi mulus: ∫₀^π sin x dx = 2"),
                             (ax[1], elips_baris, "Elips analitik: luas = π·a·b")):
        h = np.array([r["h"] for r in baris])
        for kunci, mk in (("trapesium", "x"), ("simpson_1_3", "o"), ("simpson_3_8", "^")):
            e = np.array([r[f"galat_{kunci}"] for r in baris])
            e = np.where(e > 0, e, np.nan)
            a_.loglog(h, e, marker=mk, label=LABEL[kunci])
        # garis acuan kemiringan 2 dan 4
        h0, e0 = h[0], baris[0]["galat_simpson_1_3"] or 1e-3
        for p, gaya in ((2, ":"), (4, "--")):
            a_.loglog(h, e0 * (h / h0) ** p, "k" + gaya, lw=0.8, alpha=0.6,
                      label=f"acuan ~ h^{p}")
        a_.set_title(judul, fontsize=10)
        a_.set_xlabel("h"); a_.set_ylabel("Galat absolut")
        a_.grid(True, which="both", alpha=0.3); a_.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


# Penyimpanan & cetak

def _simpan_csv(baris, path):
    kolom = list(baris[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=kolom)
        w.writeheader()
        for b in baris:
            w.writerow(_bersih(b))


def _cetak_ringkasan(ref, baris, orde_citra, sin_baris, elips_baris, dilewati):
    print(f"\n=== ANALISIS GALAT (luas referensi = {ref:,.2f} m²) ===")
    print(f"{'step':>4} {'h':>5} {'metode':<17}{'luas':>12}{'galat abs':>11}"
          f"{'galat rel %':>13}{'batas teori':>13}")
    for b in baris:
        bt = b["batas_pangkas_teoretis"]
        bt_s = f"{bt:>13.2f}" if not np.isnan(bt) else f"{'-':>13}"
        print(f"{b['step']:>4} {b['h']:>5.1f} {LABEL[b['metode']]:<17}"
              f"{b['luas']:>12,.2f}{b['galat_absolut']:>11.3f}"
              f"{b['galat_relatif_persen']:>13.4f}{bt_s}")
    if dilewati:
        print(f"({len(dilewati)} kombinasi dilewati karena n tidak memenuhi syarat metode)")
    print("\nKemiringan log-log galat vs h (data citra, kasar):")
    for m, p in orde_citra.items():
        print(f"  {LABEL[m]:<17}: {p:.2f}" if not np.isnan(p) else f"  {LABEL[m]:<17}: -")
    for judul, rows in (("sin(x) di [0, pi]", sin_baris), ("elips analitik", elips_baris)):
        print(f"\nOrde konvergensi - {judul}")
        print(f"{'n':>4}{'h':>10}{'e trap':>12}{'e S1/3':>12}{'e S3/8':>12}"
              f"{'p trap':>8}{'p 1/3':>8}{'p 3/8':>8}")
        for r in rows:
            def f(v):
                return f"{v:>8.2f}" if not np.isnan(v) else f"{'-':>8}"
            print(f"{r['n']:>4}{r['h']:>10.5f}{r['galat_trapesium']:>12.3e}"
                  f"{r['galat_simpson_1_3']:>12.3e}{r['galat_simpson_3_8']:>12.3e}"
                  f"{f(r['orde_trapesium'])}{f(r['orde_simpson_1_3'])}{f(r['orde_simpson_3_8'])}")

# Titik masuk 

def jalankan(mask, folder_hasil, ukuran_piksel=1.0):
    os.makedirs(folder_hasil, exist_ok=True)

    ref, baris, dilewati = uji_variasi_h(mask, ukuran_piksel)
    orde_citra = orde_empiris_citra(baris)
    sin_baris = uji_sin()
    elips_baris = uji_elips_analitik()

    _cetak_ringkasan(ref, baris, orde_citra, sin_baris, elips_baris, dilewati)

    _simpan_csv(baris, os.path.join(folder_hasil, "galat_variasi_h.csv"))
    _simpan_csv(sin_baris, os.path.join(folder_hasil, "galat_konvergensi_sin.csv"))
    _simpan_csv(elips_baris, os.path.join(folder_hasil, "galat_konvergensi_elips.csv"))
    with open(os.path.join(folder_hasil, "hasil_analisis_galat.json"), "w", encoding="utf-8") as f:
        json.dump(_bersih({"luas_referensi": ref, "resolusi": ukuran_piksel,
                           "variasi_h": baris, "dilewati": dilewati,
                           "orde_empiris_citra": orde_citra,
                           "konvergensi_sin": sin_baris,
                           "konvergensi_elips": elips_baris}), f, indent=2)

    _grafik_galat_vs_h(baris, os.path.join(folder_hasil, "grafik_galat_vs_h.png"))
    _grafik_galat_metode(baris, os.path.join(folder_hasil, "grafik_galat_metode.png"))
    _grafik_batas_teoretis(baris, os.path.join(folder_hasil, "grafik_batas_teoretis.png"))
    _grafik_konvergensi(sin_baris, elips_baris, os.path.join(folder_hasil, "grafik_konvergensi.png"))
    print(f"\n[analisis_galat] selesai -> {folder_hasil}/")


if __name__ == "__main__":
    from data_sampel import buat_danau_tidak_beraturan
    jalankan(buat_danau_tidak_beraturan(200), "hasil")