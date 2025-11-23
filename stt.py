import speech_recognition as sr
from deep_translator import GoogleTranslator
import pyttsx3
import threading
import queue
import time

# --- Ayarlar ---
INPUT_LANGUAGE = "tr-TR"
OUTPUT_LANGUAGE_CODE = "en"
TTS_VOICE_HINT_LANG = "english" # pyttsx3 için ses ipucu (sistemdeki seslere göre değişir)
TTS_VOICE_HINT_COUNTRY = "us" # pyttsx3 için ses ipucu (örn: en-us)
SPEECH_RATE = 150 # Konuşma hızı
PAUSE_THRESHOLD = 0.8 # Cümleler arası duraklama
PHRASE_TIME_LIMIT = 15 # Bir konuşma parçasının maksimum süresi (saniye)
MIC_TIMEOUT = None # Mikrofon dinleme süresi (None = sürekli, bir değer girilirse o kadar saniye bekler)
# MIC_TIMEOUT = 5 # 5 saniye boyunca ses gelmezse zaman aşımına uğrar

# Çıkış komutları (küçük harfle)
EXIT_COMMANDS = ["çıkış yap", "programı kapat", "kapat", "exit program"]

# --- Global Değişkenler ---
try:
    tts_engine = pyttsx3.init()
except ImportError:
    print("pyttsx3 kütüphanesi bulunamadı. Lütfen kurun: pip install pyttsx3")
    exit()
except RuntimeError:
    print("pyttsx3 sürücüsü başlatılamadı. Ses sürücülerinizde sorun olabilir.")
    exit()

text_queue = queue.Queue()
stop_event = threading.Event() # Programın sonlandırılması için olay

# --- TTS Motoru Ayarları ---
def setup_tts_engine():
    voices = tts_engine.getProperty('voices')
    selected_voice_id = None
    for voice in voices:
        try:
            # Bazı sistemlerde voice.languages boş olabilir, try-except ile yakalayalım
            if any(lang.lower().startswith(OUTPUT_LANGUAGE_CODE) for lang in voice.languages) or \
               (TTS_VOICE_HINT_LANG in voice.name.lower() and (not TTS_VOICE_HINT_COUNTRY or TTS_VOICE_HINT_COUNTRY in voice.id.lower())):
                selected_voice_id = voice.id
                print(f"İngilizce ses bulundu: {voice.name} ({voice.id})")
                break
        except AttributeError: # voice.languages yoksa
             if TTS_VOICE_HINT_LANG in voice.name.lower() and (not TTS_VOICE_HINT_COUNTRY or TTS_VOICE_HINT_COUNTRY in voice.id.lower()):
                selected_voice_id = voice.id
                print(f"İngilizce ses bulundu (isim/id ile): {voice.name} ({voice.id})")
                break


    if selected_voice_id:
        tts_engine.setProperty('voice', selected_voice_id)
    else:
        print(f"Belirli bir {TTS_VOICE_HINT_LANG} sesi bulunamadı, varsayılan ses kullanılacak.")

    tts_engine.setProperty('rate', SPEECH_RATE)

# --- Dinleme ve Tanıma İş Parçacığı Fonksiyonu ---
def listen_thread_func(recognizer, microphone):
    print("Dinleme iş parçacığı başlatıldı.")
    while not stop_event.is_set():
        with microphone as source:
            try:
                # adjust_for_ambient_noise her seferinde yapmak yerine başta bir kere yeterli olabilir,
                # ama sürekli değişen ortamlar için burada tutulabilir.
                # recognizer.adjust_for_ambient_noise(source, duration=0.3)
                print("\nSiz konuşun (TR):")
                audio = recognizer.listen(source, timeout=MIC_TIMEOUT, phrase_time_limit=PHRASE_TIME_LIMIT)
            except sr.WaitTimeoutError:
                # print("Kimse konuşmadı veya ses çok düşük.")
                continue # Zaman aşımı olduysa döngüye devam et
            except Exception as e:
                if not stop_event.is_set(): # Eğer program kapatılmıyorsa hata yazdır
                    print(f"Mikrofon dinleme hatası: {e}")
                time.sleep(0.1) # Hata durumunda kısa bir bekleme
                continue

        try:
            if stop_event.is_set(): break
            print("Ses algılandı, Türkçe metne çevriliyor...")
            turkish_text = recognizer.recognize_google(audio, language=INPUT_LANGUAGE)
            print(f"Algılanan (TR): {turkish_text}")

            if turkish_text.strip().lower() in EXIT_COMMANDS:
                print("Çıkış komutu algılandı.")
                text_queue.put(None) # Sinyal olarak None gönder
                stop_event.set()
                break

            text_queue.put(turkish_text)

        except sr.UnknownValueError:
            if not stop_event.is_set():
                print("Ne dediğinizi anlayamadım.")
        except sr.RequestError as e:
            if not stop_event.is_set():
                print(f"Google Speech Recognition servisinden sonuç alınamadı; {e}")
        except Exception as e:
            if not stop_event.is_set():
                print(f"Tanıma sırasında beklenmedik hata: {e}")
    print("Dinleme iş parçacığı sonlandırıldı.")

