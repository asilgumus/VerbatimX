import pyttsx3
import threading
import time

engine = None
tts_lock = threading.Lock()

def initialize_engine():
    global engine
    print("Engine initialize ediliyor...")
    try:
        engine = pyttsx3.init()
        # Gerekirse sürücü adı belirtin (Windows'ta 'sapi5', Linux'ta 'espeak', macOS'ta 'nsss')
        # engine = pyttsx3.init(driverName='sapi5')
        print("Engine initialize edildi.")
        # Motorun özelliklerini ayarlamayı deneyin, bazen bu 'canlanmasına' yardımcı olur
        voices = engine.getProperty('voices')
        if voices:
            engine.setProperty('voice', voices[0].id) # İlk uygun sesi ayarla
        engine.setProperty('rate', 150)
    except Exception as e:
        print(f"Engine initialize edilirken HATA: {e}")
        engine = None # Başarısız olursa None olarak kalsın

def speak_test(text, thread_name):
    global engine
    print(f"Thread {thread_name}: '{text}' konuşması için kilit bekleniyor.")
    with tts_lock:
        print(f"Thread {thread_name}: Kilit alındı, '{text}' konuşulacak.")
        if engine is None:
            print(f"Thread {thread_name}: HATA - TTS Engine initialize edilmemiş!")
            return
        try:
            print(f"Thread {thread_name}: engine.say çağrılıyor...")
            engine.say(text)
            print(f"Thread {thread_name}: engine.runAndWait çağrılıyor...")
            engine.runAndWait()
            print(f"Thread {thread_name}: engine.runAndWait tamamlandı.")
        except Exception as e:
            print(f"Thread {thread_name}: TTS sırasında HATA: {e}")
        print(f"Thread {thread_name}: Kilit serbest bırakılacak.")

if __name__ == "__main__":
    initialize_engine()

    if engine: # Sadece motor başarılı bir şekilde initialize olduysa devam et
        print("\n--- Test 1: Tek Thread ---")
        speak_test("Bu ilk test mesajı.", "Test-1")

        time.sleep(1) # Thread'in bitmesi için biraz zaman tanı

        print("\n--- Test 2: İki Thread (ardışık başlatma) ---")
        thread1 = threading.Thread(target=speak_test, args=("Merhaba dünya.", "Thread-A"))
        thread2 = threading.Thread(target=speak_test, args=("Nasılsın?", "Thread-B"))

        thread1.start()
        time.sleep(0.1) # Thread2'nin, Thread1 kilidi aldıktan sonra başlamasını sağlamak için küçük bir gecikme
        thread2.start()

        thread1.join()
        thread2.join()

        print("\nTestler tamamlandı.")
    else:
        print("TTS motoru başlatılamadığı için testler çalıştırılamadı.")