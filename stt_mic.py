import argparse
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
VAD_THRESHOLD = 0.05 # Energy threshold for voice activity detection (higher = more selective)
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


def create_whisper_model(model_name: str) -> WhisperModel:
    print(f"Loading model: {model_name}...")
    return WhisperModel(model_name, compute_type=AUDIO_DTYPE)


def is_voice(audio: np.ndarray) -> bool:
    energy = float(np.mean(np.abs(audio)))
    return energy > VAD_THRESHOLD


def is_min_duration(audio: np.ndarray) -> bool:
    return audio.shape[0] > int(SAMPLE_RATE * MIN_AUDIO_DURATION_SECONDS)


# Defensive coding to ensure the audio is mono, even if we ask for mono
# the hardware, driver, etc. might return stereo audio
def ensure_mono(audio: np.ndarray) -> np.ndarray:
    if audio.ndim == 2:
        return audio[:, 0]
    return audio


# Normalize the audio to the valid range of -1.0 to 1.0
def normalize_audio(audio: np.ndarray) -> np.ndarray:
    return np.clip(np.nan_to_num(audio), -1.0, 1.0)


def process_audio_segment(audio: np.ndarray, model: WhisperModel, language: str) -> Optional[str]:
    print("Processing audio segment...", audio.shape, audio.size)
    mono = ensure_mono(audio)
    mono = normalize_audio(mono)
    
    try:
        segments, _ = model.transcribe(mono, beam_size=1, vad_filter=True, language=language)
        text = "".join(s.text for s in segments).strip()
        return text if text else None
    except Exception as e:
        print(f"Transcription error: {e}", file=sys.stderr)
        return None


def process_audio_stream(audio_stream, model: WhisperModel, language: str):
    """
    Process audio from any stream source (microphone, file, test data)
    audio_stream should have a read_all() method that returns Optional[np.ndarray]
    """
    print("Listening... Press Ctrl+C to stop.")
    buffer: list[np.ndarray] = []
    last_voice_time: Optional[float] = None
    
    while True:
        data = audio_stream.read_all()
        if data is None:
            time.sleep(0.01)
            continue
        
        buffer.append(data)
        
        if is_voice(data):
            last_voice_time = time.monotonic()
        
        # Only check for silence after we've detected voice at least once
        if last_voice_time is not None:
            now = time.monotonic()
            silence_after_voice_ms = (now - last_voice_time) * 1000
            
            if silence_after_voice_ms >= SILENCE_THRESHOLD_MS:
                audio = np.concatenate(buffer)
                
                # Only process if we have enough audio duration
                if is_min_duration(audio):
                    buffer.clear()
                    last_voice_time = None  # Reset voice detection after processing
                    text = process_audio_segment(audio, model, language)
                    if text and len(text.strip()) > 0:
                        print(f"Transcribed: {text}")
                # Otherwise keep accumulating audio in buffer


def transcribe_realtime(model: WhisperModel, language: str):
    """Transcribe from microphone in real-time"""
    stream = AudioStream(SAMPLE_RATE)
    
    with sd.InputStream(
        channels=CHANNELS,
        samplerate=SAMPLE_RATE,
        dtype=AUDIO_DTYPE,
        callback=stream.callback,
    ):
        process_audio_stream(stream, model, language)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transcribe microphone audio with faster-whisper")
    parser.add_argument("--model", default="small", help="Whisper model: tiny (fastest), small (balanced), medium (best quality)")
    parser.add_argument("--language", default="en", help="Language code (e.g., en, es, fr)")
    return parser.parse_args()


def main():
    print("VERSION 0.1")
    args = parse_arguments()
    model = create_whisper_model(args.model)
    
    try:
        transcribe_realtime(model, language=args.language)
    except KeyboardInterrupt:
        print("\nStopped by user.")


if __name__ == "__main__":
    main()


