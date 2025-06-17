# dashboard2_recommended_final_PATCHED.py

import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from datetime import datetime
from sklearn.cluster import DBSCAN
import io

st.set_page_config(layout="wide", page_title="Risk Grid Guardsquare Dashboard", initial_sidebar_state="expanded")
st.title("🛡️ Risk Grid Guardsquare Dashboard")

@st.cache_data
def load_data():
    grid = pd.read_excel("hasil_grid_agg.xlsx")
    detail = pd.read_excel("hasil_grid_detail.xlsx")
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

# ==== Apply filters ====
filt = grid["Audit"].isin(selected_audit)
if selected_region != "All":
    filt &= grid["Region"] == selected_region
if selected_risk == "High Risk Grid":
    filt &= grid["HIGH_RISK"]
elif selected_risk == "Normal Grid":
    filt &= ~grid["HIGH_RISK"]
if selected_model:
    filt &= grid["Device_Model"].apply(lambda x: any(m in str(x) for m in selected_model))
if selected_scenario:
    filt &= grid["SCENARIO"].apply(lambda x: any(s in str(x) for s in selected_scenario))
if selected_reason:
    filt &= grid["Reasons"].apply(lambda x: any(r in str(x) for r in selected_reason))
if search_cif:
    q = search_cif.lower()
    filt &= (
        grid["CIFs"].str.lower().str.contains(q) |
        grid["DEVICE_IDs"].str.lower().str.contains(q) |
        grid["Device_Model"].str.lower().str.contains(q) |
        grid["Region"].str.lower().str.contains(q)
    )

grid_filtered = grid[filt]
detail_time = detail[
    (detail["CREATED_TIME"].dt.date >= timeline_range[0]) &
    (detail["CREATED_TIME"].dt.date <= timeline_range[1])
]

if grid_filtered.empty:
    st.warning("⚠️ Tidak ada data sesuai filter.")
    st.stop()

# ==== Summary Cards ====
st.markdown("### Grid Risk Summary", unsafe_allow_html=True)
st.markdown(f"""
<div style="display: flex; flex-wrap: wrap; gap: 20px; margin: 10px 0 20px;">
  <div style="flex: 1; background:#f8f8f8; padding:15px; border-radius:10px; text-align: center;">
    <div style="font-size:18px; color:#888;">Total Grid</div>
    <div style="font-size:26px; font-weight:bold; color:#d62728;">{len(grid_filtered)}</div>
  </div>
  <div style="flex: 1; background:#f8f8f8; padding:15px; border-radius:10px; text-align: center;">
    <div style="font-size:18px; color:#888;">Total Nasabah</div>
    <div style="font-size:26px; font-weight:bold; color:#1f77b4;">{detail_time['CIF'].nunique()}</div>
  </div>
  <div style="flex: 1; background:#f8f8f8; padding:15px; border-radius:10px; text-align: center;">
    <div style="font-size:18px; color:#888;">High Risk Grid</div>
    <div style="font-size:26px; font-weight:bold; color:#ff0000;">{grid_filtered['HIGH_RISK'].sum()}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ==== Map ====
st.subheader("🗺️ Risk Map")
m = folium.Map(location=[-2.5, 118], zoom_start=5, tiles='CartoDB positron')
mc = MarkerCluster().add_to(m)

for _, row in grid_filtered.iterrows():
    folium.CircleMarker(
        location=[row["GRID_LAT"], row["GRID_LON"]],
        radius=10 if row["HIGH_RISK"] else 6,
        color=row["COLOR"], fill=True, fill_color=row["COLOR"],
        fill_opacity=0.85,
        popup=folium.Popup(f"<b>Grid:</b> {row['GRID_ID']}", max_width=600)
    ).add_to(mc)

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
