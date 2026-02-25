import speech_recognition as sr
import whisper
import os
# We import the setup function so the table is always created safely
from idea_inbox import log_idea, setup_idea_table 

def record_and_transcribe():
    # 1. FIX: Ensure the database table exists before we do anything
    setup_idea_table()
    
    r = sr.Recognizer()
    # 2. FIX: Wait for 2 seconds of silence before cutting you off
    r.pause_threshold = 2.0 
    
    # 3. FIX: Upgraded to 'small' model for much better accuracy
    print("🧠 Booting up local Whisper AI model (Small version)...")
    model = whisper.load_model("small") 

    with sr.Microphone() as source:
        print("🎙️ Calibrating microphone for background noise... please wait 1 second.")
        r.adjust_for_ambient_noise(source, duration=1)
        print("\n✅ READY! Speak your idea now (It will wait 2 seconds after you stop speaking):")
        
        try:
            # Removed the strict timeout limits so you can speak longer
            audio = r.listen(source)
            print("\n⏳ Processing your voice through the AI...")
            
            temp_file = "temp_idea.wav"
            with open(temp_file, "wb") as f:
                f.write(audio.get_wav_data())
            
            # Using FP32 to silence that warning you saw earlier
            result = model.transcribe(temp_file, fp16=False)
            idea_text = result["text"].strip()
            
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            if idea_text:
                print(f"🗣️ AI transcribed: '{idea_text}'")
                log_idea(idea_text)
            else:
                print("⚠️ Couldn't detect any words.")
                
        except Exception as e:
            print(f"❌ Error during AI transcription: {e}")

if __name__ == "__main__":
    record_and_transcribe()