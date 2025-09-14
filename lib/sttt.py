import queue
import sys
import time
from typing import Optional

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel


SAMPLE_RATE = 16000
CHANNELS = 1 # Asking for mono
AUDIO_DTYPE = "float32"  # Audio data type for consistency between input and model
VAD_THRESHOLD = 0.01 # Energy threshold for voice activity detection (higher = more selective)
SILENCE_THRESHOLD_MS = 800 # Silence threshold in milliseconds
MIN_AUDIO_DURATION_SECONDS = 0.5 # Minimum audio length to process

class AudioStream:
    def __init__(self, sample_rate: int):
        self.sample_rate = sample_rate
        self.audio_queue: queue.Queue[np.ndarray] = queue.Queue()

    def callback(self, indata, frames, time_info, status):
        if status:
            print(status, file=sys.stderr)
        self.audio_queue.put(indata.copy())

    def read_all(self) -> Optional[np.ndarray]:
        chunks = []
        try:
            while True:
                # get_nowait sends a queue.Empty exception when is empty
                # so we stop the loop
                chunks.append(self.audio_queue.get_nowait())
        except queue.Empty:
            pass

        if not chunks:
            return None
        return np.concatenate(chunks)


class SpeechToTextTranscriber:
    def __init__(self, model_name: str, language: str, vad_threshold: float = VAD_THRESHOLD):
        self.model = self._create_whisper_model(model_name)
        self.language = language
        self.vad_threshold = vad_threshold
        self.sample_rate = SAMPLE_RATE
        print(f"Initialized SpeechToTextTranscriber with model: {model_name}, language: {language}, vad_threshold: {vad_threshold}")

    def _create_whisper_model(self, model_name: str) -> WhisperModel:
        print(f"Loading model: {model_name}...")
        return WhisperModel(model_name, compute_type=AUDIO_DTYPE)

    def _is_voice(self, audio: np.ndarray) -> bool:
        energy = float(np.mean(np.abs(audio)))
        return energy > self.vad_threshold

    def _is_min_duration(self, audio: np.ndarray) -> bool:
        return audio.shape[0] > int(self.sample_rate * MIN_AUDIO_DURATION_SECONDS)

    def _ensure_mono(self, audio: np.ndarray) -> np.ndarray:
        if audio.ndim == 2:
            return audio[:, 0]
        return audio

    def _normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        return np.clip(np.nan_to_num(audio), -1.0, 1.0)

    def _process_audio_segment(self, audio: np.ndarray) -> Optional[str]:
        mono = self._ensure_mono(audio)
        mono = self._normalize_audio(mono)

        try:
            segments, _ = self.model.transcribe(mono, beam_size=1, vad_filter=True, language=self.language)
            text = "".join(s.text for s in segments).strip()
            return text if text else None
        except Exception as e:
            print(f"Transcription error: {e}", file=sys.stderr)
            return None

    def call(self, transcription_callback):
        """
        Start real-time transcription from microphone
        transcription_callback: function that takes a string parameter (the transcribed text)
        """
        print("Listening... Press Ctrl+C to stop.")

        audio_stream = AudioStream(self.sample_rate)
        buffer: list[np.ndarray] = []
        last_voice_time: Optional[float] = None

        with sd.InputStream(
            channels=CHANNELS,
            samplerate=self.sample_rate,
            dtype=AUDIO_DTYPE,
            callback=audio_stream.callback,
        ):
            while True:
                data = audio_stream.read_all()
                if data is None:
                    time.sleep(0.01)
                    continue

                buffer.append(data)
                if self._is_voice(data):
                    last_voice_time = time.monotonic()

                # Only check for silence after we've detected voice at least once
                if last_voice_time is not None:
                    now = time.monotonic()
                    silence_after_voice_ms = (now - last_voice_time) * 1000

                    if silence_after_voice_ms >= SILENCE_THRESHOLD_MS:
                        audio = np.concatenate(buffer)

                        # Only process if we have enough audio duration
                        if self._is_min_duration(audio):
                            buffer.clear()
                            last_voice_time = None  # Reset voice detection after processing
                            text = self._process_audio_segment(audio)
                            if text and len(text.strip()) > 0:
                                transcription_callback(text)
                        # Otherwise keep accumulating audio in buffer




