import paho.mqtt.client as mqtt
import json
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Muat isi brankas .env ke dalam memori
load_dotenv()

# --- KONFIGURASI MQTT ---
BROKER = os.getenv("BROKER")
TOPIK = os.getenv("TOPIK")

# --- KONFIGURASI SUPABASE ---
# Ambil variabel dari .env secara aman
url = os.getenv("URL")
key = os.getenv("KEY")

# Validasi keamanan (Mencegah skrip berjalan jika file .env lupa dibuat)
if not url or not key:
    raise ValueError("File .env tidak ditemukan atau URL/Key Supabase kosong!")

# Membuat koneksi ke Supabase
supabase: Client = create_client(url, key)

# --- FUNGSI CALLBACK MQTT ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Terhubung ke MQTT Broker!")
        client.subscribe(TOPIK)
        print(f"🎧 Mendengarkan di topik: {TOPIK}...\n")
    else:
        print(f"❌ Gagal terhubung. Kode: {rc}")

def on_message(client, userdata, msg):
    payload = msg.payload.decode("utf-8")
    
    try:
        data = json.loads(payload)
        # Ekstrak dengan aman menggunakan .get()
        suhu = data.get("suhu")
        kelembapan = data.get("kelembapan")
        cahaya = data.get("ldr")
        
        # Validasi sederhana: Jangan simpan jika datanya kosong
        if suhu is not None and cahaya is not None:
            # 1. Bungkus data sesuai nama kolom di tabel SQL 'log_cuaca'
            data_sql = {
                "suhu": suhu,
                "kelembapan": kelembapan,
                "cahaya": cahaya
            }
            
            # 2. Tembakkan ke Supabase
            hasil = supabase.table("log_sensor").insert(data_sql).execute()
            print(f"💾 TERSIMPAN KE DATABASE -> Suhu: {suhu}°C | Cahaya: {cahaya}")
            
        else:
            print("⚠️ Data tidak lengkap, diabaikan dari database.")
            
    except json.JSONDecodeError:
        print("⚠️ Format bukan JSON yang valid.")
    except Exception as e:
        print(f"❌ Gagal menyimpan ke database: {e}")

# --- EKSEKUSI UTAMA ---
print("Memulai Skrip Backend & Menghubungkan ke Database...")
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, 1883, 60)

try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\n🛑 Subscriber dihentikan.")