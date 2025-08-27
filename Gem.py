import os
from dotenv import load_dotenv
import speech_recognition as sr
import google.generativeai as genai
import pyttsx3

# --- 1. INITIAL CONFIGURATION ---

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

# Load and configure the Google API key
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in the .env file")
genai.configure(api_key=api_key)


# --- 2. MODEL AND VOICE INITIALIZATION ---
try:
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction=(
            "personality input"
        )
    )
    # Start a chat session that will retain conversation history
    chat = model.start_chat(history=[])
except Exception as e:
    print(f"Error initializing the Gemini model: {e}")
    exit()

# Initialize the text-to-speech engine
try:
    tts_engine = pyttsx3.init()
    # Find and set an English voice
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


# --- 3. FUNCTION DEFINITIONS ---

def speech_to_text():
    """
    Captures audio when speech is detected and converts it to text.
    It actively listens instead of using a fixed duration.
    """
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\nAdjusting for ambient noise...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Listening... (say something!)")

        try:
            # Listen for speech and automatically detect when the user stops talking
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
    """
    Sends text to the Gemini model using the persistent chat session to maintain context.
    """
    try:
        print("Sending to Gemini...")
        response = chat.send_message(prompt_text)
        return response.text
    except Exception as e:
        print(f"Error calling the Gemini API: {e}")
        return "I'm having some trouble connecting to my brain right now."

def text_to_speech(text):
    """
    Converts text to speech using the pre-initialized engine.
    """
    if not text:
        print("No text to speak.")
        return
    try:
        tts_engine.say(text)
        tts_engine.runAndWait()
    except Exception as e:
        print(f"An error occurred with the TTS engine: {e}")


# --- 4. MAIN PROGRAM EXECUTION ---

if __name__ == "__main__":
    print("AI Assistant 'I-san' is now running. Say 'goodbye' to exit.")
    
    # Main loop to keep the assistant running
    while True:
        user_speech = speech_to_text()

        if user_speech:
            # Check for the exit command
            if "goodbye" in user_speech.lower():
                farewell = "Okay, talk to you later. Goodbye!"
                print(f"\nI-san says: {farewell}")
                text_to_speech(farewell)
                break  # Exit the while loop

            # Get the response from Gemini
            gemini_response = ask_gemini(user_speech)
            
            # Print and speak the response
            print(f"\nI-san says: {gemini_response}")
            text_to_speech(gemini_response)
        else:
            print("No speech detected. Please try again.")

