#import bawaan
import time 
from machine import Pin, ADC
import network


#REMOTE READ
import webrepl
webrepl.start()


#import untuk teknis purpose
import dht
from umqtt.simple import MQTTClient

BROKER = "broker.hivemq.com"
CLIENT = "esp32_mikojat_smart_179"
TOPIK = "miko/home/smart"

SSID = "POCO M5"
PASS = "miko1234"

# INISIALISASI MQTT
client = MQTTClient(CLIENT, BROKER)

# WAKTU
waktu_sebelumnya = time.ticks_ms()
interval_waktu = 10000

led = Pin(23,Pin.OUT)
buzzer = Pin(4,Pin.OUT)
sensor_dht = dht.DHT11(Pin(14))
ldr = ADC(Pin(34))
ldr.atten(ADC.ATTN_11DB) # Redaman 11dB untuk membaca hingga 3.3V

def Connect_Mqtt():
    try :
        client.connect()
        print("connect ke mqtt")
    
    except OSError:
        
        print("GAGAL: Broker MQTT tidak merespons.")
        
def Connect_WiFi(SSID, PASSWORD):
    global wlan
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    print("memindai jaringan di sekitar ")
    daftar_wifi = wlan.scan()
    
    for wifi in daftar_wifi:
        print(f"- SSID: {wifi[0].decode('utf-8')} | Sinyal: {wifi[3]} dBm")
        
    if not wlan.isconnected():
        print(f"\nMenghubungkan ke {SSID}...")
        wlan.connect(SSID, PASSWORD)
        
        # Batasi waktu tunggu maksimal 10 detik (agar tidak stuck jika gagal)
        waktu_tunggu = 10
        while not wlan.isconnected() and waktu_tunggu > 0:
            print(".", end="")
            time.sleep(1)
            waktu_tunggu -= 1
            
    # 4. Cek Status Akhir
    if wlan.isconnected():
        print("\nWiFi Berhasil Terhubung!")
        # Menampilkan info IP Address, Subnet Mask, dan Gateway yang didapat ESP32
        print("Konfigurasi Jaringan (IP/Netmask/GW/DNS):", wlan.ifconfig())
    else:
        print("\nGagal terhubung. Periksa kembali SSID dan Password Anda.")


def PUBLISH_MQTT(suhu, kelembapan, ldr):
    global client
    payload = f'{{"suhu" : {suhu}, "kelembapan" : {kelembapan}, "ldr" : {ldr}}}'
    
    client.publish(TOPIK, payload)
    print("Data sukses terkirim ke MQTT:", payload)

    led.value(1)
    buzzer.value(1)
    time.sleep(0.1)

    led.value(0)
    buzzer.value(0)
    time.sleep(0.1)

Connect_WiFi(SSID, PASS)
Connect_Mqtt()

# -----------------------------------------------------------
# LOOP MAIN==================================================
# -----------------------------------------------------------
# --- 1. SETUP AWAL ---
# (Koneksi WiFi, Setup Sensor, dll ada di luar sini)

print("Program berjalan...")

# --- 2. BUNGKUS SELURUH SISTEM DENGAN TRY UTAMA ---
try:
    while True:
        waktu_sekarang = time.ticks_ms()
        if time.ticks_diff(waktu_sekarang, waktu_sebelumnya) >= interval_waktu:
            
            # --- 3. BUNGKUS ERROR KONEKSI/SENSOR DI DALAM SINI ---
            try:
                sensor_dht.measure()
                suhu = sensor_dht.temperature()
                kelembaban = sensor_dht.humidity()
                nilai_cahaya = ldr.read()
                
                PUBLISH_MQTT(suhu, kelembaban, nilai_cahaya)
                                
            except OSError:
                print("Gagal kirim, cek kabel.")
            
            waktu_sebelumnya = waktu_sekarang

# --- 4. TANGKAP TOMBOL STOP DARI LAPTOP ---
except KeyboardInterrupt:
    print("\nProgram dihentikan secara paksa oleh pengguna!")

# --- 5. FINALLY BERADA DI TINGKAT PALING LUAR ---
finally:
    print("Mereset status pin perangkat keras...")
    led.value(0)
    buzzer.value(0)
    
    # Ini HANYA akan tereksekusi SATU KALI saat program benar-benar mati.

    