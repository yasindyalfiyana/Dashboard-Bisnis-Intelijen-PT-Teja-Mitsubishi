import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# =========================================================
# 1. KONFIGURASI HALAMAN
# =========================================================
st.set_page_config(
    page_title="Dashboard BI - PT Teja Berlian Mitsubishi",
    page_icon="📊",
    layout="wide"
)

FILE_DATA = Path(__file__).parent / "data_dashboard_agregat.csv"

st.title("Dashboard Business Intelligence")
st.subheader("Analisis Tren dan Distribusi Layanan Servis Kendaraan")
st.caption("Studi Kasus: PT Teja Berlian Mitsubishi")

st.info(
    "Dashboard menampilkan ringkasan agregat dari data yang memiliki tanggal "
    "servis valid. Angka menunjukkan jumlah catatan dalam dataset, bukan "
    "jaminan jumlah seluruh transaksi servis yang terjadi. Status merupakan "
    "status tindak lanjut yang tercatat dan tidak otomatis membuktikan servis selesai."
)

# =========================================================
# 2. MEMUAT DATA AGREGAT
# =========================================================
@st.cache_data
def load_data(path):
    data = pd.read_csv(path, encoding="utf-8-sig")
    required = {"JENIS_ANALISIS", "DIMENSI_1", "DIMENSI_2", "JUMLAH_CATATAN"}
    if not required.issubset(data.columns):
        raise ValueError("Struktur CSV tidak sesuai. Periksa kolom dataset agregat.")
    for col in ["JENIS_ANALISIS", "DIMENSI_1", "DIMENSI_2"]:
        data[col] = data[col].fillna("").astype(str).str.strip()
    data["JUMLAH_CATATAN"] = pd.to_numeric(data["JUMLAH_CATATAN"], errors="coerce").fillna(0)
    return data

try:
    df = load_data(FILE_DATA)
except Exception as e:
    st.error("Dataset agregat belum dapat dibaca. Pastikan 'data_dashboard_agregat.csv' berada di folder yang sama dengan app.py.")
    st.exception(e)
    st.stop()

def ambil_data(jenis):
    return df[df["JENIS_ANALISIS"] == jenis].copy()

df_bulan = ambil_data("BULAN")
df_model = ambil_data("MODEL")
df_kategori = ambil_data("KATEGORI")
df_penawaran = ambil_data("PENAWARAN")
df_status = ambil_data("STATUS")
df_model_kategori = ambil_data("MODEL_KATEGORI")
df_bulan_kategori = ambil_data("BULAN_KATEGORI")
df_bulan_model = ambil_data("BULAN_MODEL")
df_bulan_model_kategori = ambil_data("BULAN_MODEL_KATEGORI")

# =========================================================
# 3. FILTER SIDEBAR
# =========================================================
st.sidebar.header("Filter Dashboard")

daftar_bulan = sorted(df_bulan["DIMENSI_1"].unique().tolist())
daftar_model = sorted(df_model["DIMENSI_1"].unique().tolist())
daftar_kategori = sorted(df_kategori["DIMENSI_1"].unique().tolist())

pilihan_bulan = st.sidebar.selectbox(
    "Bulan servis",
    ["Semua bulan"] + daftar_bulan,
    index=0
)
pilihan_model = st.sidebar.multiselect(
    "Model kendaraan",
    options=daftar_model,
    default=[],
    help="Kosongkan pilihan untuk menampilkan semua model."
)
pilihan_kategori = st.sidebar.multiselect(
    "Kategori servis",
    options=daftar_kategori,
    default=[],
    help="Kosongkan pilihan untuk menampilkan semua kategori."
)
st.sidebar.caption("Filter memengaruhi grafik tren dan distribusi yang memiliki rincian dimensi terkait. Ringkasan penawaran dan status tetap menggambarkan keseluruhan data bertanggal valid.")

# Normalize empty selections to 'all'
model_filter = pilihan_model if pilihan_model else None
kategori_filter = pilihan_kategori if pilihan_kategori else None
bulan_filter = pilihan_bulan if pilihan_bulan != "Semua bulan" else None

