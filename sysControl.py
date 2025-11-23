import sounddevice as sd
import numpy as np
import queue
import threading
from faster_whisper import WhisperModel
import time

# Modeli yükle
try:
    print("Whisper model yükleniyor...")
    model = WhisperModel("tiny", compute_type="int8")
    print("Model başarıyla yüklendi!")
except Exception as e:
    print(f"Model yüklenirken hata: {e}")
    exit()

# Mikrofon ayarları
samplerate = 16000
block_duration = 2  # saniye
block_size = int(samplerate * block_duration)

audio_q = queue.Queue()

# Ses kartlarını kontrol et
try:
    print("Mikrofon cihazları kontrol ediliyor...")
    print(sd.query_devices())
    print("Mikrofon cihazları başarıyla listelendi!")
except Exception as e:
    print(f"Mikrofon cihazları kontrol edilirken hata: {e}")
    exit()

# Ses dinleme callback fonksiyonu
def callback(indata, frames, time, status):
    if status:
        print("Mikrofon hatası:", status)
    audio_q.put(indata.copy())

# Ses dinleme thread'i
def listen():
    try:
        with sd.InputStream(samplerate=samplerate, channels=1, callback=callback):
            print("🎙️ Mikrofon başarıyla açıldı, dinleniyor...")
            while True:
                audio_block = audio_q.get()
                audio_np = np.squeeze(audio_block)
                segments, _ = model.transcribe(audio_np, language="tr", beam_size=1)
                for segment in segments:
                    print("📝", segment.text)
    except Exception as e:
        print(f"Dinleme sırasında hata: {e}")
        exit()

# Thread başlat
try:
    threading.Thread(target=listen, daemon=True).start()
    print("Dinleme thread'i başlatıldı.")
except Exception as e:
    print(f"Thread başlatılırken hata: {e}")
    exit()

# Ana thread'in açık kalması için
try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Program sonlandırıldı.")
