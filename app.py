
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# =========================================================
# 1. KONFIGURASI DASHBOARD
# =========================================================

st.set_page_config(
    page_title="Dashboard BI Layanan Servis Mitsubishi",
    page_icon="🚗",
    layout="wide"
)

st.title("Dashboard Business Intelligence")
st.subheader(
    "Analisis Tren dan Distribusi Layanan Servis Kendaraan "
    "PT Teja Berlian Mitsubishi"
)

st.markdown(
    """
    Dashboard ini digunakan untuk mengeksplorasi catatan layanan servis
    berdasarkan waktu, model kendaraan, kategori servis, penawaran,
    dan status yang tercatat dalam dataset.
    """
)

# =========================================================
# 2. MEMUAT DATA
# =========================================================

FILE_DATA = Path(__file__).parent / "data_servis_bi.csv"

if not FILE_DATA.exists():
    st.error(
        "File data_servis_bi.csv tidak ditemukan. "
        "Pastikan file CSV sudah diekspor ke folder /content."
    )
    st.stop()


@st.cache_data
def load_data(path):
    data = pd.read_csv(path)

    # Mengubah kolom tanggal menjadi format datetime
    kolom_tanggal = [
        "TANGGALTERAKHIR SERVICE",
        "TANGGAL INPUT DATA"
    ]

    for kolom in kolom_tanggal:
        if kolom in data.columns:
            data[kolom] = pd.to_datetime(
                data[kolom],
                errors="coerce"
            )

    return data


df = load_data(str(FILE_DATA))

# =========================================================
# 3. MENYIAPKAN KOLOM ANALISIS
# =========================================================

kolom_model = (
    "PRODUK UNIT_ANALISIS"
    if "PRODUK UNIT_ANALISIS" in df.columns
    else "PRODUK UNIT"
)

kolom_kategori = (
    "KATEGORI SERVICE_ANALISIS"
    if "KATEGORI SERVICE_ANALISIS" in df.columns
    else "KATEGORI SERVICE"
)

kolom_status = (
    "STATUS_ANALISIS"
    if "STATUS_ANALISIS" in df.columns
    else "STATUS"
)

kolom_penawaran = (
    "PENAWARAN_ANALISIS"
    if "PENAWARAN_ANALISIS" in df.columns
    else "PENAWARAN"
)

kolom_tanggal = "TANGGALTERAKHIR SERVICE"

# Memastikan kolom utama tersedia
kolom_wajib = [
    kolom_model,
    kolom_kategori,
    kolom_status,
    kolom_penawaran,
    kolom_tanggal
]

kolom_tidak_ada = [
    kolom for kolom in kolom_wajib
    if kolom not in df.columns
]

if kolom_tidak_ada:
    st.error(
        "Kolom berikut tidak ditemukan dalam dataset: "
        + ", ".join(kolom_tidak_ada)
    )
    st.stop()

# Membuat salinan khusus untuk dashboard
df_dashboard = df.copy()

# Mengubah nilai kosong menjadi label yang jelas
for kolom in [
    kolom_model,
    kolom_kategori,
    kolom_status,
    kolom_penawaran
]:
    df_dashboard[kolom] = (
        df_dashboard[kolom]
        .astype("string")
        .str.strip()
        .fillna("Tidak diketahui")
    )

    df_dashboard[kolom] = (
        df_dashboard[kolom]
        .replace("", "Tidak diketahui")
    )

# =========================================================
# 4. FILTER DASHBOARD
# =========================================================

st.sidebar.header("Filter Dashboard")

tanggal_valid = df_dashboard[kolom_tanggal].dropna()

if tanggal_valid.empty:
    st.error("Tidak terdapat tanggal servis valid dalam dataset.")
    st.stop()

tanggal_min = tanggal_valid.min().date()
tanggal_max = tanggal_valid.max().date()

rentang_tanggal = st.sidebar.date_input(
    "Rentang tanggal servis",
    value=(tanggal_min, tanggal_max),
    min_value=tanggal_min,
    max_value=tanggal_max
)