# --- Çeviri ve Seslendirme İş Parçacığı Fonksiyonu ---
def translate_speak_thread_func():
    print("Çeviri ve seslendirme iş parçacığı başlatıldı.")
    translator = GoogleTranslator(source=INPUT_LANGUAGE.split('-')[0], target=OUTPUT_LANGUAGE_CODE)

    while not stop_event.is_set():
        try:
            turkish_text = text_queue.get(timeout=1) # Kuyruktan 1 saniye bekleyerek al
            if turkish_text is None: # Sonlandırma sinyali
                stop_event.set() # Diğer iş parçacığını da durdurmak için
                break

            print(f"Çevriliyor: \"{turkish_text}\"")
            try:
                translated_text = translator.translate(turkish_text)
                if translated_text:
                    print(f"Çeviri (EN): {translated_text}")
                    tts_engine.say(translated_text)
                    tts_engine.runAndWait() # Bu satır bir sonraki çeviriye geçmeden seslendirmenin bitmesini bekler
                else:
                    print("Çeviri boş sonuç döndürdü.")
            except Exception as e:
                print(f"Çeviri hatası: {e}")
                tts_engine.say(f"Sorry, I encountered a translation error for: {turkish_text[:30]}") # Hata mesajını da seslendirebiliriz
                tts_engine.runAndWait()

            text_queue.task_done() # Kuyruk işlemcisinin işi bitirdiğini bildirir

        except queue.Empty:
            continue # Kuyruk boşsa döngüye devam et
        except Exception as e:
            if not stop_event.is_set():
                print(f"Çeviri/Seslendirme sırasında beklenmedik hata: {e}")
    
    # Motoru düzgün kapatmak için son bir runAndWait gerekebilir
    # Özellikle kuyrukta bekleyen son bir 'say' komutu varsa
    try:
        tts_engine.stop() # Bekleyen konuşmaları iptal et
    except Exception as e:
        print(f"TTS motoru durdurulurken hata: {e}")
    print("Çeviri ve seslendirme iş parçacığı sonlandırıldı.")


# --- Ana Program ---
if __name__ == "__main__":
    setup_tts_engine()

    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    recognizer.pause_threshold = PAUSE_THRESHOLD
    # recognizer.energy_threshold = 4000 # Ortamınıza göre ayarlayın, varsayılan dinamik ayar daha iyi olabilir

    print("Program Başladı. Türkçe konuşabilirsiniz.")
    print(f"Çıkmak için '{', '.join(EXIT_COMMANDS)}' deyin.")

    # Başlangıçta ortam gürültüsünü ayarlama
    with microphone as source:
        print("Ortam gürültüsü ayarlanıyor (1sn), lütfen sessiz olun...")
        try:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Gürültü ayarı tamamlandı.")
        except Exception as e:
            print(f"Gürültü ayarı sırasında hata: {e}. Varsayılan ayarlar kullanılacak.")


    # İş parçacıklarını oluştur ve başlat
    listener_thread = threading.Thread(target=listen_thread_func, args=(recognizer, microphone))
    translator_speaker_thread = threading.Thread(target=translate_speak_thread_func)

    listener_thread.daemon = True # Ana program sonlandığında bu thread'ler de sonlansın
    translator_speaker_thread.daemon = True

    listener_thread.start()
    translator_speaker_thread.start()

    try:
        while not stop_event.is_set():
            time.sleep(0.5) # Ana iş parçacığı olayları beklerken uyusun
    except KeyboardInterrupt:
        print("\nCtrl+C algılandı. Program sonlandırılıyor...")
        stop_event.set()
        text_queue.put(None) # Kuyruğa None ekleyerek çeviri thread'inin de çıkmasını sağla

    # İş parçacıklarının bitmesini bekle
    print("İş parçacıklarının sonlanması bekleniyor...")
    if listener_thread.is_alive():
        listener_thread.join(timeout=5)
    if translator_speaker_thread.is_alive():
        translator_speaker_thread.join(timeout=5) # Seslendirmenin bitmesi için biraz zaman tanıyabiliriz

    print("Program kapatıldı.")