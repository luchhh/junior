import sys
from datetime import datetime
from typing import Optional

import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel

from .audio_capture import VAD_THRESHOLD


class SpeechToTextTranscriber:
    """
    Transcription service using local Whisper.
    Receives audio data and returns transcribed text.
    Uses "small" model (best balance of speed/accuracy for Raspberry Pi 5).
    """

    def __init__(self, language: str):
        self.language = language
        self.model = self._create_whisper_model()
        print(f"Initialized SpeechToTextTranscriber with model: small, language: {language}")

    def _create_whisper_model(self) -> WhisperModel:
        print("Loading Whisper model: small...")
        return WhisperModel(
            "small",
            device="cpu",
            compute_type="int8",  # Faster on CPU, especially Raspberry Pi
            cpu_threads=4,  # Use all 4 cores of Raspberry Pi 5
            num_workers=1
        )

    def transcribe(self, audio: np.ndarray, sample_rate: int) -> Optional[str]:
        """Transcribe audio and return text, or None if nothing detected."""
        sf.write('/tmp/debug_audio.wav', audio, sample_rate)
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Saved debug audio to /tmp/debug_audio.wav (shape: {audio.shape}, min: {audio.min():.4f}, max: {audio.max():.4f})")

        try:
            transcribe_start = datetime.now()
            segments, _ = self.model.transcribe(
                audio,
                beam_size=1,
                vad_filter=False,
                language=self.language
            )
            text = "".join(s.text for s in segments).strip()
            transcribe_end = datetime.now()
            print(f"[{transcribe_end.strftime('%H:%M:%S.%f')[:-3]}] Transcription took {(transcribe_end - transcribe_start).total_seconds():.2f}s")
            return text if text else None
        except Exception as e:
            print(f"Transcription error: {e}", file=sys.stderr)
            return None
