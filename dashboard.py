import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from folium import FeatureGroup, LayerControl
from streamlit_folium import st_folium
from datetime import datetime
from sklearn.cluster import DBSCAN
import io
import re
import warnings

warnings.filterwarnings("ignore")

st.set_page_config(layout="wide", page_title="Risk Grid Guardsquare Dashboard", initial_sidebar_state="expanded")
st.title("🛡️ Risk Grid Guardsquare Dashboard")

@st.cache_data

def load_data():
    try:
        grid = pd.read_excel("hasil_grid_agg.xlsx")
        detail = pd.read_excel("hasil_grid_detail.xlsx")
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        st.stop()

    if "CREATED_TIME" in detail.columns:
        detail["CREATED_TIME"] = pd.to_datetime(detail["CREATED_TIME"])

    grid["Timeline"] = grid["Timeline"].astype(str)
    if "GRID_LAT" not in grid.columns:
        grid["GRID_LAT"] = grid["LATITUDE"]
    if "GRID_LON" not in grid.columns:
        grid["GRID_LON"] = grid["LONGITUDE"]
    return grid, detail

grid, detail = load_data()

with st.sidebar:
    st.header("🧮 Filter Data")
    region_list = sorted(grid["Region"].dropna().unique())
    risk_type = ["All", "High Risk Grid", "Normal Grid"]
    audit_types = sorted(grid["Audit"].dropna().unique())
    models = sorted(set([m.strip() for m in ", ".join(grid["Device_Model"].dropna().unique()).split(",")]))
    scenarios = sorted(set([s.strip() for s in ", ".join(grid["SCENARIO"].dropna().unique()).split(",")]))
    reasons = sorted(set([r.strip() for r in ", ".join(grid["Reasons"].dropna().unique()).split(",")]))
    timeline_min = detail["CREATED_TIME"].min().date()
    timeline_max = detail["CREATED_TIME"].max().date()

    selected_region = st.selectbox("Region", ["All"] + region_list)
    selected_risk = st.selectbox("Grid Risk", risk_type, index=0)
    selected_audit = st.multiselect("Audit Category", audit_types, default=audit_types)
    selected_model = st.multiselect("Device Model", models)
    selected_scenario = st.multiselect("Scenario", scenarios)
    selected_reason = st.multiselect("Reasons/Flag", reasons)
    timeline_range = st.slider("Timeline Range", min_value=timeline_min, max_value=timeline_max,
                                value=(timeline_min, timeline_max), format="YYYY-MM-DD")
    search_cif = st.text_input("🔍 Search CIF/Device/Model/Region")

    if st.button("🔄 Reset All Filters"):
        st.session_state.clear()
        st.rerun()

    st.markdown("----")
    st.subheader("Summary")
    st.markdown(f"Total Grid: **{grid.shape[0]}**")
    st.markdown(f"Total Device: **{detail['DEVICE_ID'].nunique()}**")
    st.markdown(f"Total Nasabah: **{detail['CIF'].nunique()}**")
    st.markdown(f"High Risk Grid: **{grid['HIGH_RISK'].sum()}** ({(grid['HIGH_RISK'].mean()*100):.2f}%)")
    st.markdown("**Developer:** _Data Analytics Team 2025_")

filt = grid["Audit"].isin(selected_audit)
if selected_region != "All":
    filt &= grid["Region"] == selected_region
if selected_risk == "High Risk Grid":
    filt &= grid["HIGH_RISK"]
elif selected_risk == "Normal Grid":
    filt &= ~grid["HIGH_RISK"]
if selected_model:
    pattern = '|'.join([re.escape(m) for m in selected_model])
    filt &= grid["Device_Model"].fillna('').str.contains(pattern, case=False)
if selected_scenario:
    pattern = '|'.join([re.escape(s) for s in selected_scenario])
    filt &= grid["SCENARIO"].fillna('').str.contains(pattern, case=False)
if selected_reason:
    pattern = '|'.join([re.escape(r) for r in selected_reason])
    filt &= grid["Reasons"].fillna('').str.contains(pattern, case=False)
