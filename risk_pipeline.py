import pandas as pd
from geopy.geocoders import Nominatim
from tqdm import tqdm
import time
import matplotlib.pyplot as plt
import folium
from folium.plugins import HeatMap
import pickle

# --- 1. Load Data ---
def load_threatcast(path):
    df = pd.read_excel(path)
    return set(df.iloc[:, 0].astype(str))

def load_production(path):
    return pd.read_excel(path)

# --- 2. Join DeviceID Guardsquare ke Production ---
def filter_production_by_deviceid(df_prod, device_ids):
    return df_prod[df_prod['DEVICE_ID'].astype(str).isin(device_ids)].copy()

# --- 3. Caching Setup ---
def load_region_cache(cache_path='region_cache.pkl'):
    try:
        with open(cache_path, 'rb') as f:
            cache = pickle.load(f)
    except FileNotFoundError:
        cache = {}
    return cache

def save_region_cache(cache, cache_path='region_cache.pkl'):
    with open(cache_path, 'wb') as f:
        pickle.dump(cache, f)

# --- 4. Geocoding with Caching (serial, for simplicity & API respect) ---
def get_region_cached(lat, lon, geolocator, cache, delay=1):
    key = (round(lat, 5), round(lon, 5))
    if pd.isnull(lat) or pd.isnull(lon):
        return "Unknown"
    if key in cache:
        return cache[key]
    try:
        location = geolocator.reverse(f"{lat}, {lon}", language='id', timeout=10)
        time.sleep(delay)
        if location and location.raw.get('address'):
            address = location.raw['address']
            region = (
                address.get('city') or address.get('town') or
                address.get('county') or address.get('state') or
                address.get('country')
            )
            cache[key] = region
            return region
        else:
            cache[key] = "Unknown"
            return "Unknown"
    except:
        cache[key] = "Unknown"
        return "Unknown"

def map_all_regions(df, cache, delay=1):
    geolocator = Nominatim(user_agent="wondr_risk_segmentasi")
    tqdm.pandas()
    df['REGION'] = df.progress_apply(
        lambda row: get_region_cached(row['LATITUDE'], row['LONGITUDE'], geolocator, cache, delay=delay), axis=1
    )
    return df

# --- 5. Risk Scoring Dinamis per CIF ---
def compute_risk_scoring(df):
    df['CREATED_TIME'] = pd.to_datetime(df['CREATED_TIME'], errors='coerce')
    df['BULAN_TAHUN'] = df['CREATED_TIME'].dt.to_period('M')
    df['COHORT'] = df.groupby('CIF')['CREATED_TIME'].transform('min').dt.to_period('M')

    results = []
    for cif, group in df.groupby('CIF'):
        months = group['BULAN_TAHUN'].nunique()
        devices = group['DEVICE_ID'].nunique() if 'DEVICE_ID' in group else 1
        returning = months > 1
        # Risk scoring dinamis
        if months == 1 and devices == 1:
            score = 1  # Transient
            label = "Transient"
        elif months > 1 and devices == 1:
            score = 2  # Persistent (multi-bulan)
            label = "Persistent"
        elif months == 1 and devices > 1:
            score = 2  # Multi-device
            label = "Multi-device"
        elif months > 1 and devices > 1:
            score = 3  # Persistent + Multi-device
            label = "Critical"
        else:
            score = 1
            label = "Transient"
        region = group['REGION'].mode()[0] if group['REGION'].notna().any() else "Unknown"
        cohort = group['COHORT'].iloc[0]
        results.append({'CIF': cif, 'Risk_Score': score, 'Risk_Label': label, 'Region': region, 'Cohort': cohort})
    return pd.DataFrame(results)

# --- 6. Cohort & Segmentasi Analisis ---
def cohort_analysis(df_risk):
    cohort_summary = df_risk.groupby('Cohort')['Risk_Score'].mean()
    plt.figure(figsize=(10, 4))
    plt.plot(cohort_summary.index.astype(str), cohort_summary.values, marker='o')
    plt.title("Rata-rata Risk Score per Cohort Onboarding")
    plt.xlabel("Cohort Onboarding (Bulan-Tahun)")
    plt.ylabel("Average Risk Score")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
    return cohort_summary

