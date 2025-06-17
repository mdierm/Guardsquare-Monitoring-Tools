import pandas as pd
import numpy as np
import folium
from folium.plugins import MarkerCluster
import pickle
from tqdm import tqdm
import os

# ========== KONFIGURASI ==========
GS_PATH = "Data Excel GS Feb 25.xlsx"
GS_SHEET = "threatcast bni Hardware Febuary"
ONBOARD_PATH = "export_detail.xlsx"
REGION_CACHE_PATH = "region_cache.pkl"
OUT_MAP = "risk_grid_map.html"
OUT_GRID = "hasil_grid_agg.xlsx"
OUT_DETAIL = "hasil_grid_detail.xlsx"

GRID_DEC = 2   # grid presisi 0.01 derajat (sekitar 1km)
MIN_RISK = 5   # min risk score dianggap high risk

from geopy.geocoders import Nominatim
import time

def get_region(lat, lon, cache, delay=1):
    key = (round(lat, 3), round(lon, 3))
    if pd.isnull(lat) or pd.isnull(lon) or lat == 0 or lon == 0:
        return "Unknown"
    if key in cache:
        return cache[key]
    geolocator = Nominatim(user_agent="risk_grid_locator")
    try:
        location = geolocator.reverse(f"{lat}, {lon}", language="id", timeout=5)
        if location and location.raw.get('address'):
            address = location.raw['address']
            region = (
                address.get('city') or address.get('town') or
                address.get('county') or address.get('state') or
                address.get('country')
            )
            cache[key] = region
            time.sleep(delay)
            return region
        else:
            cache[key] = "Unknown"
            return "Unknown"
    except Exception:
        cache[key] = "Unknown"
        return "Unknown"

def load_region_cache(path=REGION_CACHE_PATH):
    if os.path.exists(path):
        with open(path, 'rb') as f:
            cache = pickle.load(f)
        print(f"[INFO] Region cache loaded ({len(cache)} coords)")
    else:
        cache = {}
        print("[INFO] Region cache tidak ditemukan, akan dibuat baru.")
    return cache

def save_region_cache(cache, path=REGION_CACHE_PATH):
    with open(path, 'wb') as f:
        pickle.dump(cache, f)
    print(f"[INFO] Region cache saved ({len(cache)} coords)")

def load_data():
    print("[INFO] Load GS + Onboarding data ...")
    gs = pd.read_excel(GS_PATH, sheet_name=GS_SHEET)
    ob = pd.read_excel(ONBOARD_PATH)
    print(f"[INFO] Data GS loaded: {len(gs)} rows")
    print(f"[INFO] Data onboarding loaded: {len(ob)} rows")
    return gs, ob

def preprocess_join(gs, ob):
    print("[INFO] Preprocessing & join ...")
    gs['app_user_id'] = gs['app_user_id'].astype(str)
    ob['DEVICE_ID'] = ob['DEVICE_ID'].astype(str)
    df = ob[ob['DEVICE_ID'].isin(gs['app_user_id'])]
    print(f"[INFO] Data join: {len(df)} baris, {df['CIF'].nunique()} CIF unik")
    return df, gs

def region_mapping(df, cache):
    tqdm.pandas()
    def _map(row):
        lat, lon = row['LATITUDE'], row['LONGITUDE']
        return get_region(lat, lon, cache, delay=0.1)
    print("[INFO] Mapping region (geocode w/ cache)...")
    if 'Region' not in df.columns or df['Region'].isnull().any():
        df['Region'] = df.progress_apply(_map, axis=1)
        save_region_cache(cache)
    return df

def audit_flag(row):
    # Cek FaceAttack dari MESSAGE_ORIGIN
    if "faceattack" in str(row.get('MESSAGE_ORIGIN', '')).lower():
        return "FaceAttack"
    if row['Customer_Count'] > 1 and row['Device_Count'] == 1:
        return "DeviceSharing"
    if row['Customer_Count'] > 1 and row['Device_Count'] > 1:
        return "Mass/Cluster"
    return "Normal"

def audit_color(audit):
    return {
        "FaceAttack": "red",
        "DeviceSharing": "orange",
        "Mass/Cluster": "purple",
        "Normal": "blue"
    }.get(audit, "gray")