if search_cif:
    q = search_cif.lower()
    filt &= (
        grid.get("CIFs", pd.Series("", index=grid.index)).fillna('').str.lower().str.contains(q) |
        grid.get("DEVICE_IDs", pd.Series("", index=grid.index)).fillna('').str.lower().str.contains(q) |
        grid["Device_Model"].fillna('').str.lower().str.contains(q) |
        grid["Region"].fillna('').str.lower().str.contains(q)
    )

grid_filtered = grid[filt]
detail_time = detail[
    (detail["CREATED_TIME"].dt.date >= timeline_range[0]) &
    (detail["CREATED_TIME"].dt.date <= timeline_range[1]) &
    (detail["GRID_ID"].isin(grid_filtered["GRID_ID"]))
]
# === Formulasi Risk Score ===
faceattack = detail_time[detail_time["MESSAGE_ORIGIN"].str.lower().str.contains("faceattack", na=False)]
faceattack_per_grid = faceattack.groupby("GRID_ID").size().rename("faceattack_count")

device_sharing = detail_time.groupby("DEVICE_ID")["CIF"].nunique()
device_sharing_ids = device_sharing[device_sharing > 1].index.tolist()
sharing_per_grid = detail_time[detail_time["DEVICE_ID"].isin(device_sharing_ids)]
sharing_count = sharing_per_grid.groupby("GRID_ID")["DEVICE_ID"].nunique().rename("sharing_count")

failed_ratio = detail_time.groupby("GRID_ID")["TEMPORARY_USER_STATUS"].apply(
    lambda x: (x.str.lower() == "failed").sum() / len(x)
).rename("failed_ratio")

scenario_flag = detail_time[detail_time["SCENARIO"].str.contains("REACTIVATION|RESET|FORGOT", na=False, case=False)]
scenario_per_grid = scenario_flag.groupby("GRID_ID").size().rename("high_risk_scenario")

cif_per_grid = detail_time.groupby("GRID_ID")["CIF"].nunique().rename("cif_count")

risk_df = grid_filtered.set_index("GRID_ID").copy()
risk_df = risk_df.join(faceattack_per_grid).join(sharing_count).join(failed_ratio).join(scenario_per_grid).join(cif_per_grid)
risk_df = risk_df.fillna(0)

risk_df["faceattack_norm"] = risk_df["faceattack_count"] / max(risk_df["faceattack_count"].max(), 1)
risk_df["sharing_norm"] = risk_df["sharing_count"] / max(risk_df["sharing_count"].max(), 1)

risk_df["mass_flag"] = (risk_df["cif_count"] > 10).astype(int)
risk_df["scenario_flag"] = (risk_df["high_risk_scenario"] > 0).astype(int)

risk_df["Risk_Score_Final"] = (
    0.25 * risk_df["faceattack_norm"] +
    0.25 * risk_df["sharing_norm"] +
    0.20 * risk_df["failed_ratio"] +
    0.15 * risk_df["mass_flag"] +
    0.15 * risk_df["scenario_flag"]
)

grid_filtered = grid_filtered.merge(risk_df[["Risk_Score_Final"]], on="GRID_ID", how="left")


if grid_filtered.empty:
    st.warning("⚠️ Tidak ada data sesuai filter.")
    st.stop()

st.markdown("### Grid Risk Summary", unsafe_allow_html=True)

st.subheader("🗺️ Risk Map")
m = folium.Map(location=[-2.5, 118], zoom_start=5, tiles='CartoDB positron')
mc = MarkerCluster(name="Grid Risk Summary").add_to(m)
detail_layer = FeatureGroup(name="Detail Grid Info")
presisi_layer = FeatureGroup(name="Presisi Nasabah/Device")

# Identifikasi klasifikasi tambahan untuk presisi
device_sharing = detail_time.groupby("DEVICE_ID")["CIF"].nunique()
device_sharing_ids = device_sharing[device_sharing > 1].index.tolist()
clustered_grids = detail_time.groupby("GRID_ID").size()
clustered_grids = clustered_grids[clustered_grids > 10].index.tolist()