# Memastikan rentang tanggal memiliki tanggal awal dan akhir
if isinstance(rentang_tanggal, (tuple, list)):
    if len(rentang_tanggal) == 2:
        tanggal_awal, tanggal_akhir = rentang_tanggal
    elif len(rentang_tanggal) == 1:
        tanggal_awal = rentang_tanggal[0]
        tanggal_akhir = rentang_tanggal[0]
    else:
        tanggal_awal = tanggal_min
        tanggal_akhir = tanggal_max
else:
    tanggal_awal = rentang_tanggal
    tanggal_akhir = rentang_tanggal

if tanggal_awal > tanggal_akhir:
    st.sidebar.warning(
        "Tanggal awal melewati tanggal akhir. "
        "Silakan periksa kembali filter tanggal."
    )
    st.stop()

# Filter model kendaraan
daftar_model = sorted(
    df_dashboard[kolom_model].unique().tolist()
)

pilihan_model = st.sidebar.multiselect(
    "Model kendaraan",
    options=daftar_model,
    default=daftar_model
)

# Filter kategori servis
daftar_kategori = sorted(
    df_dashboard[kolom_kategori].unique().tolist()
)

pilihan_kategori = st.sidebar.multiselect(
    "Kategori servis",
    options=daftar_kategori,
    default=daftar_kategori
)

# Filter status
daftar_status = sorted(
    df_dashboard[kolom_status].unique().tolist()
)

pilihan_status = st.sidebar.multiselect(
    "Status",
    options=daftar_status,
    default=daftar_status
)

# Filter penawaran
daftar_penawaran = sorted(
    df_dashboard[kolom_penawaran].unique().tolist()
)

pilihan_penawaran = st.sidebar.multiselect(
    "Penawaran",
    options=daftar_penawaran,
    default=daftar_penawaran
)

# =========================================================
# 5. MENERAPKAN FILTER
# =========================================================

df_filter = df_dashboard.copy()

df_filter = df_filter[
    df_filter[kolom_tanggal].notna()
    & (
        df_filter[kolom_tanggal].dt.date >= tanggal_awal
    )
    & (
        df_filter[kolom_tanggal].dt.date <= tanggal_akhir
    )
]

df_filter = df_filter[
    df_filter[kolom_model].isin(pilihan_model)
    & df_filter[kolom_kategori].isin(pilihan_kategori)
    & df_filter[kolom_status].isin(pilihan_status)
    & df_filter[kolom_penawaran].isin(pilihan_penawaran)
]

if df_filter.empty:
    st.warning(
        "Tidak ada catatan yang sesuai dengan kombinasi filter. "
        "Silakan ubah pilihan filter pada panel sebelah kiri."
    )
    st.stop()

# =========================================================
# 6. INDIKATOR UTAMA / KPI
# =========================================================

jumlah_catatan = len(df_filter)

jumlah_model = df_filter[kolom_model].nunique()

jumlah_kategori = df_filter[kolom_kategori].nunique()

jumlah_tanggal = df_filter[kolom_tanggal].dt.date.nunique()

tanggal_terawal = df_filter[kolom_tanggal].min().strftime("%d-%m-%Y")

tanggal_terakhir = df_filter[kolom_tanggal].max().strftime("%d-%m-%Y")

st.markdown("### Ringkasan Data")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric(
    "Jumlah Catatan",
    f"{jumlah_catatan:,}".replace(",", ".")
)

kpi2.metric(
    "Model Kendaraan",
    f"{jumlah_model:,}".replace(",", ".")
)

kpi3.metric(
    "Kategori Servis",
    f"{jumlah_kategori:,}".replace(",", ".")
)

kpi4.metric(
    "Tanggal Servis Berbeda",
    f"{jumlah_tanggal:,}".replace(",", ".")
)

st.caption(
    f"Periode catatan yang ditampilkan: {tanggal_terawal} sampai "
    f"{tanggal_terakhir}. Angka menunjukkan catatan dalam dataset, "
    "bukan jumlah kendaraan unik atau bukti seluruh transaksi servis."
)

st.divider()

# =========================================================
# 7. ANALISIS TREN BULANAN
# =========================================================

st.markdown("### 1. Tren Catatan Servis Bulanan")

df_waktu = df_filter.copy()

df_waktu["BULAN"] = (
    df_waktu[kolom_tanggal]
    .dt.to_period("M")
    .astype(str)
)