# =========================================================
# 4. SIAPKAN DATA UNTUK FILTER
# =========================================================
# BULAN_MODEL_KATEGORI stores DIMENSI_2 as "model ||| kategori".
if not df_bulan_model_kategori.empty:
    detail = df_bulan_model_kategori.copy()
    split_cols = detail["DIMENSI_2"].str.split(" ||| ", n=1, expand=True, regex=False)
    detail["MODEL"] = split_cols[0].fillna("")
    detail["KATEGORI"] = split_cols[1].fillna("")
else:
    detail = pd.DataFrame(columns=["DIMENSI_1", "MODEL", "KATEGORI", "JUMLAH_CATATAN"])

filtered_detail = detail.copy()
if bulan_filter:
    filtered_detail = filtered_detail[filtered_detail["DIMENSI_1"] == bulan_filter]
if model_filter:
    filtered_detail = filtered_detail[filtered_detail["MODEL"].isin(model_filter)]
if kategori_filter:
    filtered_detail = filtered_detail[filtered_detail["KATEGORI"].isin(kategori_filter)]

# Summary totals use the detailed combination table when any of the three filters is active.
dimension_filter_active = bool(model_filter or kategori_filter)
filters_active = bool(bulan_filter or model_filter or kategori_filter)

if dimension_filter_active:
    kpi_total = int(filtered_detail["JUMLAH_CATATAN"].sum())
    kpi_models = int(filtered_detail["MODEL"].nunique())
    kpi_categories = int(filtered_detail["KATEGORI"].nunique())
    if not filtered_detail.empty:
        monthly_counts = filtered_detail.groupby("DIMENSI_1", as_index=False)["JUMLAH_CATATAN"].sum()
        peak = monthly_counts.loc[monthly_counts["JUMLAH_CATATAN"].idxmax()]
        peak_month, peak_count = peak["DIMENSI_1"], int(peak["JUMLAH_CATATAN"])
    else:
        peak_month, peak_count = "-", 0
elif bulan_filter:
    month_row = df_bulan[df_bulan["DIMENSI_1"] == bulan_filter]
    kpi_total = int(month_row["JUMLAH_CATATAN"].sum())
    model_month = df_bulan_model[df_bulan_model["DIMENSI_1"] == bulan_filter]
    category_month = df_bulan_kategori[df_bulan_kategori["DIMENSI_1"] == bulan_filter]
    kpi_models = int(model_month["DIMENSI_2"].nunique())
    kpi_categories = int(category_month["DIMENSI_2"].nunique())
    peak_month, peak_count = bulan_filter, kpi_total
else:
    kpi_total = int(df_bulan["JUMLAH_CATATAN"].sum())
    kpi_models = int(df_model["DIMENSI_1"].nunique())
    kpi_categories = int(df_kategori["DIMENSI_1"].nunique())
    if not df_bulan.empty:
        peak = df_bulan.loc[df_bulan["JUMLAH_CATATAN"].idxmax()]
        peak_month, peak_count = peak["DIMENSI_1"], int(peak["JUMLAH_CATATAN"])
    else:
        peak_month, peak_count = "-", 0

# =========================================================
# 5. KPI
# =========================================================
k1, k2, k3, k4 = st.columns(4)
k1.metric("Jumlah Catatan Terpilih", f"{kpi_total:,}")
k2.metric("Model Kendaraan", kpi_models)
k3.metric("Kategori Servis", kpi_categories)
k4.metric("Bulan Terbanyak", peak_month, f"{peak_count:,} catatan")
st.divider()

# =========================================================
# 6. TREN BULANAN
# =========================================================
st.header("1. Analisis Tren Bulanan")
if dimension_filter_active:
    data_tren = filtered_detail.groupby("DIMENSI_1", as_index=False)["JUMLAH_CATATAN"].sum()
else:
    data_tren = df_bulan[["DIMENSI_1", "JUMLAH_CATATAN"]].copy()
if bulan_filter:
    data_tren = data_tren[data_tren["DIMENSI_1"] == bulan_filter]
data_tren = data_tren.sort_values("DIMENSI_1")
if not data_tren.empty:
    fig = px.line(data_tren, x="DIMENSI_1", y="JUMLAH_CATATAN", markers=True,
                  title="Tren Catatan Servis Berdasarkan Bulan",
                  labels={"DIMENSI_1":"Bulan", "JUMLAH_CATATAN":"Jumlah Catatan"})
    fig.update_layout(xaxis_title="Bulan", yaxis_title="Jumlah Catatan")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Tidak ada catatan yang sesuai dengan kombinasi filter yang dipilih.")