def grid_aggregate(df, gs):
    print("[INFO] Grid mapping ...")
    df['GRID_LAT'] = df['LATITUDE'].round(GRID_DEC)
    df['GRID_LON'] = df['LONGITUDE'].round(GRID_DEC)
    df['GRID_ID'] = df['GRID_LAT'].astype(str) + "," + df['GRID_LON'].astype(str)

    gs_sub = gs[['app_user_id', 'device', 'os_version', 'reasons_for_detection']].drop_duplicates('app_user_id')
    gs_sub.columns = ['DEVICE_ID', 'Device_Model', 'OS', 'Reasons']
    df = pd.merge(df, gs_sub, how='left', left_on='DEVICE_ID', right_on='DEVICE_ID')

    agg = df.groupby(['GRID_ID', 'GRID_LAT', 'GRID_LON', 'Region']).agg(
        Risk_Score=('CIF', 'count'),
        Customer_Count=('CIF', pd.Series.nunique),
        Device_Count=('DEVICE_ID', pd.Series.nunique),
        Device_Model=('Device_Model', lambda x: ", ".join(set(str(i) for i in x if pd.notna(i)))),
        OS=('OS', lambda x: ", ".join(set(str(i) for i in x if pd.notna(i)))),
        MESSAGE_ORIGIN=('MESSAGE_ORIGIN', lambda x: ", ".join(set(str(i) for i in x if pd.notna(i)))),
        SCENARIO=('SCENARIO', lambda x: ", ".join(set(str(i) for i in x if pd.notna(i)))),
        PROVISIONING_NIK_LOG=('PROVISIONING_NIK_LOG', lambda x: ", ".join(set(str(i) for i in x if pd.notna(i)))),
        TEMPORARY_USER_STATUS=('TEMPORARY_USER_STATUS', lambda x: ", ".join(set(str(i) for i in x if pd.notna(i)))),
        Reasons=('Reasons', lambda x: ", ".join(set(str(i) for i in x if pd.notna(i)))),
        FAILED_Count=('TEMPORARY_USER_STATUS', lambda x: sum(str(i).lower() == 'failed' for i in x)),
        Timeline=('CREATED_TIME', lambda x: ", ".join(str(i) for i in sorted(set(x)) if pd.notna(i))),
        CIFs=('CIF', lambda x: ", ".join(set(str(i) for i in x if pd.notna(i)))),
        DEVICE_IDs=('DEVICE_ID', lambda x: ", ".join(set(str(i) for i in x if pd.notna(i))))
    ).reset_index()

    agg['Audit'] = agg.apply(audit_flag, axis=1)
    agg['COLOR'] = agg['Audit'].apply(audit_color)
    agg['HIGH_RISK'] = agg['Risk_Score'] >= MIN_RISK
    agg['POPUP'] = agg.apply(lambda row: f"""
        <b>Grid:</b> {row['GRID_ID']}<br>
        <b>Device Model:</b> {row['Device_Model']}<br>
        <b>OS:</b> {row['OS']}<br>
        <b>Region:</b> {row['Region']}<br>
        <b>Risk Score:</b> {row['Risk_Score']}<br>
        <b>Customer Count:</b> {row['Customer_Count']}<br>
        <b>Device Count:</b> {row['Device_Count']}<br>
        <b>Audit:</b> {row['Audit']}<br>
        <b>Reasons:</b> {row['Reasons']}<br>
        <b>MESSAGE_ORIGIN:</b> {row['MESSAGE_ORIGIN']}<br>
        <b>SCENARIO:</b> {row['SCENARIO']}<br>
        <b>PROVISIONING_NIK_LOG:</b> {row['PROVISIONING_NIK_LOG']}<br>
        <b>TEMPORARY_USER_STATUS:</b> {row['TEMPORARY_USER_STATUS']}<br>
        <b>FAILED Count:</b> {row['FAILED_Count']}<br>
        <b>Timeline:</b> {row['Timeline']}<br>
        <b>CIFs:</b> {row['CIFs']}<br>
        <b>DEVICE_IDs:</b> {row['DEVICE_IDs']}<br>
    """, axis=1)
    return agg, df

