from __future__ import annotations

import os

from idea_inbox import log_idea, setup_idea_table


def record_and_transcribe():
    try:
        import speech_recognition as sr
        import whisper
    except Exception as exc:
        raise RuntimeError("voice_inbox requires SpeechRecognition and whisper installed") from exc

    setup_idea_table()

    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 2.0

    print("Booting local Whisper model...")
    model = whisper.load_model(os.environ.get("WHISPER_MODEL", "small"))

    with sr.Microphone() as source:
        print("Calibrating microphone...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Speak your idea now.")
        audio = recognizer.listen(source)
        temp_file = "temp_idea.wav"
        with open(temp_file, "wb") as handle:
            handle.write(audio.get_wav_data())
        try:
            result = model.transcribe(temp_file, fp16=False)
            idea_text = result.get("text", "").strip()
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

        if idea_text:
            log_idea(idea_text)
        else:
            print("No words detected.")


if __name__ == "__main__":
    record_and_transcribe()