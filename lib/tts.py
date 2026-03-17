"""
Text-to-Speech module supporting both OpenAI TTS API and local Piper TTS
"""
import subprocess
from pathlib import Path
from openai import OpenAI
import os
from typing import Optional
import numpy as np
import sounddevice as sd
import soundfile as sf
from math import gcd
from scipy.signal import resample_poly
from .audio_device import get_output_device


PIPER_MODEL_PATH = os.path.expanduser("~/piper-voices/en_US-lessac-medium.onnx")


class TextToSpeech:
    """Text-to-Speech service with pluggable backends"""

    def __init__(self, backend: str = "piper", api_key: Optional[str] = None):
        if backend not in ["piper", "openai"]:
            raise ValueError(f"Unknown TTS backend: {backend}. Choose 'piper' or 'openai'")

        self.backend = backend
        self.audio_device = get_output_device()
        self._client = OpenAI(api_key=api_key) if backend == "openai" else None
        print(f"🗣️  TTS initialized: {backend} backend, audio device {self.audio_device}")

    def _play_wav(self, path: Path) -> None:
        """Play a WAV file through the configured output device, resampling if needed."""
        data, file_sr = sf.read(str(path), dtype="float32")
        device_info = sd.query_devices(self.audio_device) if self.audio_device is not None else sd.query_devices(kind="output")
        device_sr = int(device_info["default_samplerate"])
        if file_sr != device_sr:
            g = gcd(file_sr, device_sr)
            data = resample_poly(data, device_sr // g, file_sr // g).astype(np.float32)
        sd.play(data, samplerate=device_sr, device=self.audio_device)
        sd.wait()

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
            self._play_wav(speech_file)
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
            response = self._client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text,
                response_format="wav"
            )

            speech_file = Path("/tmp/robot_speech.wav")
            response.stream_to_file(speech_file)
            self._play_wav(speech_file)
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