# =========================================================
# 7. DISTRIBUSI MODEL DAN KATEGORI
# =========================================================
st.header("2. Distribusi Model Kendaraan dan Kategori Servis")
left, right = st.columns(2)

with left:
    if dimension_filter_active:
        model_dist = filtered_detail.groupby("MODEL", as_index=False)["JUMLAH_CATATAN"].sum()
        model_dist = model_dist.rename(columns={"MODEL":"DIMENSI_1"})
    elif bulan_filter:
        model_dist = df_bulan_model[df_bulan_model["DIMENSI_1"] == bulan_filter].groupby("DIMENSI_2", as_index=False)["JUMLAH_CATATAN"].sum()
        model_dist = model_dist.rename(columns={"DIMENSI_2":"DIMENSI_1"})
    else:
        model_dist = df_model[["DIMENSI_1", "JUMLAH_CATATAN"]].copy()
    if model_filter:
        model_dist = model_dist[model_dist["DIMENSI_1"].isin(model_filter)]
    if not model_dist.empty:
        top = model_dist.sort_values("JUMLAH_CATATAN", ascending=False).head(10)
        fig = px.bar(top.sort_values("JUMLAH_CATATAN"), x="JUMLAH_CATATAN", y="DIMENSI_1",
                     orientation="h", title="Model Kendaraan dengan Catatan Terbanyak",
                     labels={"DIMENSI_1":"Model Kendaraan", "JUMLAH_CATATAN":"Jumlah Catatan"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Tidak ada model yang sesuai dengan filter.")

with right:
    if dimension_filter_active:
        category_dist = filtered_detail.groupby("KATEGORI", as_index=False)["JUMLAH_CATATAN"].sum()
        category_dist = category_dist.rename(columns={"KATEGORI":"DIMENSI_1"})
    elif bulan_filter:
        category_dist = df_bulan_kategori[df_bulan_kategori["DIMENSI_1"] == bulan_filter].groupby("DIMENSI_2", as_index=False)["JUMLAH_CATATAN"].sum()
        category_dist = category_dist.rename(columns={"DIMENSI_2":"DIMENSI_1"})
    else:
        category_dist = df_kategori[["DIMENSI_1", "JUMLAH_CATATAN"]].copy()
    if kategori_filter:
        category_dist = category_dist[category_dist["DIMENSI_1"].isin(kategori_filter)]
    if not category_dist.empty:
        top = category_dist.sort_values("JUMLAH_CATATAN", ascending=False).head(10)
        fig = px.bar(top.sort_values("JUMLAH_CATATAN"), x="JUMLAH_CATATAN", y="DIMENSI_1",
                     orientation="h", title="Kategori Servis dengan Catatan Terbanyak",
                     labels={"DIMENSI_1":"Kategori Servis", "JUMLAH_CATATAN":"Jumlah Catatan"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Tidak ada kategori servis yang sesuai dengan filter.")

# =========================================================
# 8. KOMBINASI MODEL DAN KATEGORI
# =========================================================
st.header("3. Analisis Kombinasi Model dan Kategori Servis")
if dimension_filter_active:
    combo = filtered_detail.groupby(["MODEL","KATEGORI"], as_index=False)["JUMLAH_CATATAN"].sum()
    combo["KOMBINASI"] = combo["MODEL"] + " | " + combo["KATEGORI"]
elif bulan_filter:
    combo = detail[detail["DIMENSI_1"] == bulan_filter].groupby(["MODEL","KATEGORI"], as_index=False)["JUMLAH_CATATAN"].sum()
    combo["KOMBINASI"] = combo["MODEL"] + " | " + combo["KATEGORI"]
else:
    combo = df_model_kategori.copy()
    combo["KOMBINASI"] = combo["DIMENSI_1"] + " | " + combo["DIMENSI_2"]
if not combo.empty:
    top = combo.sort_values("JUMLAH_CATATAN", ascending=False).head(10)
    fig = px.bar(top.sort_values("JUMLAH_CATATAN"), x="JUMLAH_CATATAN", y="KOMBINASI",
                 orientation="h", title="10 Kombinasi Model dan Kategori Teratas",
                 labels={"KOMBINASI":"Model | Kategori Servis", "JUMLAH_CATATAN":"Jumlah Catatan"})
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Tidak ada kombinasi model dan kategori yang sesuai dengan filter.")

# =========================================================
# 9. TREN MODEL PER BULAN
# =========================================================
st.header("4. Tren Model Kendaraan dari Waktu ke Waktu")
if dimension_filter_active:
    model_time = filtered_detail.groupby(["DIMENSI_1","MODEL"], as_index=False)["JUMLAH_CATATAN"].sum()
    model_time = model_time.rename(columns={"MODEL":"DIMENSI_2"})
else:
    model_time = df_bulan_model.copy()
if model_filter:
    model_time = model_time[model_time["DIMENSI_2"].isin(model_filter)]
if bulan_filter:
    model_time = model_time[model_time["DIMENSI_1"] == bulan_filter]
if not model_time.empty:
    if not model_filter:
        top_models = model_time.groupby("DIMENSI_2")["JUMLAH_CATATAN"].sum().nlargest(5).index.tolist()
        model_time = model_time[model_time["DIMENSI_2"].isin(top_models)]
    fig = px.line(model_time.sort_values("DIMENSI_1"), x="DIMENSI_1", y="JUMLAH_CATATAN",
                  color="DIMENSI_2", markers=True, title="Tren Bulanan Model Kendaraan",
                  labels={"DIMENSI_1":"Bulan", "DIMENSI_2":"Model Kendaraan", "JUMLAH_CATATAN":"Jumlah Catatan"})
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Tidak ada data tren model untuk filter yang dipilih.")

# =========================================================
# 10. TREN KATEGORI PER BULAN
# =========================================================
st.header("5. Tren Kategori Servis dari Waktu ke Waktu")
if dimension_filter_active:
    category_time = filtered_detail.groupby(["DIMENSI_1","KATEGORI"], as_index=False)["JUMLAH_CATATAN"].sum()
    category_time = category_time.rename(columns={"KATEGORI":"DIMENSI_2"})
else:
    category_time = df_bulan_kategori.copy()
if kategori_filter:
    category_time = category_time[category_time["DIMENSI_2"].isin(kategori_filter)]
if bulan_filter:
    category_time = category_time[category_time["DIMENSI_1"] == bulan_filter]
if not category_time.empty:
    if not kategori_filter:
        top_categories = category_time.groupby("DIMENSI_2")["JUMLAH_CATATAN"].sum().nlargest(5).index.tolist()
        category_time = category_time[category_time["DIMENSI_2"].isin(top_categories)]
    fig = px.line(category_time.sort_values("DIMENSI_1"), x="DIMENSI_1", y="JUMLAH_CATATAN",
                  color="DIMENSI_2", markers=True, title="Tren Bulanan Kategori Servis",
                  labels={"DIMENSI_1":"Bulan", "DIMENSI_2":"Kategori Servis", "JUMLAH_CATATAN":"Jumlah Catatan"})
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Tidak ada data tren kategori untuk filter yang dipilih.")

# =========================================================
# 11. PENAWARAN DAN STATUS
# =========================================================
st.header("6. Distribusi Penawaran dan Status Tindak Lanjut")
left, right = st.columns(2)
with left:
    if not df_penawaran.empty:
        fig = px.bar(df_penawaran.sort_values("JUMLAH_CATATAN", ascending=False),
                     x="DIMENSI_1", y="JUMLAH_CATATAN", title="Distribusi Penawaran",
                     labels={"DIMENSI_1":"Penawaran", "JUMLAH_CATATAN":"Jumlah Catatan"})
        fig.update_layout(xaxis_tickangle=-35)
        st.plotly_chart(fig, use_container_width=True)
with right:
    if not df_status.empty:
        fig = px.bar(df_status.sort_values("JUMLAH_CATATAN", ascending=False),
                     x="DIMENSI_1", y="JUMLAH_CATATAN", title="Distribusi Status Tindak Lanjut",
                     labels={"DIMENSI_1":"Status", "JUMLAH_CATATAN":"Jumlah Catatan"})
        fig.update_layout(xaxis_tickangle=-35)
        st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption(
    "Sumber: data olahan layanan servis PT Teja Berlian Mitsubishi. "
    "Analisis menggunakan catatan yang memiliki tanggal servis valid. "
    "Label mengikuti data hasil pengolahan."
)
st.caption(
    "Catatan privasi: dashboard hanya menampilkan grafik dan angka agregat; "
    "tidak menyediakan tabel data per baris atau unduhan data mentah."
)
