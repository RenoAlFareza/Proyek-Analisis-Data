import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Konfigurasi Halaman
st.set_page_config(
    page_title="E-Commerce Olist Dashboard",
    page_icon="🛒",
    layout="wide"
)

# Load Data
@st.cache_data
def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "main_data.csv")
    df = pd.read_csv(file_path)
    datetime_cols = ["order_purchase_timestamp", "order_delivered_customer_date", "order_estimated_delivery_date"]
    for col in datetime_cols:
        df[col] = pd.to_datetime(df[col])
    return df

try:
    main_df = load_data()
except FileNotFoundError:
    st.error("File main_data.csv tidak ditemukan. Pastikan Anda menjalankan dari direktori submission/dashboard/")
    st.stop()

# Menambahkan CSS Kustom
st.markdown("""
<style>
    .main-title {
        text-align: center;
        font-size: 3rem;
        font-weight: 700;
        color: #1F77B4;
        margin-bottom: 30px;
    }
    .metric-card {
        background-color: #2b323c;
        border: 1px solid #4a5462;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        color: #FFFFFF;
    }
</style>
""", unsafe_allow_html=True)

# Judul Dashboard
st.markdown('<div class="main-title">🛒 Olist E-Commerce Interactive Dashboard</div>', unsafe_allow_html=True)

# =========================================================
# SIDEBAR & FILTER INTERAKTIF
# =========================================================
with st.sidebar:
    st.image("https://github.com/dicodingacademy/assets/raw/main/logo.png", width=200)
    st.title("Filter Data")
    
    # Menentukan batas rentang tanggal dari dataset
    min_date = main_df["order_purchase_timestamp"].min().date()
    max_date = main_df["order_purchase_timestamp"].max().date()
    
    # 1. Filter Rentang Waktu (Slider)
    st.subheader("📅 Rentang Waktu")
    date_range = st.slider(
        label="Geser untuk memilih tanggal",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="YYYY-MM-DD"
    )
    
    # Ekstrak nilai start dan end dari tuple slider
    start_date, end_date = date_range
    
    # 2. Filter Demografi Negara Bagian (Multiselect)
    st.subheader("🌎 Negara Bagian (State)")
    all_states = sorted(main_df["customer_state"].dropna().unique())
    selected_states = st.multiselect(
        label="Pilih Negara Bagian",
        options=all_states,
        default=all_states, # Defaultnya memilih semua
        help="Kosongkan untuk menghapus semua filter state."
    )
    
    st.markdown("---")
    st.write("**Oleh:** Reno Alfa Reza")

# =========================================================
# MENERAPKAN FILTER (GLOBAL)
# =========================================================
# Memastikan rentang tanggal difilter dengan benar (mengubah ke datetime)
start_dt = pd.to_datetime(start_date)
# end_date ditambah 1 hari agar mencakup seluruh transaksi di hari terakhir tersebut
end_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1) 

filtered_df = main_df[
    (main_df["order_purchase_timestamp"] >= start_dt) & 
    (main_df["order_purchase_timestamp"] < end_dt)
]

if selected_states:
    filtered_df = filtered_df[filtered_df["customer_state"].isin(selected_states)]

# Validasi jika data kosong setelah difilter
if filtered_df.empty:
    st.warning("Data tidak ditemukan untuk rentang tanggal dan negara bagian yang dipilih. Silakan ubah filter Anda.")
    st.stop()


# =========================================================
# 1. RINGKASAN METRIK & TREN (BUSINESS OVERVIEW)
# =========================================================
st.header("1. Ringkasan Bisnis & Performa")

# Metrik Utama
total_orders = filtered_df["order_id"].nunique()
total_revenue = filtered_df["price"].sum()
avg_review = filtered_df["review_score"].mean()

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f'<div class="metric-card"><h2>📦 Total Pesanan</h2><h1>{total_orders:,}</h1></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><h2>💰 Total GMV (BRL)</h2><h1>R$ {total_revenue:,.2f}</h1></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><h2>⭐ Rata-rata Ulasan</h2><h1>{avg_review:.2f} / 5.0</h1></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Tren Pendapatan & Top States
col_trend, col_demo = st.columns([2, 1])

