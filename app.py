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
    "Dashboard ini menampilkan ringkasan agregat dari data yang dianalisis. "
    "Angka menunjukkan jumlah catatan dalam dataset, bukan jaminan jumlah "
    "seluruh transaksi servis yang terjadi. Status merupakan status tindak "
    "lanjut yang tercatat dan tidak otomatis membuktikan servis telah selesai."
)

# =========================================================
# 2. MEMUAT DATA AGREGAT
# =========================================================
@st.cache_data
def load_data(path):
    data = pd.read_csv(path, encoding="utf-8-sig")

    kolom_wajib = {
        "JENIS_ANALISIS",
        "DIMENSI_1",
        "DIMENSI_2",
        "JUMLAH_CATATAN"
    }

    if not kolom_wajib.issubset(data.columns):
        raise ValueError(
            "Struktur CSV tidak sesuai. Periksa kolom dataset agregat."
        )

    data["JENIS_ANALISIS"] = data["JENIS_ANALISIS"].astype(str)
    data["DIMENSI_1"] = data["DIMENSI_1"].fillna("").astype(str)
    data["DIMENSI_2"] = data["DIMENSI_2"].fillna("").astype(str)
    data["JUMLAH_CATATAN"] = pd.to_numeric(
        data["JUMLAH_CATATAN"], errors="coerce"
    ).fillna(0)

    return data


try:
    df = load_data(FILE_DATA)
except Exception as e:
    st.error(
        "Dataset agregat belum dapat dibaca. Pastikan file "
        "'data_dashboard_agregat.csv' berada di folder yang sama dengan app.py."
    )
    st.exception(e)
    st.stop()

# =========================================================
# 3. MEMISAHKAN RINGKASAN BERDASARKAN JENIS ANALISIS
# =========================================================
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

# =========================================================
# 4. FILTER BULAN
# =========================================================
st.sidebar.header("Filter Dashboard")

daftar_bulan = sorted(df_bulan["DIMENSI_1"].unique().tolist())

if daftar_bulan:
    pilihan_bulan = st.sidebar.selectbox(
        "Pilih bulan untuk melihat ringkasan tren",
        options=["Semua bulan"] + daftar_bulan,
        index=0
    )
else:
    pilihan_bulan = "Semua bulan"

st.sidebar.caption(
    "Filter bulan diterapkan pada grafik tren bulanan dan grafik tren "
    "model/kategori. Grafik distribusi keseluruhan menampilkan ringkasan "
    "dari periode yang tersedia."
)

# =========================================================
# 5. KPI RINGKASAN
# =========================================================
total_bulan = df_bulan["DIMENSI_1"].nunique()
jumlah_model = df_model["DIMENSI_1"].nunique()
jumlah_kategori = df_kategori["DIMENSI_1"].nunique()

if not df_bulan.empty:
    bulan_tertinggi = df_bulan.loc[
        df_bulan["JUMLAH_CATATAN"].idxmax()
    ]
    label_bulan_tertinggi = bulan_tertinggi["DIMENSI_1"]
    nilai_bulan_tertinggi = int(bulan_tertinggi["JUMLAH_CATATAN"])
else:
    label_bulan_tertinggi = "-"
    nilai_bulan_tertinggi = 0

k1, k2, k3, k4 = st.columns(4)

k1.metric("Bulan dengan Catatan", total_bulan)
k2.metric("Model yang Ditampilkan", jumlah_model)
k3.metric("Kategori yang Ditampilkan", jumlah_kategori)
k4.metric(
    "Bulan dengan Catatan Terbanyak",
    label_bulan_tertinggi,
    f"{nilai_bulan_tertinggi} catatan"
)

st.divider()

# =========================================================
# 6. TREN BULANAN
# =========================================================
st.header("1. Analisis Tren Bulanan")

data_tren = df_bulan.copy().sort_values("DIMENSI_1")

if pilihan_bulan != "Semua bulan":
    data_tren = data_tren[
        data_tren["DIMENSI_1"] == pilihan_bulan
    ]

