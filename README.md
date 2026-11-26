# LK-04 Metode Numerik — Estimasi Luas Wilayah dan Ekstraksi Tepi Citra Digital

Mata kuliah **Metode Numerik (CIF63309)** — Teknik Informatika, Universitas Brawijaya, Semester Ganjil 2026/2027.

Proyek ini menghitung **luas objek geografis** dari citra hasil segmentasi dengan **integral numerik
(Simpson 1/3, Simpson 3/8, dan gabungan)**, serta **mengekstrak tepi citra** dengan **diferensial numerik
(Central Difference)**, lalu menganalisis galat pangkasnya.

## Anggota & pembagian tugas

| Anggota | Fokus | Berkas |
|---|---|---|
| Naufal Mufli Jamal - 255150201111038 | Diferensial + visualisasi | `diferensial.py` |
| Phaksi Giring Pamungkas - 255150207111034 | Integral + kode utama + repo | `integral.py`, `main.py`, `README.md` |
| Naufal Mohammad Adhi - 255150207111018 | Analisis galat + laporan | `analisis_galat.py` |

## Struktur repositori

```
.
├── main.py              # titik masuk program
├── integral.py          # Simpson 1/3, 3/8, gabungan, perhitungan luas
├── diferensial.py       # Central Difference, magnitudo, peta tepi   
├── analisis_galat.py    # galat absolut/relatif/pangkas, uji variasi h 
├── data_sampel.py       # data sintetis & pemuat citra -> mask
├── data/                # taruh citra segmentasi di sini
├── hasil/               # keluaran: grafik & JSON (dibuat otomatis)
├── tests/test_integral.py
├── docs/bab_integral.md # draf Bab Integral untuk laporan
└── requirements.txt
```

## Cara menjalankan

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python main.py                                   # data sintetis (danau tidak beraturan)
python main.py --bentuk elips                    # elips: luas analitik = pi*a*b
python main.py --citra data/segmentasi.png --resolusi 10 --step 2
```

| Opsi | Keterangan |
|---|---|
| `--citra` | Path citra segmentasi; objek diambil lewat thresholding |
| `--ambang` | Ambang threshold 0–255 (default 128) |
| `--resolusi` | Sisi 1 piksel dalam meter (default 1.0) |
| `--step` | Ambil tiap `step` kolom → `h = step × resolusi` |
| `--bentuk` | `elips` / `danau` bila `--citra` tidak diberikan |

Uji unit: `python -m unittest discover tests -v`

## Kontrak antarmodul 
`main.py` memanggil modul lain:

```python
diferensial.jalankan(mask, folder_hasil)       
analisis_galat.jalankan(mask, folder_hasil)    
```

- `mask`: array 2D boolean (`True` = objek). Jika Anggota 1 butuh citra grayscale, muat sendiri di dalam `jalankan`.
- Anggota 3 dapat memakai langsung: `from integral import hitung_luas, luas_referensi`
  - `hitung_luas(mask, metode, step, ukuran_piksel)` dengan `metode` ∈ `{"simpson_1_3","simpson_3_8","gabungan"}`
  - `luas_referensi(mask, ukuran_piksel)` = jumlah piksel × luas piksel
- Variasi `h` untuk uji galat: ubah `step` (1, 2, 3, 4, 5, 6, ...).

## Metode singkat

Luas objek = ∫ w(x) dx, dengan w(x) = lebar vertikal objek (jumlah piksel objek) pada kolom x.
- **Simpson 1/3**: `I = h/3 [y0 + 4Σ(ganjil) + 2Σ(genap) + yn]`, syarat n genap.
- **Simpson 3/8**: `I = 3h/8 [y0 + 3Σ(bukan kelipatan 3) + 2Σ(kelipatan 3) + yn]`, syarat n kelipatan 3.
- **Gabungan**: n genap → 1/3; n ganjil → 3/8 pada 3 subinterval pertama + 1/3 untuk sisanya.

## Referensi
- Chapra, *Applied Numerical Methods with MATLAB for Engineers and Scientists*, McGraw-Hill, 2012.
- Rinaldi Munir, *Metode Numerik* edisi 5, Informatika, 2021.