with col_trend:
    st.subheader("📈 Tren Pendapatan Bulanan (GMV)")
    filtered_df["year_month"] = filtered_df["order_purchase_timestamp"].dt.to_period("M").astype(str)
    monthly_revenue = filtered_df.groupby("year_month")["price"].sum().reset_index()
    
    fig_line, ax_line = plt.subplots(figsize=(10, 5))
    sns.lineplot(x="year_month", y="price", data=monthly_revenue, marker="o", color="#1F77B4", linewidth=2.5, ax=ax_line)
    ax_line.set_xlabel("Bulan")
    ax_line.set_ylabel("Total Pendapatan (BRL)")
    plt.xticks(rotation=45)
    sns.despine()
    st.pyplot(fig_line)

with col_demo:
    st.subheader("🌎 Top 5 Negara Bagian")
    top_states_df = filtered_df["customer_state"].value_counts().head(5).reset_index()
    top_states_df.columns = ["State", "Jumlah Transaksi"]
    
    fig_bar, ax_bar = plt.subplots(figsize=(5, 5))
    sns.barplot(x="State", y="Jumlah Transaksi", data=top_states_df, palette="Blues_r", ax=ax_bar)
    ax_bar.set_xlabel("Negara Bagian")
    ax_bar.set_ylabel("Transaksi")
    sns.despine()
    st.pyplot(fig_bar)


st.markdown("---")

# =========================================================
# 2. ANALISIS PENGARUH KETERLAMBATAN & KATEGORI TOP
# =========================================================
st.header("2. Dampak Keterlambatan & Kategori Produk Top")

col_late, col_cat = st.columns(2)

with col_late:
    st.subheader("Pengaruh Keterlambatan Pengiriman")
    late_df = filtered_df.copy()
    late_df["delivery_status"] = "Tepat Waktu"
    late_df.loc[late_df["order_delivered_customer_date"] > late_df["order_estimated_delivery_date"], "delivery_status"] = "Terlambat"
    
    eda_1 = late_df.groupby("delivery_status")["review_score"].mean().reset_index()
    
    fig_late, ax_late = plt.subplots(figsize=(8, 5))
    colors_1 = ["#D3D3D3", "#D9534F"]
    sns.barplot(x="delivery_status", y="review_score", data=eda_1, palette=colors_1, ax=ax_late)
    ax_late.set_ylim(0, 5)
    ax_late.set_xlabel("")
    ax_late.set_ylabel("Rata-rata Skor Ulasan (1-5)")
    for index, row in eda_1.iterrows():
        ax_late.text(index, row["review_score"] + 0.1, f'{row["review_score"]:.2f}', color='black', ha="center", fontsize=12)
    sns.despine()
    st.pyplot(fig_late)
    