if not data_tren.empty:
    fig_tren = px.line(
        data_tren,
        x="DIMENSI_1",
        y="JUMLAH_CATATAN",
        markers=True,
        title="Tren Catatan Servis Berdasarkan Bulan",
        labels={
            "DIMENSI_1": "Bulan",
            "JUMLAH_CATATAN": "Jumlah Catatan"
        }
    )
    fig_tren.update_layout(xaxis_title="Bulan", yaxis_title="Jumlah Catatan")
    st.plotly_chart(fig_tren, use_container_width=True)
else:
    st.warning("Tidak ada data tren untuk pilihan bulan tersebut.")

st.caption(
    "Bulan yang tidak tampil pada ringkasan dapat memiliki nol catatan "
    "bertanggal valid. Hal ini tidak membuktikan bahwa tidak ada aktivitas servis."
)

# =========================================================
# 7. DISTRIBUSI MODEL DAN KATEGORI
# =========================================================
st.header("2. Distribusi Model Kendaraan dan Kategori Servis")

kolom_kiri, kolom_kanan = st.columns(2)

with kolom_kiri:
    if not df_model.empty:
        top_model = (
            df_model.sort_values("JUMLAH_CATATAN", ascending=False)
            .head(10)
        )

        fig_model = px.bar(
            top_model.sort_values("JUMLAH_CATATAN"),
            x="JUMLAH_CATATAN",
            y="DIMENSI_1",
            orientation="h",
            title="10 Model Kendaraan dengan Catatan Terbanyak",
            labels={
                "DIMENSI_1": "Model Kendaraan",
                "JUMLAH_CATATAN": "Jumlah Catatan"
            }
        )
        st.plotly_chart(fig_model, use_container_width=True)
    else:
        st.warning("Ringkasan model kendaraan tidak tersedia.")

with kolom_kanan:
    if not df_kategori.empty:
        top_kategori = (
            df_kategori.sort_values("JUMLAH_CATATAN", ascending=False)
            .head(10)
        )

        fig_kategori = px.bar(
            top_kategori.sort_values("JUMLAH_CATATAN"),
            x="JUMLAH_CATATAN",
            y="DIMENSI_1",
            orientation="h",
            title="Kategori Servis dengan Catatan Terbanyak",
            labels={
                "DIMENSI_1": "Kategori Servis",
                "JUMLAH_CATATAN": "Jumlah Catatan"
            }
        )
        st.plotly_chart(fig_kategori, use_container_width=True)
    else:
        st.warning("Ringkasan kategori servis tidak tersedia.")

# =========================================================
# 8. KOMBINASI MODEL DAN KATEGORI
# =========================================================
st.header("3. Analisis Kombinasi Model dan Kategori Servis")

if not df_model_kategori.empty:
    top_kombinasi = (
        df_model_kategori
        .sort_values("JUMLAH_CATATAN", ascending=False)
        .head(10)
        .copy()
    )

    top_kombinasi["KOMBINASI"] = (
        top_kombinasi["DIMENSI_1"]
        + " | "
        + top_kombinasi["DIMENSI_2"]
    )

    fig_kombinasi = px.bar(
        top_kombinasi.sort_values("JUMLAH_CATATAN"),
        x="JUMLAH_CATATAN",
        y="KOMBINASI",
        orientation="h",
        title="10 Kombinasi Model dan Kategori Teratas",
        labels={
            "KOMBINASI": "Model | Kategori Servis",
            "JUMLAH_CATATAN": "Jumlah Catatan"
        }
    )
    st.plotly_chart(fig_kombinasi, use_container_width=True)
else:
    st.warning("Ringkasan kombinasi model dan kategori tidak tersedia.")

# =========================================================
# 9. TREN MODEL PER BULAN
# =========================================================
st.header("4. Tren Model Kendaraan dari Waktu ke Waktu")