def plot_point_precision(df, m):
    print("[INFO] Plotting individual customer/device points ...")
    for _, row in df.iterrows():
        lat, lon = row.get('LATITUDE'), row.get('LONGITUDE')
        if pd.isnull(lat) or pd.isnull(lon) or lat == 0 or lon == 0:
            continue
        # Color by MESSAGE_ORIGIN/Audit (for device/cif)
        col = "blue"
        if "faceattack" in str(row.get("MESSAGE_ORIGIN", "")).lower():
            col = "red"
        elif str(row.get("TEMPORARY_USER_STATUS", "")).lower() == "failed":
            col = "orange"
        popup = f"""
        <b>CIF:</b> {row.get('CIF', '')}<br>
        <b>Device ID:</b> {row.get('DEVICE_ID', '')}<br>
        <b>Device Model:</b> {row.get('Device_Model', '')}<br>
        <b>OS:</b> {row.get('OS', '')}<br>
        <b>Region:</b> {row.get('Region', '')}<br>
        <b>MESSAGE_ORIGIN:</b> {row.get('MESSAGE_ORIGIN', '')}<br>
        <b>SCENARIO:</b> {row.get('SCENARIO', '')}<br>
        <b>PROVISIONING_NIK_LOG:</b> {row.get('PROVISIONING_NIK_LOG', '')}<br>
        <b>TEMPORARY_USER_STATUS:</b> {row.get('TEMPORARY_USER_STATUS', '')}<br>
        <b>CREATED_TIME:</b> {row.get('CREATED_TIME', '')}<br>
        """
        folium.CircleMarker(
            location=[lat, lon],
            radius=4,
            color=col,
            fill=True,
            fill_color=col,
            fill_opacity=0.65,
            popup=folium.Popup(popup, max_width=400)
        ).add_to(m)

def plot_map(agg, df):
    print("[INFO] Visualisasi map ...")
    m = folium.Map(location=[-2.5, 118.0], zoom_start=5, tiles='OpenStreetMap')
    mc = MarkerCluster(name="Grid Risk Summary").add_to(m)
    for _, row in agg.iterrows():
        lat, lon = row['GRID_LAT'], row['GRID_LON']
        if pd.isnull(lat) or pd.isnull(lon):
            continue
        folium.CircleMarker(
            location=[lat, lon],
            radius=8 if row['HIGH_RISK'] else 5,
            color=row['COLOR'],
            fill=True,
            fill_color=row['COLOR'],
            fill_opacity=0.7,
            popup=folium.Popup(row['POPUP'], max_width=450)
        ).add_to(mc)
    fg_points = folium.FeatureGroup(name="Presisi Nasabah/Device").add_to(m)
    plot_point_precision(df, fg_points)
    folium.LayerControl(collapsed=False).add_to(m)
    m.save(OUT_MAP)
    print(f"[INFO] Map risk grid berhasil disimpan ke {OUT_MAP}")

def main():
    print("=== RISK GRID PIPELINE v5.1 ===")
    gs, ob = load_data()
    df, gs = preprocess_join(gs, ob)
    cache = load_region_cache()
    df = region_mapping(df, cache)
    agg, df_full = grid_aggregate(df, gs)
    # --- Simpan hasil ke file untuk dashboard ---
    agg.to_excel(OUT_GRID, index=False)
    df_full.to_excel(OUT_DETAIL, index=False)
    print(f"[INFO] Hasil grid summary disimpan ke {OUT_GRID}")
    print(f"[INFO] Hasil detail device-nasabah disimpan ke {OUT_DETAIL}")
    # --- Summary ---
    print("="*50)
    print(f"Total nasabah terdeteksi: {df['CIF'].nunique()}")
    print(f"Total grid/titik: {agg.shape[0]}")
    print(f"High risk grid: {(agg['HIGH_RISK']).sum()} ({(agg['HIGH_RISK']).mean():.2%})")
    print("Top 10 grid paling tinggi risk score:")
    print(agg.sort_values("Risk_Score", ascending=False).head(10)[['GRID_ID', 'Risk_Score', 'Customer_Count', 'GRID_LAT', 'GRID_LON', 'Region', 'HIGH_RISK']])
    print("="*50)
    plot_map(agg, df_full)
    print("Pipeline join + scoring + grid mapping selesai! 🚦")

if __name__ == "__main__":
    main()
