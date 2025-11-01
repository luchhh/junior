"""
Text-to-Speech module supporting both OpenAI TTS API and local Piper TTS
"""
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import os
from typing import Optional
from .audio_device import get_audio_device


PIPER_MODEL_PATH = os.path.expanduser("~/piper-voices/en_US-lessac-medium.onnx")


class TextToSpeech:
    """Text-to-Speech service with pluggable backends"""

    def __init__(self, backend: str = "piper"):
        """
        Initialize TTS service.

        Args:
            backend: "piper" for local TTS or "openai" for cloud TTS
        """
        if backend not in ["piper", "openai"]:
            raise ValueError(f"Unknown TTS backend: {backend}. Choose 'piper' or 'openai'")

        self.backend = backend
        self.audio_device = get_audio_device()
        print(f"🗣️  TTS initialized: {backend} backend, audio device {self.audio_device}")

    def _get_openai_client(self) -> OpenAI:
        """Create and return an OpenAI client using the API key from env."""
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Add it to your environment or .env file."
            )
        return OpenAI(api_key=api_key)

    def _speak_piper(self, text: str) -> None:
        """Generate speech using local Piper TTS"""
        from datetime import datetime

        speech_file = Path("/tmp/robot_speech.wav")

        try:
            # Generate speech with Piper
            gen_start = datetime.now()
            with open(speech_file, "wb") as f:
                subprocess.run(
                    ["piper", "--model", PIPER_MODEL_PATH, "--output_file", "-"],
                    input=text.encode("utf-8"),
                    stdout=f,
                    check=True,
                    stderr=subprocess.PIPE
                )
            gen_end = datetime.now()
            gen_time = (gen_end - gen_start).total_seconds()
            print(f"⏱️  Piper generation: {gen_time:.3f}s")

            # Play audio
            play_start = datetime.now()
            subprocess.run(
                ["aplay", "-D", f"plughw:{self.audio_device},0", str(speech_file)],
                check=True,
                capture_output=True
            )
            play_end = datetime.now()
            play_time = (play_end - play_start).total_seconds()
            total_time = (play_end - gen_start).total_seconds()
            print(f"⏱️  Audio playback: {play_time:.3f}s")
            print(f"⏱️  Total TTS time: {total_time:.3f}s")
        except subprocess.CalledProcessError as e:
            print(f"❌ Piper TTS error: {e}")
            print(f"   stderr: {e.stderr.decode() if e.stderr else 'N/A'}")

    def _speak_openai(self, text: str, voice: str = "alloy") -> None:
        """Generate speech using OpenAI TTS API"""
        try:
            client = self._get_openai_client()
            response = client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text,
                response_format="wav"
            )

            speech_file = Path("/tmp/robot_speech.wav")
            response.stream_to_file(speech_file)

            # Play using aplay to specific device
            subprocess.run(
                ["aplay", "-D", f"plughw:{self.audio_device},0", str(speech_file)],
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            print(f"❌ Audio playback error: {e}")
            print(f"   stderr: {e.stderr.decode() if e.stderr else 'N/A'}")
        except Exception as e:
            print(f"❌ OpenAI TTS error: {e}")

    def speak(self, text: str, voice: str = "alloy") -> None:
        """
        Convert text to speech and play it through the speaker.

        Args:
            text: Text to convert to speech
            voice: OpenAI TTS voice (alloy, echo, fable, onyx, nova, shimmer) - only used for OpenAI backend
        """
        if not text or len(text.strip()) == 0:
            print("⚠️  Empty text, skipping TTS")
            return

        print(f"🗣️  Speaking ({self.backend}): {text}")

        try:
            if self.backend == "piper":
                self._speak_piper(text)
            elif self.backend == "openai":
                self._speak_openai(text, voice)

            print("✅ Speech playback complete")

        except Exception as e:
            print(f"❌ TTS error: {e}")
