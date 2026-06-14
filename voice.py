import speech_recognition as sr
import pyttsx3

engine = pyttsx3.init()
engine.setProperty("rate", 165)
engine.setProperty("volume", 1.0)

def speak(text):
    """AI speaks the feedback out loud"""
    print(f"\n🔊 {text}")
    engine.say(text)
    engine.runAndWait()

def listen(timeout=15, phrase_limit=90):
    """Capture voice — runs until silence detected"""
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 2.0   # waits 2 sec of silence before stopping
    recognizer.energy_threshold = 300  # mic sensitivity

    with sr.Microphone() as source:
        print(c("\n🎤 Listening... speak your answer. Pause for 2 seconds to finish.", "cyan"))
        recognizer.adjust_for_ambient_noise(source, duration=1)
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
            text = recognizer.recognize_google(audio)
            print(f"\n📝 You said: {text}")
            return text
        except sr.WaitTimeoutError:
            print("⏱ No speech detected.")
            return None
        except sr.UnknownValueError:
            print("❌ Could not understand audio. Please try again.")
            return None
        except sr.RequestError:
            print("❌ Internet needed for voice recognition.")
            return None

def c(text, color):
    COLORS = {
        "cyan": "\033[96m",
        "reset": "\033[0m",
    }
    return f"{COLORS.get(color, '')}{text}{COLORS['reset']}"