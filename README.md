# 📊 Risk Scoring Device/CIF Per Region

**(Guardsquare + Wondr Analytics & Dashboard)**

---

## **🔎 Penjelasan Singkat**

Tools ini dibuat untuk:

* **Mendeteksi, memetakan, dan memvisualisasikan risiko device rooting/jailbreak** pada nasabah aplikasi Wondr
* **Join data device pelanggar** (ThreatCast/Guardsquare) dengan data onboarding (CIF, lokasi)
* **Menghitung risk score dinamis** per nasabah (transient, persistent, critical)
* **Mapping risk geospasial** ke wilayah Indonesia
* **Visualisasi interaktif** dengan dashboard web (Streamlit)

---

## **📁 Struktur File**

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

## **⚙️ Cara Penggunaan**

### **1. Persiapan**

* Siapkan file Excel **device pelanggar** dan **data onboarding** (lihat contoh struktur `/data/`)
* Install dependensi:

  ```sh
  pip install -r requirements.txt
  ```

---

### **2. Jalankan Pipeline Analitik**

```sh
python risk_pipeline.py
```

* Output:

  * `hasil_risk_scoring_per_cif_YYYYMMDD_HHMM.xlsx`
  * `risk_heatmap.html`
  * `region_cache.pkl` (cache reverse geocoding otomatis)

---

### **3. Jalankan Dashboard Interaktif**

```sh
streamlit run dashboard.py
```

* Buka browser ke: [http://localhost:8501](http://localhost:8501)
* **Dashboard siap dipakai tim BI, audit, risk, management**
* Fitur: filter cohort, region, risk type; bar chart; trend cohort; heatmap; cluster analysis

---

### **4. Navigasi Dashboard**

* **Risk per Region**: Total risk score per wilayah (bar chart)
* **Trend Cohort**: Tren risk score berdasarkan cohort onboarding nasabah
* **Heatmap**: Sebaran lokasi risk device (onboarding pertama)
* **Cluster Analysis**: Deteksi cluster/hotspot risk (K-Means)
* **Demografi**: Visual segmentasi jika data demografi tersedia

---

### **5. Tips & Troubleshooting**

* **Jika mapping region lama**: Cek koneksi internet, gunakan cache, atau jalankan di batch kecil.
* **Jika file risk scoring hasil pipeline ada timestamp**:
  Pastikan dashboard.py menggunakan file hasil terbaru (`hasil_risk_scoring_per_cif_YYYYMMDD_HHMM.xlsx`)
* **Jika ada kolom baru/hilang**:
  Script pipeline & dashboard otomatis menyesuaikan jika kolom demografi tidak ada.
* **Jika heatmap kosong/cluster error**:
  Cek apakah ada cukup data titik (≥2 lokasi).

---

## **💡 Fitur Lanjutan**

* **Cache geocoding otomatis** (region\_cache.pkl, bisa reuse next run)
* **Ekspor heatmap ke HTML untuk presentasi/audit**
* **Otomatis summary nasabah terdampak dan risk per wilayah**
* **Cocok untuk audit, BI, reporting, compliance risk device**

---

## **🚦 Catatan**

* **Lokasi yang dianalisis = lokasi onboarding pertama device**
  (bukan lokasi login/transaksi harian)
* **Pipeline & dashboard siap di-deploy ke server/cloud internal**
* **Jika ingin fitur baru (alert notifikasi, PDF report, dsb.), tinggal request!**

---

## **Lisensi**

Bebas dipakai untuk kebutuhan internal risk analytics, audit, compliance, dan penguatan fraud detection.

---

> **For any questions, support, or custom development: contact the repo maintainer.**

---
