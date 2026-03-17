import queue
import threading
from typing import Iterator

import numpy as np

from .audio_capture import AudioCapture, VAD_THRESHOLD
from .audio_device import get_input_device


class MicrophoneSource:
    """
    Iterable audio source backed by the microphone.
    Yields (audio: np.ndarray, sample_rate: int) tuples — one per speech segment.
    Supports pause()/resume() for TTS feedback prevention.

    A future FileSource can replace this as a drop-in.
    """

    def __init__(self, vad_threshold: float = VAD_THRESHOLD):
        self._capture = AudioCapture(vad_threshold)
        self._device = get_input_device()
        self._queue: queue.Queue = queue.Queue()
        self._thread: threading.Thread | None = None

    def pause(self):
        self._capture.pause()

    def resume(self):
        self._capture.resume()

    def __iter__(self) -> Iterator[tuple[np.ndarray, int]]:
        if self._thread is None:
            self._thread = threading.Thread(
                target=self._capture.capture,
                args=(lambda audio, sr: self._queue.put((audio, sr)),),
                kwargs={"device": self._device},
                daemon=True,
            )
            self._thread.start()

        while True:
            try:
                yield self._queue.get(timeout=1.0)
            except queue.Empty:
                if not self._thread.is_alive():
                    raise RuntimeError("Audio capture thread died unexpectedly")