with col_cat:
    st.subheader("5 Kategori Produk Top (Berdasarkan Filter)")
    gmv_category = filtered_df.groupby("product_category_name_english")["price"].sum().reset_index()
    total_gmv_filtered = gmv_category["price"].sum()
    
    top_5 = gmv_category.sort_values(by="price", ascending=False).head(5).copy()
    top_5["persentase(%)"] = (top_5["price"] / total_gmv_filtered) * 100
    
    fig_cat, ax_cat = plt.subplots(figsize=(8, 5))
    colors_2 = ["#1F77B4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
    sns.barplot(x="price", y="product_category_name_english", data=top_5, palette=colors_2, ax=ax_cat)
    ax_cat.set_xlabel("Total GMV (BRL)")
    ax_cat.set_ylabel("")
    for index, row in top_5.reset_index(drop=True).iterrows():
        ax_cat.text(row["price"] + 2000, index, f'{row["persentase(%)"]:.1f}%', color='black', va="center", fontsize=11)
    sns.despine()
    st.pyplot(fig_cat)

st.markdown("---")

# =========================================================
# 3. ANALISIS METODE PEMBAYARAN
# =========================================================
st.header("3. Analisis Metode Pembayaran vs Ukuran Keranjang (AOV)")

def classify_payment(row):
    if row["payment_type"] == "credit_card" and row["payment_installments"] > 3:
        return "Kartu Kredit (>3 Bulan)"
    elif row["payment_type"] in ["boleto", "debit_card"]:
        return "Lunas (Boleto/Debit)"
    else:
        return "Lainnya"
        
pay_df = filtered_df.copy()
if not pay_df.empty:
    pay_df["tipe_bayar"] = pay_df.apply(classify_payment, axis=1)
    filtered_pay = pay_df[pay_df["tipe_bayar"].isin(["Kartu Kredit (>3 Bulan)", "Lunas (Boleto/Debit)"])]
    eda_3 = filtered_pay.groupby("tipe_bayar")["payment_value"].mean().reset_index()
    
    if not eda_3.empty:
        fig_pay, ax_pay = plt.subplots(figsize=(8, 4))
        colors_3 = ["#2CA02C", "#D3D3D3"]
        sns.barplot(
            x="tipe_bayar", y="payment_value", data=eda_3, 
            palette=colors_3, order=["Kartu Kredit (>3 Bulan)", "Lunas (Boleto/Debit)"], ax=ax_pay
        )
        ax_pay.set_xlabel("")
        ax_pay.set_ylabel("AOV (BRL)")
        
        # Validasi index untuk menaruh text annotation
        for index, row in eda_3.iterrows():
            ax_pay.text(index, row["payment_value"] + 2, f'R$ {row["payment_value"]:.2f}', color='black', ha="center", fontsize=12)
            
        sns.despine()
        st.pyplot(fig_pay)
    else:
        st.info("Tidak cukup data pembayaran Kartu Kredit / Lunas pada filter ini.")

st.markdown("---")

# =========================================================
# 4. ANALISIS LANJUTAN: RFM & GEOSPATIAL
# =========================================================
st.header("4. Analisis Lanjutan: RFM & Geospatial")

col_rfm, col_geo = st.columns([1, 1])

with col_rfm:
    st.subheader("RFM Analysis: Top 10 Pelanggan")
    st.write("Daftar pelanggan bernilai tinggi (berdasarkan nilai transaksi/Monetary):")
    recent_date = filtered_df["order_purchase_timestamp"].max() + pd.Timedelta(days=1)
    
    rfm_df = filtered_df.groupby("customer_unique_id").agg({
        "order_purchase_timestamp": lambda x: (recent_date - x.max()).days,
        "order_id": "nunique",
        "price": "sum"
    }).reset_index()
    rfm_df.columns = ["customer_unique_id", "recency", "frequency", "monetary"]
    
    st.dataframe(rfm_df.sort_values(by="monetary", ascending=False).head(10), use_container_width=True)

with col_geo:
    st.subheader("Geospatial: Peta Sebaran Pelanggan")
    
    # Load data geolocation dari file raw
    current_dir = os.path.dirname(os.path.abspath(__file__))
    geo_path = os.path.join(current_dir, "..", "data", "geolocation_dataset.csv")
    geo_df = pd.read_csv(geo_path).drop_duplicates(subset=["geolocation_zip_code_prefix"])
    
    # Filter koordinat agar sesuai data yang difilter pengguna
    customers_geo = pd.merge(filtered_df[["customer_zip_code_prefix"]].drop_duplicates(), geo_df, left_on="customer_zip_code_prefix", right_on="geolocation_zip_code_prefix", how="inner")
    
    customers_geo = customers_geo[
        (customers_geo["geolocation_lat"] <= 5.274388) &
        (customers_geo["geolocation_lat"] >= -33.751169) &
        (customers_geo["geolocation_lng"] <= -34.793147) &
        (customers_geo["geolocation_lng"] >= -73.982830)
    ]
    
    sample_geo = customers_geo.sample(n=min(5000, len(customers_geo)), random_state=42)
    
    # Gunakan st.map
    st.map(data=sample_geo, latitude="geolocation_lat", longitude="geolocation_lng")

# Footer
st.caption("Hak Cipta © 2026 - Olist E-Commerce Analytics")
