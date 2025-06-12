# 📊 Risk Scoring Device/CIF Per Region

**(Guardsquare + Wondr Analytics & Dashboard)**

---

## 🔎 Penjelasan Singkat

Tools ini dibuat untuk:

* **Mendeteksi, memetakan, dan memvisualisasikan risiko device rooting/jailbreak** pada nasabah aplikasi Wondr.
* **Join data device pelanggar** (ThreatCast/Guardsquare) dengan data onboarding (CIF, lokasi).
* **Menghitung risk score dinamis** per nasabah (transient, persistent, critical).
* **Mapping risk geospasial** ke wilayah Indonesia.
* **Visualisasi interaktif** dengan dashboard web (Streamlit).

---

## 📁 Struktur File

```
risk_pipeline.py        # Pipeline analitik risk scoring & mapping wilayah
dashboard.py           # Streamlit dashboard interaktif
requirements.txt       # Daftar dependensi Python
region_cache.pkl       # (otomatis, cache hasil geocoding)
hasil_risk_scoring_per_cif_YYYYMMDD_HHMM.xlsx # Output risk scoring
risk_heatmap.html      # Heatmap geospasial (HTML, buka di browser)
/data/
   |--- Final Data Unique ID - Februari 2025.xlsx   # Data device pelanggar (Guardsquare)
   |--- export_detail.xlsx                          # Data onboarding Wondr (nasabah)
```

---

## ⚙️ Cara Penggunaan

### 1. Persiapan

* Siapkan file Excel **device pelanggar** dan **data onboarding** (lihat contoh struktur `/data/`)
* Install dependensi:

  ```sh
  pip install -r requirements.txt
  ```

---

### 2. Jalankan Pipeline Analitik

```sh
python risk_pipeline.py
```

Output:

* `hasil_risk_scoring_per_cif_YYYYMMDD_HHMM.xlsx`
* `risk_heatmap.html`
* `region_cache.pkl` (cache reverse geocoding otomatis)

---

### 3. Jalankan Dashboard Interaktif

```sh
streamlit run dashboard.py
```

* Buka browser ke: [http://localhost:8501](http://localhost:8501)
* **Dashboard siap dipakai tim BI, audit, risk, management**
* Fitur: filter cohort, region, risk type; bar chart; trend cohort; heatmap; cluster analysis

---

### 4. Navigasi Dashboard

* **Risk per Region:** Total risk score per wilayah (bar chart)
* **Trend Cohort:** Tren risk score berdasarkan cohort onboarding nasabah
* **Heatmap:** Sebaran lokasi risk device (onboarding pertama)
* **Cluster Analysis:** Deteksi cluster/hotspot risk (K-Means)
* **Demografi:** Visual segmentasi jika data demografi tersedia

---

### 5. Tips & Troubleshooting

* Jika mapping region lama: cek koneksi internet, gunakan cache, atau jalankan di batch kecil.
* Jika file risk scoring hasil pipeline ada timestamp:
  Pastikan dashboard.py menggunakan file hasil terbaru (`hasil_risk_scoring_per_cif_YYYYMMDD_HHMM.xlsx`)
* Jika ada kolom baru/hilang:
  Script pipeline & dashboard otomatis menyesuaikan jika kolom demografi tidak ada.
* Jika heatmap kosong/cluster error:
  Cek apakah ada cukup data titik (≥2 lokasi).

---

## 💡 Fitur Lanjutan

* Cache geocoding otomatis (`region_cache.pkl`, bisa reuse next run)
* Ekspor heatmap ke HTML untuk presentasi/audit
* Otomatis summary nasabah terdampak dan risk per wilayah
* Cocok untuk audit, BI, reporting, compliance risk device

---

## 🚦 Catatan

* Lokasi yang dianalisis = lokasi onboarding pertama device (bukan lokasi login/transaksi harian)
* Pipeline & dashboard siap di-deploy ke server/cloud internal
* Jika ingin fitur baru (alert notifikasi, PDF report, dsb.), tinggal request!

---

## 🔄 Alur Kerja Script Risk Scoring Device/CIF Per Region

---

### A. Pipeline Analitik (`risk_pipeline.py`)

1. **Load Data**
   Membaca file DEVICE\_ID pelanggar dari Guardsquare/ThreatCast dan file onboarding nasabah dari Wondr.

2. **Validasi Kolom**
   Memastikan kolom wajib seperti `DEVICE_ID`, `CIF`, `LATITUDE`, `LONGITUDE`, dan `CREATED_TIME` tersedia.

3. **Join Data**
   Join antara device pelanggar dan data onboarding, hanya nasabah nyata yang dianalisis.

4. **Mapping Lokasi (Reverse Geocoding)**
   Koordinat latitude/longitude menjadi nama region/provinsi/kota dengan caching otomatis.

5. **Risk Scoring per CIF**
   Menghitung risk score setiap nasabah (CIF) berdasarkan pola:

   * Transient: 1 device, 1 bulan
   * Persistent: 1 device, >1 bulan
   * Multi-device: >1 device, 1 bulan
   * Critical: >1 device, >1 bulan

6. **Analitik Cohort**
   Tren risk berdasarkan cohort onboarding nasabah.

7. **Visualisasi**
   Bar chart total/rata-rata risk score per region & heatmap geospasial HTML.

8. **Summary Impact**
   Ringkasan jumlah nasabah terdampak, breakdown transient/persistent/critical.

9. **Export Output**
   Simpan hasil ke Excel (timestamped) dan heatmap ke HTML.

10. **Progress Info**
    Selama eksekusi, script menampilkan status dan info summary di console.

---

### B. Dashboard Interaktif (`dashboard.py`)

1. **Load Data Output Pipeline**
   Membaca file Excel hasil scoring pipeline.

2. **Filter & Navigasi**
   Filter cohort, region, risk type, jumlah data hasil filter selalu diinformasikan.

3. **Tab Visualisasi**
   Risk per Region, Trend Cohort, Heatmap, Cluster Analysis, Demografi (jika ada).

4. **Progress Info & Warning**
   Muncul otomatis jika data hasil filter sedikit/tidak cukup untuk visual tertentu.

5. **Keterangan Sidebar**
   Penjelasan workflow, filter, dan batasan tools untuk user.

---

## Diagram Alur Pipeline

```mermaid
flowchart TD
A[Data Device Pelanggar (Guardsquare)]
B[Data Onboarding Nasabah (Wondr)]
C[Join DeviceID & Onboarding]
D[Reverse Geocoding (LatLon ke Region)]
E[Risk Scoring per CIF]
F[Analitik Cohort]
G[Visualisasi & Export (Chart, Heatmap, Excel)]
H[Web Dashboard (Streamlit)]
I[Summary Impact & Progress]

A --> C
B --> C
C --> D
D --> E
E --> F
E --> G
G --> H
E --> I
F --> H
I --> H
```

---

## Inti Alur Kerja

* **Input:** Data device pelanggar & data onboarding
* **Proses:** Join → mapping lokasi → scoring risk → analitik cohort/region
* **Output:** Tabel scoring CIF, heatmap HTML, dashboard web interaktif

---

Tools ini memastikan risk analytic berbasis device & region hanya memakai data yang valid dan siap presentasi ke audit/BI.
Alur ini juga sangat fleksibel—jika data atau model scoring berubah, pipeline bisa langsung diadaptasi.

---