# Tambahkan marker untuk Grid Risk Summary
for _, row in grid_filtered.iterrows():
    folium.CircleMarker(
        location=[row["GRID_LAT"], row["GRID_LON"]],
        radius=10 if row["HIGH_RISK"] else 6,
        color=row["COLOR"], fill=True, fill_color=row["COLOR"],
        fill_opacity=0.85,
        popup=folium.Popup(f"<b>Grid:</b> {row['GRID_ID']}", max_width=600)
    ).add_to(mc)

# Tambahkan marker untuk Detail Grid Info (layer agregat)
for _, row in grid_filtered.iterrows():
    df_grid = detail_time[detail_time["GRID_ID"] == row["GRID_ID"]]
    popup_html = f"""
    <b>Grid:</b> {row['GRID_ID']}<br>
    <b>Region:</b> {row['Region']}<br>
    <b>Risk Score:</b> {row['Risk_Score']}<br>
    <b>High Risk:</b> {'Yes' if row['HIGH_RISK'] else 'No'}<br>
    <b>Total Device:</b> {df_grid['DEVICE_ID'].nunique()}<br>
    <b>Total CIF:</b> {df_grid['CIF'].nunique()}
    """
    folium.CircleMarker(
        location=[row["GRID_LAT"], row["GRID_LON"]],
        radius=7,
        color="black",
        fill=True,
        fill_color="black",
        fill_opacity=0.6,
        popup=folium.Popup(popup_html, max_width=500)
    ).add_to(detail_layer)

# Tambahkan marker presisi berdasarkan multi-kondisi
for _, row in detail_time.iterrows():
    if pd.notna(row.get('LATITUDE')) and pd.notna(row.get('LONGITUDE')):
        device_id = row.get('DEVICE_ID', '')
        message_origin = str(row.get('MESSAGE_ORIGIN', '')).lower()
        grid_id = row.get('GRID_ID', '')

        is_faceattack = 'faceattack' in message_origin
        is_sharing = device_id in device_sharing_ids
        is_cluster = grid_id in clustered_grids

        # Tentukan warna berdasarkan prioritas
        if is_faceattack:
            color = 'red'
        elif is_sharing and is_cluster:
            color = 'purple'
        elif is_sharing:
            color = 'blue'
        elif is_cluster:
            color = 'orange'
        else:
            color = 'green'

        # Tentukan label klasifikasi
        labels = []
        if is_faceattack:
            labels.append("FaceAttack")
        if is_sharing:
            labels.append("DeviceSharing")
        if is_cluster:
            labels.append("Mass/Cluster")
        classification = ", ".join(labels) if labels else "Normal"

        popup_html = f"""
        <b>Classification:</b> {classification}<br>
        <b>CIF:</b> {row.get('CIF', 'N/A')}<br>
        <b>Device ID:</b> {device_id}<br>
        <b>Device Model:</b> {row.get('DEVICE_MODEL', 'N/A')}<br>
        <b>OS:</b> {row.get('OS', 'N/A')}<br>
        <b>Region:</b> {row.get('REGION', 'N/A')}<br>
        <b>MESSAGE_ORIGIN:</b> {row.get('MESSAGE_ORIGIN', 'N/A')}<br>
        <b>SCENARIO:</b> {row.get('SCENARIO', 'N/A')}<br>
        <b>PROVISIONING_NIK_LOG:</b> {row.get('PROVISIONING_NIK_LOG', 'N/A')}<br>
        <b>TEMPORARY_USER_STATUS:</b> {row.get('TEMPORARY_USER_STATUS', 'N/A')}<br>
        <b>CREATED_TIME:</b> {row.get('CREATED_TIME', 'N/A')}
        """
        folium.CircleMarker(
            location=[row['LATITUDE'], row['LONGITUDE']],
            radius=4,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=500)
        ).add_to(presisi_layer)

