import queue
import sys
import threading
from datetime import datetime

import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel

from .audio_capture import AudioCapture, VAD_THRESHOLD


class SpeechToTextTranscriber:
    """
    Speech-to-text service using AudioCapture + Whisper.

    Combines audio capture with local Whisper transcription.
    Uses "small" model (best balance of speed/accuracy for Raspberry Pi 5).
    """

    def __init__(self, language: str, vad_threshold: float = VAD_THRESHOLD):
        self.audio_capture = AudioCapture(vad_threshold)
        self.model = self._create_whisper_model()
        self.language = language
        self._queue: queue.Queue = queue.Queue()
        self._thread: threading.Thread | None = None
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

    def _transcribe_audio(self, audio: np.ndarray, sample_rate: int) -> str | None:
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

    def _run(self):
        def on_audio_captured(audio: np.ndarray, sample_rate: int):
            text = self._transcribe_audio(audio, sample_rate)
            if text and len(text.strip()) > 0:
                self._queue.put(text)
            else:
                print(f"No transcription result (got: '{text}')")

        self.audio_capture.capture(on_audio_captured)

    def pause(self):
        self.audio_capture.pause()

    def resume(self):
        self.audio_capture.resume()

    def __iter__(self):
        if self._thread is None:
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

        while True:
            try:
                yield self._queue.get(timeout=1.0)
            except queue.Empty:
                if not self._thread.is_alive():
                    raise RuntimeError("Transcription thread died unexpectedly")
