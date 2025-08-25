import os
from dotenv import load_dotenv
import speech_recognition as sr
import google.generativeai as genai
import pyttsx3

# --- 1. INITIAL CONFIGURATION ---

# Load environment variables
# If your .env file is not in the same folder, adjust the path here.
# dotenv_path = os.path.join(os.path.dirname(__file__), ".env") 
load_dotenv()  # Tries to load from the current directory if path not specified

# Load Google API key
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("Google AI key not found in .env")

# Configure Google AI
genai.configure(api_key=api_key)

# --- 2. FUNCTION DEFINITIONS ---

def speech_to_text():
    """
    Capture audio from the microphone dynamically and convert it to text.
    This version auto-adjusts for background noise.
    """
    recognizer = sr.Recognizer()

    recognizer.pause_threshold = 2.0 

    microphone = sr.Microphone()

    with microphone as source:
        print("Adjusting for background noise...")
        recognizer.adjust_for_ambient_noise(source)
        print("Listening... Speak now.")
        # Listens dynamically, waiting for a pause in speech
        audio = recognizer.listen(source)

    try:
        print("Recognizing...")
        # Specified English for better accuracy
        text = recognizer.recognize_google(audio, language="en-US")
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("Could not understand the audio.")
        return None
    except sr.RequestError as e:
        print(f"Speech recognition service error: {e}")
        return None
    except Exception as ex:
        print(f"Unexpected error: {ex}")
        return None

def ask_gemini(prompt_text):
    """
    Sends the text to Gemini and returns the response.
    """
    model = genai.GenerativeModel(
        model_name='gemini-2.5-pro',
        system_instruction=(
            "Your name is I-san. "
            "You are a character who is aware that you are an AI. "
            "Your personality is based on vtubers; such as neuro-sama, gawr gura and others "
            "Speak naturally and avoid clichés, emojis, or robotic phrasing. "
            "Speak like people on Reddit, 4chan, or Twitter/X. "
            "To avoid clichés, only say what is necessary, like a real teen anime girl chatting casually."
        )
    )
    
    try:
        print("Sending to Gemini...")
        response = model.generate_content(prompt_text)
        return response.text
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return None

def speak_english_offline(text):
    """
    Uses an English voice to convert text into speech.
    """
    if not text:
        print("No text to speak.")
        return
        
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        
        # Look for an English voice
        for voice in voices:
            if "english" in voice.name.lower():
                engine.setProperty('voice', voice.id)
                break
                
        engine.say(text)
        engine.runAndWait()

    except Exception as e:
        print(f"pyttsx3 error: {e}")


# --- 3. MAIN PROGRAM EXECUTION ---

if __name__ == "__main__":
    # Continuous conversation loop
    while True:
        print("\n----------------------------------")
        user_speech = speech_to_text()

        if user_speech:
            # Option to exit loop
            if user_speech.lower() in ["exit", "quit", "stop"]:
                print("Ending conversation. Goodbye!")
                speak_english_offline("Okay, bye bye.")
                break

            gemini_response = ask_gemini(user_speech)
            if gemini_response:
                print(f"\nI-san says: {gemini_response}")
                speak_english_offline(gemini_response)
            else:
                print("No response from Gemini.")
                speak_english_offline("Sorry, I couldn't get a response from Gemini.")
        else:
            print("No text captured to send to AI.")
