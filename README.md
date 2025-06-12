# 📊 Risk Scoring Device/CIF Per Region – Guardsquare & Wondr Analytics

---

## **Deskripsi Singkat**

Tools ini bertujuan untuk **mengidentifikasi dan memetakan potensi risiko keamanan aplikasi berbasis device rooting/jailbreak pada nasabah**,
dengan menggabungkan data **ThreatCast Guardsquare** (DEVICE\_ID pelanggar) dan data **onboarding Wondr** (CIF, long/lat, dsb).
**Output utama:**

* Jumlah & distribusi nasabah berisiko (transient, persistent, critical)
* Visualisasi geospasial (heatmap, cluster, cohort)
* Dashboard web-based untuk eksplorasi dan pelaporan

---

## **Alur Kerja Tools (Pipeline)**

1. **Ambil data DEVICE\_ID pelanggar** dari ThreatCast/Guardsquare (Excel).
2. **Ambil data onboarding nasabah** dari Wondr (Excel): DEVICE\_ID, CIF, latitude, longitude, waktu onboarding, dst.
3. **Join/matching DEVICE\_ID** yang terdeteksi pelanggar ke data onboarding (hanya nasabah nyata, bukan seluruh device random).
4. **Reverse geocoding** (mapping long/lat ke region) dengan caching (agar cepat, efisien API).
5. **Risk scoring dinamis** per nasabah (CIF):

   * *Transient risk*: pelanggar 1x, 1 device
   * *Persistent risk*: multi bulan
   * *Multi-device risk*: >1 device
   * *Critical*: persistent + multi-device
6. **Analitik cohort** (analisis tren risk berdasarkan bulan onboarding).
7. **Aggregate risk per region**: total & rata-rata risk score per wilayah/kota.
8. **Export heatmap** risk ke HTML.
9. **Web dashboard (Streamlit)** untuk eksplorasi risk, filter cohort/region/type, cluster, dan segmentasi demografis (jika ada).

---

## **Dependensi**

```
pandas
openpyxl
matplotlib
geopy
tqdm
folium
streamlit
streamlit-folium
scikit-learn
pickle-mixin  # (bawaan Python >=3.8)
```

Install dengan:

```sh
pip install -r requirements.txt
```

---

## **Struktur File**

```
risk_pipeline.py        # Pipeline utama risk scoring & visualisasi
dashboard.py           # Streamlit web dashboard interaktif
requirements.txt       # List dependensi Python
region_cache.pkl       # (otomatis dibuat, cache hasil geocoding)
hasil_risk_scoring_per_cif.xlsx # Output risk scoring per CIF
risk_heatmap.html      # Heatmap geospasial (buka di browser)
/data/
   |--- Final Data Unique ID - Februari 2025.xlsx   # Data device pelanggar (Guardsquare)
   |--- export_detail.xlsx                          # Data onboarding Wondr (nasabah)
```

---

## **Cara Pakai**

### **A. Pipeline Analitik**

1. Siapkan data Excel (lihat folder `/data/`).
2. Jalankan pipeline risk scoring:

   ```
   python risk_pipeline.py
   ```

   * Output: Excel risk scoring, file cache, heatmap.

### **B. Dashboard Web**

1. Jalankan dashboard:

   ```
   streamlit run dashboard.py
   ```
2. Buka browser ke `localhost:8501` untuk interaktif risk analytics.

---

## **Fitur Utama**

* **Risk scoring CIF** (transient, persistent, multi-device, critical)
* **Analitik cohort onboarding**
* **Mapping geospasial (heatmap, cluster)**
* **Dashboard web-based** dengan filter cohort, risk, region
* **Cluster analysis** (hotspot detection)
* **Segmentasi demografis** (jika ada kolom tambahan, misal USIA, GENDER, dsb.)
* **Caching region** (hemat quota API geocoding)
* **Ekspor data & visualisasi** siap untuk audit/presentasi

---

## **Catatan Penting**

* Mapping region via reverse geocoding menggunakan Nominatim (OpenStreetMap); **jika data ribuan baris, proses butuh waktu** (rate limit API ±1/detik, namun cache otomatis tersimpan).
* Untuk mapping batch besar, gunakan region\_cache.pkl sebagai cache persist.
* Data demografi dapat dianalisis otomatis jika ada kolom `USIA`, `JENIS_KELAMIN`, `TIPE_NASABAH`, dll.

---

## **Pengembangan Lanjutan**

* Deploy dashboard ke server internal/cloud untuk multi-user access.
* Tambah alert/notification jika risk melonjak.
* Integrasi ke sistem fraud detection internal.
* Otomasi laporan bulanan/kuartal untuk audit & compliance.
* Kolaborasi dengan tim IT/security untuk data update reguler.

---

## **Lisensi**

Proyek ini dapat digunakan untuk keperluan internal risk/fraud analytic, BI, audit, dan penguatan compliance.

---

> **Untuk pertanyaan, pengembangan lanjutan, atau request template presentasi/laporan, silakan hubungi maintainer repo ini!**

---
