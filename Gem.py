import os
from dotenv import load_dotenv
import speech_recognition as sr
import google.generativeai as genai
import pyttsx3
import json

# --- 1. INITIAL CONFIGURATION ---

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

# Load and configure the Google API key
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in the .env file")
genai.configure(api_key=api_key)

DATA_FOLDER = "data"
MEMORY_FILE = os.path.join(DATA_FOLDER, "memory.json")

if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)

# --- 2. FUNCTION DEFINITIONS (ALL FUNCTIONS GO HERE) ---

def load_history_from_memory():
    """Loads conversation history from memory.json and formats it for Gemini."""
    filename = "memory.json"
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            history_json = json.load(f)
        
        # Convert our simple JSON format to the one Gemini's 'history' parameter expects
        gemini_history = []
        for entry in history_json:
            if isinstance(entry, dict) and 'user' in entry and 'isan' in entry:
                gemini_history.append({'role': 'user', 'parts': [entry['user']]})
                gemini_history.append({'role': 'model', 'parts': [entry['isan']]})
        
        if gemini_history:
            print(f"Successfully loaded {len(history_json)} turns from conversation history.")
        return gemini_history
            
    except (FileNotFoundError, json.JSONDecodeError):
        print("No previous history found. Starting a new conversation.")
        return []

def speech_to_text():
    """Captures audio when speech is detected and converts it to text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\nAdjusting for ambient noise...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Listening... (say something!)")
        try:
            audio_data = recognizer.listen(source)
            print("Processing speech...")
            text = recognizer.recognize_google(audio_data, language="en-US")
            print(f"You said: {text}")
            return text
        except sr.WaitTimeoutError:
            print("Listening timed out while waiting for phrase to start.")
        except sr.UnknownValueError:
            print("Could not understand the audio.")
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
    return None

def ask_gemini(prompt_text):
    """Sends text to the Gemini model using the persistent chat session."""
    try:
        print("Sending to Gemini...")
        response = chat.send_message(prompt_text)
        return response.text
    except Exception as e:
        print(f"Error calling the Gemini API: {e}")
        return "I'm having some trouble connecting to my brain right now."

def text_to_speech(text):
    """Converts text to speech using the pre-initialized engine."""
    if not text:
        print("No text to speak.")
        return
    try:
        tts_engine.say(text)
        tts_engine.runAndWait()
    except Exception as e:
        print(f"An error occurred with the TTS engine: {e}")

def save_to_memory(user_input, isan_output):
    """Loads history from memory.json, adds the new conversation, and saves it."""
    filename = "memory.json"
    current_conversation = {"user": user_input, "isan": isan_output}
    history = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data_from_file = json.load(f)
            if isinstance(data_from_file, list):
                history = data_from_file
            elif isinstance(data_from_file, dict):
                history = [data_from_file]
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    history.append(current_conversation)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=4)
    print(f"Conversation saved to {filename}")


# --- 3. MODEL AND VOICE INITIALIZATION ---

# Configure the Gemini model
try:
    model = genai.GenerativeModel(
        model_name='gemini-2.5-pro', #change if needed
        system_instruction=(
           "input personality here"
        )
    )
    # Load previous conversation history BEFORE starting the chat
    # This call now works because the function is defined above
    conversation_history = load_history_from_memory()
    # Start a chat session with the loaded history
    chat = model.start_chat(history=conversation_history)

except Exception as e:
    print(f"Error initializing the Gemini model: {e}")
    exit()

# Initialize the text-to-speech engine
try:
    tts_engine = pyttsx3.init()
    english_voice_id = None
    for voice in tts_engine.getProperty('voices'):
        if "english" in voice.name.lower():
            english_voice_id = voice.id
            break
    if english_voice_id:
        tts_engine.setProperty('voice', english_voice_id)
except Exception as e:
    print(f"Error initializing the TTS engine: {e}")
    exit()


# --- 4. MAIN PROGRAM EXECUTION ---

if __name__ == "__main__":
    print("AI Assistant 'I-san' is now running. Say 'goodbye' to exit.")
    
    while True:
        user_speech = speech_to_text()

        if user_speech:
            if "goodbye" in user_speech.lower():
                farewell = "Okay, talk to you later. Goodbye!"
                print(f"\nI-san says: {farewell}")
                text_to_speech(farewell)
                save_to_memory(user_speech, farewell)
                break

            gemini_response = ask_gemini(user_speech)
            
            print(f"\nI-san says: {gemini_response}")
            text_to_speech(gemini_response)
            save_to_memory(user_speech, gemini_response)
        else:
            print("No speech detected. Please try again.")
