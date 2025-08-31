import os
from dotenv import load_dotenv
import google.generativeai as genai
import pyttsx3
from faster_whisper import WhisperModel
import sounddevice as sd
import numpy as np
import tempfile
import wave
import time

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in the .env file")
genai.configure(api_key=api_key)

WHISPER_MODEL = "base"
GEMINI_MODEL = "gemini-1.5-flash"
RECORDING_DURATION_SECONDS = 10

def speech_to_text_whisper(model: WhisperModel):
    samplerate = 16000
    print(f"\nListening for {RECORDING_DURATION_SECONDS} seconds... (speak when you're ready)")
    audio_path = None
    try:
        audio_data = sd.rec(
            int(samplerate * RECORDING_DURATION_SECONDS),
            samplerate=samplerate,
            channels=1,
            dtype="float32"
        )
        sd.wait()
        audio_data = np.squeeze(audio_data)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
            audio_path = tmpfile.name
            with wave.open(audio_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(samplerate)
                wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())
        segments, info = model.transcribe(audio_path, vad_filter=True, language="en")
        text = "".join(seg.text for seg in segments).strip()
        if text:
            print(f"You said: {text}")
            return text
        else:
            print("I didn't hear anything.")
            return None
    except Exception as e:
        print(f"An error occurred during transcription: {e}")
        return None
    finally:
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)

def ask_gemini(prompt_text, chat_session):
    try:
        print("Sending to Gemini...")
        response = chat_session.send_message(prompt_text)
        return response.text
    except Exception as e:
        print(f"Error calling the Gemini API: {e}")
        return "I'm having some trouble connecting to my brain right now."

def text_to_speech(text, tts_engine):
    if not text:
        print("No text to speak.")
        return
    try:
        tts_engine.say(text)
        tts_engine.runAndWait()
    except Exception as e:
        print(f"An error occurred with the TTS engine: {e}")

def initialize_systems():
    try:
        print(f"Loading Faster-Whisper model ({WHISPER_MODEL})...")
        transcriber = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
        print("Faster-Whisper model loaded successfully.")
    except Exception as e:
        print(f"Error initializing Faster-Whisper: {e}")
        return None, None, None
    try:
        print(f"Initializing Gemini model ({GEMINI_MODEL})...")
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=(
                "persona"
            )
        )
        chat = model.start_chat()  # sem histórico
        print("Gemini model initialized successfully.")
    except Exception as e:
        print(f"Error initializing the Gemini model: {e}")
        return None, None, None
    try:
        print("Initializing TTS engine...")
        tts_engine = pyttsx3.init()
        english_voice_id = None
        voices = tts_engine.getProperty('voices')
        for voice in voices:
            if "english" in voice.name.lower() or "en-us" in voice.id.lower():
                english_voice_id = voice.id
                break
        if english_voice_id:
            tts_engine.setProperty('voice', english_voice_id)
            print("English TTS voice found and set.")
        else:
            print("Warning: No English voice found. Using default TTS voice.")
    except Exception as e:
        print(f"Error initializing the TTS engine: {e}")
        return None, None, None
    return transcriber, chat, tts_engine

if __name__ == "__main__":
    transcriber, chat_session, tts_engine = initialize_systems()
    if not all([transcriber, chat_session, tts_engine]):
        print("Failed to initialize one or more systems. Exiting.")
        exit()

    print("\nrunning. ")

    while True:
        user_speech = speech_to_text_whisper(transcriber)
        if user_speech:
            gemini_response = ask_gemini(user_speech, chat_session)
            print(f"\nI-san says: {gemini_response}")
            text_to_speech(gemini_response, tts_engine)

            if "goodbye" in user_speech.lower():
                break
        else:
            print("Waiting for your command...")
            time.sleep(1)