tren_bulanan = (
    df_waktu.groupby("BULAN")
    .size()
    .reset_index(name="Jumlah Catatan")
    .sort_values("BULAN")
)

fig_tren = px.line(
    tren_bulanan,
    x="BULAN",
    y="Jumlah Catatan",
    markers=True,
    title="Tren Catatan Servis per Bulan",
    labels={
        "BULAN": "Bulan",
        "Jumlah Catatan": "Jumlah Catatan"
    }
)

fig_tren.update_layout(
    xaxis_tickangle=-45,
    hovermode="x unified"
)

st.plotly_chart(fig_tren, use_container_width=True)

st.caption(
    "Interpretasi: grafik menunjukkan perubahan jumlah catatan "
    "berdasarkan bulan tanggal servis yang tercatat. Nilai rendah "
    "atau nol tidak otomatis berarti tidak ada aktivitas servis "
    "di perusahaan."
)

# =========================================================
# 8. DISTRIBUSI MODEL KENDARAAN
# =========================================================

st.markdown("### 2. Distribusi Model Kendaraan")

df_model = df_filter[
    df_filter[kolom_model] != "Tidak diketahui"
]

if not df_model.empty:
    distribusi_model = (
        df_model[kolom_model]
        .value_counts()
        .head(10)
        .reset_index()
    )

    distribusi_model.columns = [
        "Model Kendaraan",
        "Jumlah Catatan"
    ]

    distribusi_model = distribusi_model.sort_values(
        "Jumlah Catatan",
        ascending=True
    )

    fig_model = px.bar(
        distribusi_model,
        x="Jumlah Catatan",
        y="Model Kendaraan",
        orientation="h",
        title="10 Model Kendaraan dengan Catatan Terbanyak",
        labels={
            "Jumlah Catatan": "Jumlah Catatan",
            "Model Kendaraan": "Model Kendaraan"
        }
    )

    st.plotly_chart(fig_model, use_container_width=True)

    with st.expander("Lihat tabel distribusi model kendaraan"):
        tabel_model = (
            df_model[kolom_model]
            .value_counts()
            .rename_axis("Model Kendaraan")
            .reset_index(name="Jumlah Catatan")
        )
        tabel_model["Persentase (%)"] = (
            tabel_model["Jumlah Catatan"]
            / len(df_model)
            * 100
        ).round(2)

        st.dataframe(tabel_model, use_container_width=True)
else:
    st.info("Tidak ada model kendaraan yang diketahui pada filter ini.")

# =========================================================
# 9. DISTRIBUSI KATEGORI SERVIS
# =========================================================

st.markdown("### 3. Distribusi Kategori Servis")

df_kategori = df_filter[
    df_filter[kolom_kategori] != "Tidak diketahui"
]

if not df_kategori.empty:
    distribusi_kategori = (
        df_kategori[kolom_kategori]
        .value_counts()
        .head(10)
        .reset_index()
    )

    distribusi_kategori.columns = [
        "Kategori Servis",
        "Jumlah Catatan"
    ]

    distribusi_kategori = distribusi_kategori.sort_values(
        "Jumlah Catatan",
        ascending=True
    )

    fig_kategori = px.bar(
        distribusi_kategori,
        x="Jumlah Catatan",
        y="Kategori Servis",
        orientation="h",
        title="10 Kategori Servis dengan Catatan Terbanyak",
        labels={
            "Jumlah Catatan": "Jumlah Catatan",
            "Kategori Servis": "Kategori Servis"
        }
    )

    st.plotly_chart(fig_kategori, use_container_width=True)

    with st.expander("Lihat tabel distribusi kategori servis"):
        tabel_kategori = (
            df_kategori[kolom_kategori]
            .value_counts()
            .rename_axis("Kategori Servis")
            .reset_index(name="Jumlah Catatan")
        )

        tabel_kategori["Persentase (%)"] = (
            tabel_kategori["Jumlah Catatan"]
            / len(df_kategori)
            * 100
        ).round(2)

        st.dataframe(tabel_kategori, use_container_width=True)
else:
    st.info("Tidak ada kategori servis yang diketahui pada filter ini.")

# =========================================================
# 10. HUBUNGAN MODEL KENDARAAN DAN KATEGORI SERVIS
# =========================================================

