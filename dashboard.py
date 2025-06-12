# pip install streamlit streamlit-folium folium
import streamlit as st
import pandas as pd
from streamlit_folium import st_folium
import folium
from folium.plugins import HeatMap
from sklearn.cluster import KMeans

st.set_page_config(layout="wide")
st.title("Risk Scoring Device per Region - Dashboard")

@st.cache_data
def load_data():
    return pd.read_excel("hasil_risk_scoring_per_cif.xlsx")

df_risk = load_data()
cohorts = ["Semua"] + sorted(df_risk['Cohort'].astype(str).unique().tolist())
regions = ["Semua"] + sorted(df_risk['Region'].unique().tolist())
risk_labels = ["Semua"] + df_risk['Risk_Label'].unique().tolist()

col1, col2, col3 = st.columns(3)
with col1:
    cohort_filter = st.selectbox("Filter cohort onboarding", cohorts)
with col2:
    region_filter = st.selectbox("Filter region", regions)
with col3:
    risk_filter = st.selectbox("Filter risk type", risk_labels)

df_dash = df_risk.copy()
if cohort_filter != "Semua":
    df_dash = df_dash[df_dash['Cohort'].astype(str) == cohort_filter]
if region_filter != "Semua":
    df_dash = df_dash[df_dash['Region'] == region_filter]
if risk_filter != "Semua":
    df_dash = df_dash[df_dash['Risk_Label'] == risk_filter]

st.metric("Jumlah CIF (nasabah)", df_dash['CIF'].nunique())

tab1, tab2, tab3, tab4 = st.tabs(["Risk per Region", "Trend Cohort", "Heatmap", "Cluster Analysis"])
with tab1:
    st.subheader("Risk Score per Region")
    st.bar_chart(df_dash.groupby('Region')['Risk_Score'].sum().sort_values(ascending=False))

with tab2:
    st.subheader("Trend Risk Score per Cohort Onboarding")
    cohort_summary = df_dash.groupby('Cohort')['Risk_Score'].mean()
    st.line_chart(cohort_summary)

with tab3:
    st.subheader("Heatmap Risk Device per Region")
    m = folium.Map(location=[-2.5, 118.0], zoom_start=5)
    if 'LATITUDE' in df_dash and 'LONGITUDE' in df_dash:
        points = df_dash.dropna(subset=['LATITUDE', 'LONGITUDE'])[['LATITUDE', 'LONGITUDE']].values.tolist()
        if points:
            HeatMap(points, radius=10).add_to(m)
    st_folium(m, width=900, height=500)

with tab4:
    st.subheader("Cluster Analysis (K-Means, titik risk)")
    if df_dash.dropna(subset=['LATITUDE', 'LONGITUDE']).shape[0] >= 2:
        df_kmeans = df_dash.dropna(subset=['LATITUDE', 'LONGITUDE']).copy()
        X = df_kmeans[['LATITUDE', 'LONGITUDE']].to_numpy()
        k = st.slider("Jumlah cluster", 2, min(10, len(X)), 5)
        kmeans = KMeans(n_clusters=k, random_state=0).fit(X)
        df_kmeans['cluster'] = kmeans.labels_
        m2 = folium.Map(location=[-2.5, 118.0], zoom_start=5)
        colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen']
        for cl in range(k):
            cl_points = df_kmeans[df_kmeans['cluster'] == cl]
            for _, row in cl_points.iterrows():
                folium.CircleMarker([row['LATITUDE'], row['LONGITUDE']],
                                    radius=3, color=colors[cl % len(colors)], fill=True).add_to(m2)
        st_folium(m2, width=900, height=500)
    else:
        st.info("Tidak cukup data titik untuk cluster analysis.")

# Segmentasi Demografis (jika ada kolom, misal USIA/JENIS_KELAMIN/TIPE_NASABAH)
if 'USIA' in df_dash:
    st.subheader("Risk per Segmentasi Usia")
    usia_group = df_dash.groupby('USIA')['Risk_Score'].mean()
    st.bar_chart(usia_group)

if 'JENIS_KELAMIN' in df_dash:
    st.subheader("Risk per Jenis Kelamin")
    jk_group = df_dash.groupby('JENIS_KELAMIN')['Risk_Score'].mean()
    st.bar_chart(jk_group)

if 'TIPE_NASABAH' in df_dash:
    st.subheader("Risk per Tipe Nasabah")
    tipe_group = df_dash.groupby('TIPE_NASABAH')['Risk_Score'].mean()
    st.bar_chart(tipe_group)
