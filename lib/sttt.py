import sys
from datetime import datetime
from typing import Optional

import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel

from .audio_capture import AudioCapture, VAD_THRESHOLD


class SpeechToTextTranscriber:
    """
    Speech-to-text service using AudioCapture + Whisper.

    Combines audio capture with local Whisper transcription.
    """

    def __init__(self, model_name: str, language: str, vad_threshold: float = VAD_THRESHOLD):
        self.audio_capture = AudioCapture(vad_threshold)
        self.model = self._create_whisper_model(model_name)
        self.language = language
        print(f"Initialized SpeechToTextTranscriber with model: {model_name}, language: {language}")

    def _create_whisper_model(self, model_name: str) -> WhisperModel:
        print(f"Loading model: {model_name}...")
        return WhisperModel(
            model_name,
            device="cpu",
            compute_type="int8",  # Faster on CPU, especially Raspberry Pi
            cpu_threads=4,  # Use all 4 cores of Raspberry Pi 5
            num_workers=1
        )

    def _transcribe_audio(self, audio: np.ndarray, sample_rate: int) -> Optional[str]:
        """Transcribe audio using Whisper"""
        # Debug: save audio sample
        sf.write('/tmp/debug_audio.wav', audio, sample_rate)
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Saved debug audio to /tmp/debug_audio.wav (shape: {audio.shape}, min: {audio.min():.4f}, max: {audio.max():.4f})")

        try:
            transcribe_start = datetime.now()
            segments, _ = self.model.transcribe(
                audio,
                beam_size=1,
                vad_filter=False,  # Disabled - we already do VAD before transcription
                language=self.language
            )
            text = "".join(s.text for s in segments).strip()
            transcribe_end = datetime.now()
            print(f"[{transcribe_end.strftime('%H:%M:%S.%f')[:-3]}] Transcription took {(transcribe_end - transcribe_start).total_seconds():.2f}s")
            return text if text else None
        except Exception as e:
            print(f"Transcription error: {e}", file=sys.stderr)
            return None

    def call(self, transcription_callback, device: int = 0):
        """
        Start real-time transcription from microphone.

        Args:
            transcription_callback: Function that takes transcribed text string
            device: Audio input device index (default: 0)
        """
        def on_audio_captured(audio: np.ndarray, sample_rate: int):
            """Called by AudioCapture when audio segment is ready"""
            text = self._transcribe_audio(audio, sample_rate)
            if text and len(text.strip()) > 0:
                transcription_callback(text)
            else:
                print(f"No transcription result (got: '{text}')")

        # Use AudioCapture to get audio segments, then transcribe them
        self.audio_capture.capture(on_audio_captured, device=device)
