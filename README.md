# Turkish Speech-to-Text Translator with TTS Output

This project provides a Python-based application that listens to Turkish speech, converts it to text, translates the text to English, and speaks the translated text aloud. It combines speech recognition, translation, and text-to-speech (TTS) technologies to offer near real-time translation and vocal output.

## Features

    - Speech-to-text recognition of Turkish language input
    - Translation of recognized Turkish text to English
    - Text-to-speech synthesis of the translated English text
    - Configurable speech rate, language settings, and exit commands
    - Concurrent processing using threading for smooth operation

## Dependencies

    - Python 3.x
    - `pyttsx3` for text-to-speech
    - `speech_recognition` for speech-to-text
    - `deep-translator` for translation services
    - `googletrans` (referenced in `app.py` for translation, optional)
    - `vosk` models (local model files in `vosk-model-small-tr-0.3` folder)

## Usage

    1. Ensure you have Python 3 installed.
    2. Install dependencies using pip:
    ```
    pip install -r requirements.txt
    ```
    3. Run the main speech-to-text translation script:
    ```
    python stt.py
    ```
    4. Speak in Turkish to the microphone; the program will recognize your speech, translate it to English, and speak the result.
    5. To exit, say one of the exit commands such as "çıkış yap" or "exit program".

## Additional Information

- The project uses a Vosk speech recognition model stored in the `vosk-model-small-tr-0.3` directory. This folder contains necessary model files.
- You can configure speech rate, language settings, and other parameters inside the `stt.py` script.
