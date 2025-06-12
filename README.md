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

## **🔄 Alur Kerja Script Risk Scoring Device/CIF Per Region**

---

### **A. Pipeline Analitik (`risk_pipeline.py`)**

1. **Load Data**

   * Membaca file DEVICE\_ID pelanggar dari Guardsquare/ThreatCast (`Final Data Unique ID - Februari 2025.xlsx`)
   * Membaca file data onboarding nasabah dari Wondr (`export_detail.xlsx`)

2. **Validasi Kolom**

   * Memastikan kolom wajib seperti `DEVICE_ID`, `CIF`, `LATITUDE`, `LONGITUDE`, dan `CREATED_TIME` tersedia.

3. **Join Data**

   * Melakukan pencocokan (join) antara device pelanggar dan data onboarding, sehingga hanya nasabah nyata yang dianalisis.

4. **Mapping Lokasi (Reverse Geocoding)**

   * Mengubah koordinat latitude/longitude menjadi nama region/provinsi/kota dengan **caching** (agar efisien dan cepat).
   * Hasil mapping disimpan dalam cache (`region_cache.pkl`) agar proses berikutnya lebih cepat.

5. **Risk Scoring per CIF**

   * Menghitung risk score setiap nasabah (CIF) berdasarkan pola:

     * **Transient:** hanya 1 device, hanya 1 bulan
     * **Persistent:** 1 device, >1 bulan
     * **Multi-device:** >1 device, 1 bulan
     * **Critical:** >1 device, >1 bulan

6. **Analitik Cohort**

   * Menganalisis tren risk berdasarkan cohort onboarding nasabah (bulan onboarding pertama).

7. **Visualisasi**

   * Membuat bar chart total dan rata-rata risk score per region.
   * Membuat heatmap geospasial (HTML) untuk distribusi risk di seluruh Indonesia.

8. **Summary Impact**

   * Menampilkan ringkasan jumlah nasabah terdampak, breakdown transient/persistent/critical.

9. **Export Output**

   * Menyimpan hasil scoring ke file Excel (dengan timestamp).
   * Menyimpan heatmap ke HTML.

10. **Progress Info**

    * Selama eksekusi, script menampilkan status dan info summary di console agar user tahu progress setiap step.

---

### **B. Dashboard Interaktif (`dashboard.py`)**

1. **Load Data Output Pipeline**

   * Membaca file Excel hasil scoring dari pipeline (`hasil_risk_scoring_per_cif_YYYYMMDD_HHMM.xlsx`).

2. **Filter & Navigasi**

   * User dapat memfilter cohort, region, dan risk type.
   * Jumlah data hasil filter selalu diinformasikan (progress info).

3. **Tab Visualisasi**

   * **Risk per Region**: Bar chart total risk score per wilayah.
   * **Trend Cohort**: Line chart rata-rata risk score per cohort onboarding.
   * **Heatmap**: Peta sebaran lokasi onboarding device pelanggar.
   * **Cluster Analysis**: Deteksi hotspot risk via K-Means (dengan slider jumlah cluster).
   * **Demografi (jika ada)**: Bar chart segmentasi risk per gender/tipe nasabah.

4. **Progress Info & Warning**

   * Muncul otomatis jika data hasil filter sedikit/tidak cukup untuk visual tertentu (heatmap/cluster).

5. **Keterangan Sidebar**

   * Penjelasan workflow, filter, dan batasan tools untuk user.

---

## **Diagram Sederhana Alur Pipeline**

```mermaid
flowchart TD
    A[Data Device Pelanggar\n(Guardsquare/ThreatCast)]
    B[Data Onboarding Nasabah\n(Wondr)]
    C[Join DeviceID dengan Data Onboarding]
    D[Reverse Geocoding\n(Latitude, Longitude → Region)]
    E[Risk Scoring per CIF\n(Transient/Persistent/Critical)]
    F[Analitik Cohort]
    G[Visualisasi & Export\n(Bar Chart, Heatmap, Excel)]
    H[Web Dashboard Interaktif\n(Streamlit)]
    I[Summary Impact & Progress Info]

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

## **Inti Alur Kerja**

* **Input:** Data device pelanggar & data onboarding
* **Proses:** Join → mapping lokasi → scoring risk → analitik cohort/region
* **Output:** Tabel scoring CIF, heatmap HTML, dashboard web interaktif

---

**Tools ini memastikan risk analytic berbasis device & region hanya memakai data yang valid dan siap presentasi ke audit/BI.**
**Alur ini juga sangat fleksibel—jika data atau model scoring berubah, pipeline bisa langsung diadaptasi.**

---