# --- 7. Risk Region Aggregation & Visualisasi ---
def visualize_risk_region(df_risk, top_n=10):
    risk_region_sum = df_risk.groupby('Region')['Risk_Score'].sum().sort_values(ascending=False)
    risk_region_mean = df_risk.groupby('Region')['Risk_Score'].mean().sort_values(ascending=False)
    print("\nRisk score total per region (top 10):")
    print(risk_region_sum.head(top_n))
    print("\nRisk score rata-rata per region (top 10):")
    print(risk_region_mean.head(top_n))
    plt.figure(figsize=(12, 5))
    risk_region_sum.head(top_n).plot(kind='bar', color='crimson')
    plt.title('Top 10 Wilayah dengan Total Risk Score Tertinggi')
    plt.xlabel('Wilayah (Region)')
    plt.ylabel('Total Risk Score')
    plt.xticks(rotation=25)
    plt.tight_layout()
    plt.show()
    plt.figure(figsize=(12, 5))
    risk_region_mean.head(top_n).plot(kind='bar', color='purple')
    plt.title('Top 10 Wilayah dengan Rata-Rata Risk Score CIF Tertinggi')
    plt.xlabel('Wilayah (Region)')
    plt.ylabel('Average Risk Score per CIF')
    plt.xticks(rotation=25)
    plt.tight_layout()
    plt.show()
    return risk_region_sum, risk_region_mean

# --- 8. Heatmap Geospasial ---
def export_heatmap(df, path='risk_heatmap.html'):
    df_heat = df.dropna(subset=['LATITUDE', 'LONGITUDE'])
    map_center = [-2.5, 118.0]
    m = folium.Map(location=map_center, zoom_start=5, tiles='OpenStreetMap')
    points = df_heat[['LATITUDE', 'LONGITUDE']].values.tolist()
    HeatMap(points, radius=10, blur=12, max_zoom=13).add_to(m)
    m.save(path)
    print(f"Heatmap risk scoring wilayah tersimpan di {path}")

# --- 9. Analisis Jumlah Nasabah Terimpact ---
def impacted_customer_summary(df_risk):
    jumlah_nasabah = df_risk['CIF'].nunique()
    transient_risk = (df_risk['Risk_Label'] == "Transient").sum()
    persistent_risk = (df_risk['Risk_Label'] != "Transient").sum()
    print("="*50)
    print(f"Total nasabah terdeteksi (CIF unik): {jumlah_nasabah}")
    print(f"Transient risk (sekali pelanggar): {transient_risk} nasabah ({transient_risk/jumlah_nasabah:.2%})")
    print(f"Persistent/critical/multi-device risk: {persistent_risk} nasabah ({persistent_risk/jumlah_nasabah:.2%})")
    print("="*50)
    print("**Ini adalah estimasi nasabah terdampak jika RASP hardware enforcement diaktifkan.**")

# --- 10. Pipeline Utama ---
def main_pipeline(path_threatcast, path_prod):
    device_ids = load_threatcast(path_threatcast)
    df_prod = load_production(path_prod)
    df_join = filter_production_by_deviceid(df_prod, device_ids)

    print(f"DEVICE_ID pelanggar (Guardsquare): {len(device_ids)}")
    print(f"Match onboarding: {len(df_join)} rows, {df_join['CIF'].nunique()} CIF unik")

    region_cache = load_region_cache()
    if 'REGION' not in df_join.columns:
        print("Mapping long/lat ke REGION (dengan cache, proses bisa lama)...")
        df_join = map_all_regions(df_join, region_cache, delay=1)
        save_region_cache(region_cache)
    else:
        print("Kolom REGION sudah ada, skip mapping.")

    df_risk = compute_risk_scoring(df_join)
    cohort_analysis(df_risk)
    risk_region_sum, risk_region_mean = visualize_risk_region(df_risk)
    export_heatmap(df_join)
    impacted_customer_summary(df_risk)
    df_risk.to_excel("hasil_risk_scoring_per_cif.xlsx", index=False)
    print("Hasil risk scoring CIF diekspor ke hasil_risk_scoring_per_cif.xlsx")
    return df_risk, risk_region_sum, risk_region_mean

# --- Run Pipeline ---
if __name__ == "__main__":
    df_risk, risk_region_sum, risk_region_mean = main_pipeline(
        "Final Data Unique ID - Februari 2025.xlsx",
        "export_detail.xlsx"
    )
