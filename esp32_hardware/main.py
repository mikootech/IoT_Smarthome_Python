import time 
from machine import Pin, ADC, I2C
import network
import dht
from umqtt.simple import MQTTClient
import ssd1306
from config import broker, client, topik, ssid, password

# --- KONFIGURASI ---
BROKER = broker
CLIENT = client
TOPIK = topik
SSID = ssid
PASS = password


# time.sleep(1)
# --- INISIALISASI PERANGKAT KERAS ---
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
oled = ssd1306.SSD1306_I2C(128, 32, i2c) # Layar resolusi 128x32

led = Pin(23, Pin.OUT)
buzzer = Pin(4, Pin.OUT)
sensor_dht = dht.DHT11(Pin(14))
ldr = ADC(Pin(34))
ldr.atten(ADC.ATTN_11DB) 

client = MQTTClient(CLIENT, BROKER)
waktu_sebelumnya = time.ticks_ms()
interval_waktu = 3000

# --- FUNGSI TAMPILAN OLED ---
def Tampilkan_OLED(baris1, baris2="", baris3=""):
    """Fungsi pembantu agar mudah menulis ke OLED"""
    oled.fill(0) 
    oled.text(baris1, 0, 0)   # Baris 1 di atas
    oled.text(baris2, 0, 10)  # Baris 2 agak ke tengah (disesuaikan untuk 32px)
    oled.text(baris3, 0, 20)  # Baris 3 di bawah (disesuaikan untuk 32px)
    oled.show()               

# --- FUNGSI KONEKSI ---
# --- FUNGSI KONEKSI (DISEDERHANAKAN) ---
# --- FUNGSI KONEKSI (DISEDERHANAKAN) ---
def Connect_WiFi(ssid_target, pass_target): 
    global wlan
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True) # Pastikan antena menyala
    
    # Putuskan koneksi yang menggantung (gunakan try-except agar tidak error jika memang sudah putus)
    try:
        wlan.disconnect()
    except:
        pass
    
    time.sleep(1) # Beri nafas 1 detik untuk mesin WiFi
    
    if not wlan.isconnected():
        print(f"Menghubungkan ke {ssid_target}...")
        Tampilkan_OLED("Connecting...", ssid_target) 
        
        # Eksekusi koneksi
        wlan.connect(ssid_target, pass_target)
        
        waktu_tunggu = 10
        while not wlan.isconnected() and waktu_tunggu > 0:
            print(".", end="")
            time.sleep(1)
            waktu_tunggu -= 1
            
    if wlan.isconnected():
        ip_address = wlan.ifconfig()[0]
        print("\nWiFi Berhasil Terhubung! IP:", ip_address)
        Tampilkan_OLED("WiFi Connected!", "IP Address:", ip_address)
    else:
        print("\nGagal terhubung WiFi.")
        Tampilkan_OLED("WiFi Failed!")


#CONFIG MQTT
def Connect_Mqtt():
    try:
        client.connect()
        print("Berhasil connect ke MQTT")
    except OSError:
        print("GAGAL: Broker MQTT tidak merespons.")


#MENGIRIM BACAAN SENSOR KE MQTT HIVEMQ
def PUBLISH_MQTT(suhu, kelembapan, nilai_ldr):
    global client
    payload = f'{{"suhu": {suhu}, "kelembapan": {kelembapan}, "ldr": {nilai_ldr}}}'
    client.publish(TOPIK, payload)
    print("Data terkirim:", payload)
    
    buzzer.value(1)
    led.value(1)
    time.sleep(0.05)
    led.value(0)
    buzzer.value(0)


# --- JALANKAN ---
oled.fill(0)
oled.show()

# Panggil dengan argumen yang benar
Connect_WiFi(SSID, PASS)
Connect_Mqtt()

print("Program berjalan...")

try:
    while True:
        waktu_sekarang = time.ticks_ms()
        
        if time.ticks_diff(waktu_sekarang, waktu_sebelumnya) >= interval_waktu:
            
            # --- CEK KONEKSI WIFI SEBELUM KIRIM ---
            if not wlan.isconnected(): # Tambahan titik dua (:)
                print("Koneksi terputus, mencoba reconnect...") # Perbaikan tanda kutip
                Connect_WiFi(SSID, PASS) # Panggil dengan argumen
                Connect_Mqtt() # Jangan lupa sambung ulang MQTT-nya juga!
                
            try:
                sensor_dht.measure()
                suhu = sensor_dht.temperature()
                kelembaban = sensor_dht.humidity()
                nilai_cahaya = ldr.read()
                
                PUBLISH_MQTT(suhu, kelembaban, nilai_cahaya)
                
                ip_sekarang = wlan.ifconfig()[0]
                Tampilkan_OLED(f"IP:{ip_sekarang}", f"Suhu: {suhu} C", f"LDR : {nilai_cahaya}")
                
            except OSError:
                print("Gagal membaca sensor atau kirim MQTT.")
                Tampilkan_OLED("System Error!", "Check Hardware")
            
            waktu_sebelumnya = waktu_sekarang

except KeyboardInterrupt:
    print("\nProgram dihentikan.")
    Tampilkan_OLED("Program Stopped")

finally:
    led.value(0)
    buzzer.value(0)
