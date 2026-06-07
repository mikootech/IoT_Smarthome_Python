import streamlit as st
import pandas as pd
import os
from supabase import create_client, Client

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Dashboard IoT", layout="wide")
st.title("📊 Dashboard Jemuran Pintar")

# --- KONEKSI SUPABASE ---
# Trik Cerdas: Coba muat dotenv (untuk laptop), abaikan jika tidak ada (untuk internet)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass # Lanjutkan saja, jangan error

# Ambil kunci dari Brankas (baik lokal maupun cloud)
url = os.environ.get("URL") or st.secrets.get("URL")
key = os.environ.get("KEY") or st.secrets.get("KEY")

if not url or not key:
    st.error("Kredensial Supabase tidak ditemukan!")
    st.stop()

supabase: Client = create_client(url, key)

# ... (Lanjutkan fungsi ambil_data() dan kode ke bawah sama persis seperti sebelumnya) ...

# --- FUNGSI TARIK DATA ---
def ambil_data():
    # Mengambil 50 data terakhir dari tabel log_sensor
    hasil = supabase.table("log_sensor").select("*").order("id", desc=True).limit(50).execute()
    
    if hasil.data:
        df = pd.DataFrame(hasil.data)
        # Ubah format waktu dan jadikan sumbu X
        df['waktu_catat'] = pd.to_datetime(df['waktu_catat'])
        df.set_index('waktu_catat', inplace=True)
        # Urutkan kembali dari yang terlama ke terbaru untuk arah grafik dari kiri ke kanan
        df = df.sort_index(ascending=True) 
        return df
    return pd.DataFrame()

# --- TAMPILAN VISUAL ---
df = ambil_data()

if not df.empty:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Grafik Suhu (°C)")
        st.line_chart(df['suhu'], color="#ff4b4b")
        
    with col2:
        st.subheader("💡 Grafik Cahaya (LDR)")
        st.line_chart(df['cahaya'], color="#ffd166")
        
    st.markdown("---")
    st.subheader("📋 Log Data Mentah")
    st.dataframe(df, width='stretch')  # Tampilkan data mentah dalam bentuk tabels
    
    # Tombol Refresh Manual
    if st.button("🔄 Refresh Data"):
        st.rerun()
else:
    st.warning("Belum ada data di database Supabase.")