import queue
import sys
import time
from datetime import datetime
from fractions import Fraction
from typing import Optional, Callable

import numpy as np
import sounddevice as sd
from scipy import signal


SAMPLE_RATE = 16000
FALLBACK_SAMPLE_RATES = [16000, 44100, 48000, 8000]  # Try these in order
CHANNELS = 1  # Asking for mono
AUDIO_DTYPE = "float32"  # Audio data type for sounddevice input stream
VAD_THRESHOLD = 0.0035  # Energy threshold for voice activity detection (higher = more selective)
SILENCE_THRESHOLD_MS = 800  # Silence threshold in milliseconds
MIN_AUDIO_DURATION_SECONDS = 0.5  # Minimum audio length to process


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


class AudioCapture:
    """
    Pure audio capture service with Voice Activity Detection (VAD).

    Captures audio from microphone, detects voice activity, segments speech,
    and delivers preprocessed audio chunks via callback.
    """

    def __init__(self, vad_threshold: float = VAD_THRESHOLD):
        self.vad_threshold = vad_threshold
        self.sample_rate = SAMPLE_RATE
        self.paused = False  # Flag to pause audio processing (e.g., during TTS playback)
        print(f"Initialized AudioCapture with vad_threshold: {vad_threshold}")

    def pause(self):
        """Pause audio processing (stops capturing new audio segments)"""
        self.paused = True
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] 🔇 Audio capture paused")

    def resume(self):
        """Resume audio processing"""
        self.paused = False
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] 🎤 Audio capture resumed")

    def _is_voice(self, audio: np.ndarray) -> bool:
        """Check if audio chunk contains voice based on energy threshold"""
        energy = float(np.mean(np.abs(audio)))
        return energy > self.vad_threshold

    def _is_min_duration(self, audio: np.ndarray, sample_rate: int) -> bool:
        """Check if audio meets minimum duration requirement"""
        return audio.shape[0] > int(sample_rate * MIN_AUDIO_DURATION_SECONDS)

    def _ensure_mono(self, audio: np.ndarray) -> np.ndarray:
        """Convert stereo to mono if needed"""
        if audio.ndim == 2:
            return audio[:, 0]
        return audio

    def _normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """Normalize and boost audio volume"""
        audio = np.nan_to_num(audio)

        # Auto-gain: normalize to use full dynamic range
        max_val = np.abs(audio).max()
        if max_val > 0:
            audio = audio / max_val * 0.9  # Scale to 90% to avoid clipping

        return np.clip(audio, -1.0, 1.0)

    def _resample_to_16k(self, audio: np.ndarray, orig_sample_rate: int) -> np.ndarray:
        """Resample audio to 16kHz if needed"""
        if orig_sample_rate == 16000:
            return audio
        # Use resample_poly for better quality (anti-aliasing filter)
        # 44100 -> 16000 requires downsampling by 16000/44100 = 160/441
        ratio = Fraction(16000, orig_sample_rate)
        return signal.resample_poly(audio, ratio.numerator, ratio.denominator)

    def _preprocess_audio(self, audio: np.ndarray, orig_sample_rate: int) -> np.ndarray:
        """Complete audio preprocessing pipeline"""
        preprocess_start = datetime.now()
        mono = self._ensure_mono(audio)
        mono = self._normalize_audio(mono)
        mono = self._resample_to_16k(mono, orig_sample_rate)
        preprocess_end = datetime.now()
        print(f"[{preprocess_end.strftime('%H:%M:%S.%f')[:-3]}] Preprocessing took {(preprocess_end - preprocess_start).total_seconds():.3f}s")
        return mono

    def _get_working_sample_rate(self, device: int = 0) -> int:
        """Find a working sample rate for the device"""
        for rate in FALLBACK_SAMPLE_RATES:
            try:
                sd.check_input_settings(device=device, channels=CHANNELS, samplerate=rate, dtype=AUDIO_DTYPE)
                if rate != SAMPLE_RATE:
                    print(f"Using sample rate {rate}Hz (device doesn't support {SAMPLE_RATE}Hz)")
                return rate
            except sd.PortAudioError:
                continue
        raise RuntimeError(f"No supported sample rate found for device {device}")

    def capture(self, audio_callback: Callable[[np.ndarray, int], None], device: int = 0):
        """
        Capture audio from microphone with VAD.

        Continuously monitors microphone input, detects voice activity,
        segments speech based on silence, and delivers preprocessed audio
        chunks to the callback function.

        Args:
            audio_callback: Function called with (audio: np.ndarray, sample_rate: int)
                          when a complete audio segment is captured.
                          Audio is always 16kHz mono after preprocessing.
            device: Audio input device index (default: 0)
        """
        print("Listening... Press Ctrl+C to stop.")

        # Find working sample rate for device
        working_sample_rate = self._get_working_sample_rate(device=device)
        audio_stream = AudioStream(working_sample_rate)
        buffer: list[np.ndarray] = []
        last_voice_time: Optional[float] = None
        frame_count = 0  # Counter for energy logging

        with sd.InputStream(
            device=device,
            channels=CHANNELS,
            samplerate=working_sample_rate,
            dtype=AUDIO_DTYPE,
            callback=audio_stream.callback,
        ):
            while True:
                data = audio_stream.read_all()
                if data is None:
                    time.sleep(0.01)
                    continue

                # Skip processing if paused (e.g., during TTS playback)
                if self.paused:
                    time.sleep(0.01)
                    continue

                energy = float(np.mean(np.abs(data)))
                frame_count += 1

                # Log energy periodically (even when not recording)
                if frame_count % 10 == 0:
                    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Energy: {energy:.6f}, Threshold: {self.vad_threshold:.6f}")

                if self._is_voice(data):
                    if last_voice_time is None:
                        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Voice detected! (energy: {energy:.6f})")
                    last_voice_time = time.monotonic()

                # Only append to buffer after voice has been detected
                if last_voice_time is not None:
                    buffer.append(data)
                    now = time.monotonic()
                    silence_after_voice_ms = (now - last_voice_time) * 1000

                    if silence_after_voice_ms >= SILENCE_THRESHOLD_MS:
                        audio = np.concatenate(buffer)
                        buffer.clear()  # Always clear buffer after silence
                        last_voice_time = None  # Reset voice detection

                        # Only process if we have enough audio duration
                        if self._is_min_duration(audio, working_sample_rate):
                            print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Captured {len(audio)/working_sample_rate:.2f}s of audio")

                            # Preprocess and deliver audio
                            processed_audio = self._preprocess_audio(audio, working_sample_rate)
                            audio_callback(processed_audio, 16000)  # Always 16kHz after preprocessing
                        else:
                            print(f"Audio too short ({len(audio)/working_sample_rate:.2f}s), discarded")
