## **Summary Kegunaan Tools Risk Scoring Device/CIF Per Region**

### **1. Identifikasi & Mitigasi Risiko Device**

Tools ini memungkinkan bank atau institusi keuangan **mengidentifikasi nasabah yang menggunakan device berisiko tinggi** (misal: rooted/jailbreak/custom ROM),
berdasarkan data real-time dari Guardsquare/ThreatCast yang sudah diintegrasikan ke data onboarding nasabah.

### **2. Analisis Populasi Nasabah Terdampak**

Secara otomatis, tools ini melakukan pencocokan antara device yang terdeteksi pelanggaran dan nasabah aktif (CIF),
sehingga **bank dapat mengetahui dengan presisi berapa banyak nasabah unik yang akan ter-impact** jika kebijakan security enforcement seperti RASP Hardware diaktifkan.

### **3. Pemetaan Risiko Secara Geospasial**

Tools ini memanfaatkan data lokasi onboarding (long/lat) untuk **memetakan sebaran risiko hingga ke tingkat wilayah/region/provinsi**.
Hal ini sangat membantu tim risk management, BI, ataupun auditor untuk:

* Melihat **wilayah-wilayah rawan** (hotspot) penggunaan device berisiko.
* Menentukan prioritas mitigasi berdasarkan geografi.

### **4. Analitik Cohort & Trend Risk**

Dengan fitur cohort analysis, tools ini dapat:

* **Menganalisis tren risiko** berdasarkan kelompok waktu onboarding (cohort), sehingga mudah dilihat
  apakah ada lonjakan kasus risk di periode tertentu (misal, pasca campaign, promosi, dsb).
* Membandingkan **risk score antar batch onboarding**—bisa jadi landasan evaluasi efektivitas policy security dari waktu ke waktu.

### **5. Visualisasi dan Dashboard Interaktif**

Tools menghasilkan **dashboard web interaktif** (Streamlit)
dengan berbagai fitur visualisasi—bar chart, trend line, heatmap, cluster analysis—
yang memudahkan tim untuk:

* Mengeksplorasi data risk secara live
* Melakukan filter by region, risk level, cohort
* Menyusun report dan audit dengan evidence visual

### **6. Otomatisasi dan Efisiensi Analitik**

* **Caching** otomatis untuk mapping wilayah, membuat proses analisis berikutnya jauh lebih cepat.
* Proses join, scoring, dan export data **sepenuhnya otomatis**—efisien dan mengurangi potensi human error.

### **7. Landasan untuk Decision Making & Policy**

**Hasil analisis dan visualisasi** dari tools ini dapat digunakan sebagai **landasan data-driven** untuk:

* Membuat keputusan kebijakan risk enforcement (blokir device, alert, dsb)
* Pelaporan compliance ke regulator/auditor
* Penyusunan roadmap security digital channel bank

---

## **Kesimpulan**

**Tools Risk Scoring Device/CIF Per Region** adalah solusi end-to-end untuk:

* Mengidentifikasi, memetakan, dan memvisualisasikan risiko perangkat di populasi nasabah,
* Memberikan insight real-time dan historical trend,
* Serta mempercepat pengambilan keputusan mitigasi risiko berbasis data faktual.

---

## **Summary: Reverse Geocoding pada Risk Analytics Tools**

### **Apa itu Reverse Geocoding?**

Reverse geocoding adalah proses **mengubah koordinat geografis** (latitude, longitude)
menjadi **nama wilayah nyata** (seperti kota, kabupaten, provinsi, atau negara).

### **Tujuan dalam Tools Ini**

* **Menerjemahkan lokasi onboarding nasabah** (dari koordinat device) ke region/wilayah
* **Memudahkan analisis distribusi risk secara geospasial** (pemetaan per provinsi/kota)

### **Cara Kerja di Script:**

1. **Ambil koordinat** (latitude, longitude) dari file onboarding nasabah.
2. **Gunakan modul `geopy.Nominatim`** untuk query ke OpenStreetMap.
3. **Mapping hasil** ke kolom baru (`REGION`, `PROVINCE`, `CITY`) di dataframe.
4. **Caching**:

   * Lokasi yang sudah pernah diproses **tidak akan query ulang**, sehingga proses lebih cepat di run berikutnya.

---

## **Contoh Kode Mini Reverse Geocoding (Python)**

```python
from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="risk_geomap_check")

latitude = 3.583333333
longitude = 98.68093333

location = geolocator.reverse(f"{latitude}, {longitude}", language="id", timeout=10)
if location and location.raw.get('address'):
    address = location.raw['address']
    print("Lokasi:", location.address)
    print("Province:", address.get('state'))
    print("City/Regency:", address.get('city') or address.get('county'))
    print("Country:", address.get('country'))
else:
    print("Lokasi tidak ditemukan.")
```

---

## **Simulasi Hasil Reverse Geocoding**

**Input:**

```
latitude = 3.583333333
longitude = 98.68093333
```

**Output Reverse Geocoding:**

```
Lokasi: Kecamatan Medan Sunggal, Kota Medan, Sumatera Utara, Indonesia
Province: Sumatera Utara
City/Regency: Kota Medan
Country: Indonesia
```

---

### **Contoh Output Lain:**

**Input:**

```
latitude = -2.227071667
longitude = 113.9307717
```

**Output:**

```
Lokasi: Kabupaten Kapuas, Kalimantan Tengah, Indonesia
Province: Kalimantan Tengah
City/Regency: Kabupaten Kapuas
Country: Indonesia
```

---

## **Kesimpulan**

* **Reverse geocoding pada tools ini otomatis, cepat, dan efisien** (berkat caching).
* **Output langsung siap pakai untuk analisis wilayah risk dan visualisasi heatmap/cluster.**
* **Validasi bisa dilakukan dengan cek hasil langsung di Google Maps/OpenStreetMap** jika diperlukan.

---