if not df_bulan_model.empty:
    data_model_waktu = df_bulan_model.copy()

    if pilihan_bulan != "Semua bulan":
        data_model_waktu = data_model_waktu[
            data_model_waktu["DIMENSI_1"] == pilihan_bulan
        ]

    # Pilih maksimal 5 model berdasarkan jumlah agregat yang tersedia
    model_teratas = (
        df_bulan_model.groupby("DIMENSI_2")["JUMLAH_CATATAN"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .index.tolist()
    )

    data_model_waktu = data_model_waktu[
        data_model_waktu["DIMENSI_2"].isin(model_teratas)
    ]

    if not data_model_waktu.empty:
        fig_model_waktu = px.line(
            data_model_waktu.sort_values("DIMENSI_1"),
            x="DIMENSI_1",
            y="JUMLAH_CATATAN",
            color="DIMENSI_2",
            markers=True,
            title="Tren Bulanan Lima Model Teratas",
            labels={
                "DIMENSI_1": "Bulan",
                "DIMENSI_2": "Model Kendaraan",
                "JUMLAH_CATATAN": "Jumlah Catatan"
            }
        )
        st.plotly_chart(fig_model_waktu, use_container_width=True)
    else:
        st.info("Tidak ada catatan model untuk bulan yang dipilih.")
else:
    st.warning("Ringkasan tren model tidak tersedia.")

# =========================================================
# 10. TREN KATEGORI PER BULAN
# =========================================================
st.header("5. Tren Kategori Servis dari Waktu ke Waktu")

if not df_bulan_kategori.empty:
    data_kategori_waktu = df_bulan_kategori.copy()

    if pilihan_bulan != "Semua bulan":
        data_kategori_waktu = data_kategori_waktu[
            data_kategori_waktu["DIMENSI_1"] == pilihan_bulan
        ]

    kategori_teratas = (
        df_bulan_kategori.groupby("DIMENSI_2")["JUMLAH_CATATAN"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .index.tolist()
    )

    data_kategori_waktu = data_kategori_waktu[
        data_kategori_waktu["DIMENSI_2"].isin(kategori_teratas)
    ]

    if not data_kategori_waktu.empty:
        fig_kategori_waktu = px.line(
            data_kategori_waktu.sort_values("DIMENSI_1"),
            x="DIMENSI_1",
            y="JUMLAH_CATATAN",
            color="DIMENSI_2",
            markers=True,
            title="Tren Bulanan Lima Kategori Servis Teratas",
            labels={
                "DIMENSI_1": "Bulan",
                "DIMENSI_2": "Kategori Servis",
                "JUMLAH_CATATAN": "Jumlah Catatan"
            }
        )
        st.plotly_chart(fig_kategori_waktu, use_container_width=True)
    else:
        st.info("Tidak ada catatan kategori untuk bulan yang dipilih.")
else:
    st.warning("Ringkasan tren kategori tidak tersedia.")

# =========================================================
# 11. PENAWARAN DAN STATUS
# =========================================================
st.header("6. Distribusi Penawaran dan Status Tindak Lanjut")

kolom_kiri, kolom_kanan = st.columns(2)

with kolom_kiri:
    if not df_penawaran.empty:
        fig_penawaran = px.bar(
            df_penawaran.sort_values("JUMLAH_CATATAN", ascending=False),
            x="DIMENSI_1",
            y="JUMLAH_CATATAN",
            title="Distribusi Penawaran",
            labels={
                "DIMENSI_1": "Penawaran",
                "JUMLAH_CATATAN": "Jumlah Catatan"
            }
        )
        fig_penawaran.update_layout(xaxis_tickangle=-35)
        st.plotly_chart(fig_penawaran, use_container_width=True)

with kolom_kanan:
    if not df_status.empty:
        fig_status = px.bar(
            df_status.sort_values("JUMLAH_CATATAN", ascending=False),
            x="DIMENSI_1",
            y="JUMLAH_CATATAN",
            title="Distribusi Status Tindak Lanjut",
            labels={
                "DIMENSI_1": "Status",
                "JUMLAH_CATATAN": "Jumlah Catatan"
            }
        )
        fig_status.update_layout(xaxis_tickangle=-35)
        st.plotly_chart(fig_status, use_container_width=True)

st.divider()

st.caption(
    "Sumber: ringkasan agregat data layanan servis PT Teja Berlian Mitsubishi. "
    "Label kategori, model, penawaran, dan status mengikuti data sumber "
    "yang telah diproses. Kelompok dengan jumlah catatan rendah tidak "
    "ditampilkan pada beberapa analisis."
)

st.caption(
    "Catatan privasi: dashboard hanya menampilkan grafik dan angka agregat; "
    "tidak menyediakan tabel data per baris atau unduhan data mentah."
)