st.markdown("### 4. Hubungan Model Kendaraan dan Kategori Servis")

df_gabungan = df_filter[
    (df_filter[kolom_model] != "Tidak diketahui")
    & (df_filter[kolom_kategori] != "Tidak diketahui")
]

if not df_gabungan.empty:
    tabel_gabungan = pd.crosstab(
        df_gabungan[kolom_model],
        df_gabungan[kolom_kategori]
    )

    st.markdown(
        "Pilih model kendaraan dan kategori servis untuk "
        "mengeksplorasi pola catatan layanan."
    )

    model_heatmap = st.selectbox(
        "Pilih model kendaraan untuk analisis kategori",
        options=sorted(df_gabungan[kolom_model].unique())
    )

    data_model_kategori = (
        df_gabungan[
            df_gabungan[kolom_model] == model_heatmap
        ][kolom_kategori]
        .value_counts()
        .head(10)
        .reset_index()
    )

    data_model_kategori.columns = [
        "Kategori Servis",
        "Jumlah Catatan"
    ]

    fig_model_kategori = px.bar(
        data_model_kategori,
        x="Kategori Servis",
        y="Jumlah Catatan",
        title=f"Kategori Servis pada Model: {model_heatmap}",
        labels={
            "Kategori Servis": "Kategori Servis",
            "Jumlah Catatan": "Jumlah Catatan"
        }
    )

    fig_model_kategori.update_layout(xaxis_tickangle=-35)

    st.plotly_chart(
        fig_model_kategori,
        use_container_width=True
    )

    with st.expander("Lihat tabel silang model dan kategori servis"):
        st.dataframe(tabel_gabungan, use_container_width=True)
else:
    st.info(
        "Belum ada data dengan model kendaraan dan kategori servis "
        "yang terisi secara bersamaan."
    )

# =========================================================
# 11. DISTRIBUSI STATUS
# =========================================================

st.markdown("### 5. Distribusi Status")

df_status = df_filter[
    df_filter[kolom_status] != "Tidak diketahui"
]

if not df_status.empty:
    distribusi_status = (
        df_status[kolom_status]
        .value_counts()
        .head(10)
        .reset_index()
    )

    distribusi_status.columns = [
        "Status",
        "Jumlah Catatan"
    ]

    fig_status = px.bar(
        distribusi_status,
        x="Jumlah Catatan",
        y="Status",
        orientation="h",
        title="10 Status dengan Catatan Terbanyak",
        labels={
            "Jumlah Catatan": "Jumlah Catatan",
            "Status": "Status"
        }
    )

    st.plotly_chart(fig_status, use_container_width=True)
else:
    st.info("Tidak ada status yang diketahui pada filter ini.")

st.caption(
    "Status ditampilkan sebagai informasi yang tercatat dalam dataset. "
    "Status seperti pengingat atau bisa dihubungi tidak ditafsirkan "
    "sebagai bukti bahwa servis telah selesai."
)

# =========================================================
# 12. TABEL DATA HASIL FILTER
# =========================================================

st.markdown("### 6. Data Berdasarkan Filter")

kolom_tampil = [
    "TANGGALTERAKHIR SERVICE",
    "PRODUK UNIT",
    "KATEGORI SERVICE",
    "PENAWARAN",
    "STATUS"
]

kolom_tampil = [
    kolom for kolom in kolom_tampil
    if kolom in df_filter.columns
]

st.dataframe(
    df_filter[kolom_tampil].sort_values(
        by=kolom_tanggal,
        ascending=False
    ),
    use_container_width=True,
    hide_index=True
)

# =========================================================
# 13. UNDUH DATA HASIL FILTER
# =========================================================

csv_unduhan = df_filter[kolom_tampil].to_csv(
    index=False
).encode("utf-8-sig")

st.download_button(
    label="Unduh Data Hasil Filter (CSV)",
    data=csv_unduhan,
    file_name="data_servis_hasil_filter.csv",
    mime="text/csv"
)

st.divider()

st.caption(
    "Dashboard dibuat untuk mendukung eksplorasi dan analisis "
    "deskriptif data layanan servis PT Teja Berlian Mitsubishi."
)
