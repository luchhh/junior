"""
Text-to-Speech module using OpenAI TTS API
"""
import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI


def get_client() -> OpenAI:
    """Create and return an OpenAI client using the API key from env."""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to your environment or .env file."
        )
    return OpenAI(api_key=api_key)


def speak(text: str, voice: str = "alloy", audio_device: int = 3) -> None:
    """
    Convert text to speech and play it through the speaker.

    Args:
        text: Text to convert to speech
        voice: OpenAI TTS voice (alloy, echo, fable, onyx, nova, shimmer)
        audio_device: ALSA audio device card number (default: 3 for USB speaker)
    """
    if not text or len(text.strip()) == 0:
        print("⚠️  Empty text, skipping TTS")
        return

    print(f"🗣️  Speaking: {text}")

    try:
        # Generate speech using OpenAI TTS API
        client = get_client()
        response = client.audio.speech.create(
            model="tts-1",  # or "tts-1-hd" for higher quality
            voice=voice,
            input=text,
        )

        # Save to temporary file
        speech_file = Path("/tmp/robot_speech.mp3")
        response.stream_to_file(speech_file)

        # Play audio using aplay (convert from mp3 first if needed)
        # For simplicity, we'll use mpg123 or ffmpeg to play mp3 directly
        # Or save as wav format instead

        # Option 1: Use aplay with hw device (requires wav format)
        # We need to convert mp3 to wav first, or use OpenAI's format parameter

        # Let's regenerate as wav for direct aplay compatibility
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
            response_format="wav"  # Get WAV instead of MP3
        )

        speech_file = Path("/tmp/robot_speech.wav")
        response.stream_to_file(speech_file)

        # Play using aplay to specific device
        subprocess.run(
            ["aplay", "-D", f"hw:{audio_device},0", str(speech_file)],
            check=True,
            capture_output=True
        )

        print("✅ Speech playback complete")

    except subprocess.CalledProcessError as e:
        print(f"❌ Audio playback error: {e}")
        print(f"   stderr: {e.stderr.decode() if e.stderr else 'N/A'}")
    except Exception as e:
        print(f"❌ TTS error: {e}")