detail_layer.add_to(m)
presisi_layer.add_to(m)
LayerControl(collapsed=False).add_to(m)

m.fit_bounds([
    [grid_filtered["GRID_LAT"].min(), grid_filtered["GRID_LON"].min()],
    [grid_filtered["GRID_LAT"].max(), grid_filtered["GRID_LON"].max()]
])
st_data = st_folium(m, width="100%", height=750)

# ==== Drilldown ====
if st_data and st_data.get("last_object_clicked"):
    lat = round(st_data["last_object_clicked"]["lat"], 5)
    lon = round(st_data["last_object_clicked"]["lng"], 5)
    matched = grid_filtered[
        (grid_filtered["GRID_LAT"].round(5) == lat) &
        (grid_filtered["GRID_LON"].round(5) == lon)
    ]
    if not matched.empty:
        grid_id = matched.iloc[0]["GRID_ID"]
        st.success(f"**Grid Detail: {grid_id}**")
        df_detail_grid = detail[detail["GRID_ID"] == grid_id]
        st.dataframe(df_detail_grid, use_container_width=True)
        if not df_detail_grid.empty:
            timeline_grid = df_detail_grid.groupby(df_detail_grid["CREATED_TIME"].dt.date).size()
            st.bar_chart(timeline_grid)
    else:
        st.info("📍 Titik grid tidak dikenali.")
else:
    st.caption("ℹ️ Klik marker untuk melihat detail grid.")

# ==== Timeline Trend ====
st.subheader("📈 Timeline & Risk Trend")
col1, col2 = st.columns(2)
with col1:
    trend = detail_time.groupby(detail_time["CREATED_TIME"].dt.date).size()
    st.line_chart(trend, use_container_width=True)
with col2:
    fail = detail_time[detail_time["TEMPORARY_USER_STATUS"].str.lower() == "failed"]
    fail_trend = fail.groupby(fail["CREATED_TIME"].dt.date).size()
    st.line_chart(fail_trend, use_container_width=True)
st.caption("Kiri: semua aktivitas | Kanan: hanya failed (anomali)")

# ==== Device Sharing ====
st.subheader("🔗 Device Sharing Matrix")
shared = detail_time.groupby("DEVICE_ID")["CIF"].nunique().reset_index()
shared = shared[shared["CIF"] > 1]
if not shared.empty:
    st.dataframe(shared, use_container_width=True)
else:
    st.info("Tidak ada device sharing ditemukan.")

# ==== Cluster ====
st.subheader("🔥 Cluster Detection")
coords = grid_filtered[["GRID_LAT", "GRID_LON"]].dropna().to_numpy()
if len(coords) > 2:
    db = DBSCAN(eps=0.2, min_samples=2).fit(coords)
    grid_filtered = grid_filtered.assign(CLUSTER=db.labels_)
    st.dataframe(grid_filtered[grid_filtered["CLUSTER"] >= 0][["GRID_ID", "Region", "Risk_Score", "CLUSTER"]],
                 use_container_width=True)
else:
    st.info("Tidak cukup data untuk analisis cluster.")

# ==== Export ====
st.subheader("⬇️ Export Data")
col1, col2 = st.columns(2)
with col1:
    st.download_button("Download Grid (CSV)", grid_filtered.to_csv(index=False), file_name="filtered_grid.csv")
    grid_xlsx = io.BytesIO()
    with pd.ExcelWriter(grid_xlsx, engine="xlsxwriter") as writer:
        grid_filtered.to_excel(writer, index=False, sheet_name="Grid")
    st.download_button("Download Grid (Excel)", grid_xlsx.getvalue(), file_name="filtered_grid.xlsx")

with col2:
    detail_xlsx = io.BytesIO()
    with pd.ExcelWriter(detail_xlsx, engine="xlsxwriter") as writer:
        detail_time.to_excel(writer, index=False, sheet_name="Detail")
    st.download_button("Download Detail (Excel)", detail_xlsx.getvalue(), file_name="filtered_detail.xlsx")

st.markdown("---")
