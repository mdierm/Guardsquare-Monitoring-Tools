# Risk Grid Guardsquare Dashboard

### 📘 Penjelasan Komprehensif

#### 🧩 Tujuan Pencocokan Data

Proses pencocokan ini bertujuan untuk **menggabungkan informasi deteksi risiko dari sistem Threatcast (GS)** dengan **data aktivitas pengguna yang tercatat dalam sistem onboarding (export\_detail)**. Hasil pencocokan akan memberikan konteks yang lebih lengkap untuk setiap perangkat, termasuk:

* Lokasi penggunaan
* Model perangkat & sistem operasi
* Status keamanan atau risiko perangkat
* Aktivitas dan identitas nasabah (CIF)

#### 🔗 Mekanisme Join

```python
gs['app_user_id'] == export_detail['DEVICE_ID']
```

#### 📊 Data Yang Digabungkan

**Dari `export_detail`:**

* `DEVICE_ID`, `LATITUDE`, `LONGITUDE`, `CIF`, `CREATED_TIME`, `Region`, `SCENARIO`, `TEMPORARY_USER_STATUS`

**Dari `GS (Threatcast)`:**

* `device`, `os_version`, `reasons_for_detection`

#### 🧠 Proses Transformasi Tambahan

* Penambahan `GRID_ID` berdasarkan koordinat.
* Klasifikasi audit: FaceAttack, DeviceSharing, Mass/Cluster, Normal.
* Penentuan warna & high-risk grid berdasarkan skor risiko.

#### 🗂️ Output Akhir

* `hasil_grid_agg.xlsx` → Ringkasan per grid.
* `hasil_grid_detail.xlsx` → Data granular per perangkat & nasabah.

#### 🎯 Manfaat

* Pelacakan risiko geografis.
* Deteksi anomali & pola serangan.
* Dasar pengambilan keputusan & investigasi.

---

📍 **Risk Grid Guardsquare Dashboard** adalah aplikasi visualisasi interaktif berbasis Streamlit yang digunakan untuk:

* Memetakan sebaran perangkat dan pengguna berdasarkan data geolokasi.
* Menilai tingkat risiko berdasarkan skor dan pola anomali.
* Mendeteksi cluster risiko menggunakan DBSCAN.
* Mengekspor data analitik untuk keperluan pelaporan dan audit.

---

## 🚀 Fitur Utama

* **Peta Interaktif:** Visualisasi titik risiko berdasarkan lat/lon.
* **Cluster Detection:** Identifikasi konsentrasi risiko geografis.
* **Ringkasan Statistik:** Total grid, high risk, unique device.
* **Filter Wilayah & Waktu:** Filter berdasarkan region dan rentang tanggal.
* **Ekspor Data:** Unduh hasil filter dalam format CSV dan Excel.
* **Geocoding Wilayah:** Menggunakan geopy + cache lokal untuk konversi koordinat ke nama wilayah.

---

## 🧱 Struktur Proyek

* `risk_grid.py` → Script backend untuk preprocessing, geocoding, grid mapping, audit klasifikasi.
* `dashboard_patched_with_recommendations.py` → Streamlit dashboard UI interaktif.
* `hasil_grid_agg.xlsx` → Output ringkasan per grid (di-generate dari script).
* `hasil_grid_detail.xlsx` → Output detail device & nasabah.

---

## 🔧 Instalasi & Persiapan

### 1. Clone Repo

```bash
git clone https://github.com/yourusername/risk-grid-dashboard.git
cd risk-grid-dashboard
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Siapkan Data

Letakkan file Excel berikut di root folder:

* `Data Excel GS Feb 25.xlsx`
* `export_detail.xlsx`

### 4. Jalankan Proses Preprocessing

```bash
python risk_grid.py
```

Ini akan menghasilkan dua file: `hasil_grid_agg.xlsx` dan `hasil_grid_detail.xlsx`.

### 5. Jalankan Dashboard

```bash
streamlit run dashboard_patched_with_recommendations.py
```

---

## 📁 requirements.txt

```
streamlit
pandas
folium
streamlit-folium
scikit-learn
tqdm
geopy
openpyxl
xlsxwriter
numpy
```

---

## 🛡️ Audit Klasifikasi (Heuristik)

* **FaceAttack** → Terindikasi serangan wajah.
* **DeviceSharing** → Banyak CIF dengan satu perangkat.
* **Mass/Cluster** → Banyak CIF dan banyak perangkat di satu lokasi.
* **Normal** → Tidak terindikasi anomali.

---

## 🔄 Flow Pencocokan Data

Diagram berikut menunjukkan bagaimana data dari `export_detail` dan `GS (Threatcast)` digabungkan berdasarkan `DEVICE_ID` / `app_user_id`, sehingga menghasilkan data yang diperkaya:

```mermaid
flowchart LR
    A[export_detail] -->|Join on DEVICE_ID = app_user_id| B[GS (Threatcast)]
    B --> C[Hasil Join]

    subgraph A ["export_detail"]
        A1[DEVICE_ID]
        A2[LATITUDE]
        A3[CIF]
        A4[CREATED_TIME]
    end

    subgraph B ["GS (Threatcast)"]
        B1[app_user_id]
        B2[device]
        B3[os_version]
        B4[reasons_for_detection]
    end

    subgraph C ["Hasil Join"]
        C1[DEVICE_ID]
        C2[GRID_ID]
        C3[Device_Model (from device)]
        C4[OS (from os_version)]
        C5[Reasons (from reasons_for_detection)]
    end
```

---

## 📌 Catatan

* Proyek ini menggunakan reverse geocoding dari [Nominatim](https://nominatim.openstreetmap.org/) dengan caching untuk efisiensi.
* File Excel input dan output tidak di-commit ke repo karena sifatnya sensitif.

---

## 👤 Author

* ERM
* Kontribusi oleh: MDI

---

## 📄 Lisensi

Open-source untuk kebutuhan internal & riset. Gunakan dengan bijak dan sesuai etika data.
