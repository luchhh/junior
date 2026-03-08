import threading
import queue
import time


class CommandQueue:
    def __init__(self, name: str = "CommandQueue"):
        self.name = name
        self._queue = queue.Queue()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def enqueue(self, func, *args, delay: float = 0.0, **kwargs):
        """Add a command. delay = seconds to wait before executing."""
        self._queue.put((delay, func, args, kwargs))

    def clear(self):
        """Flush all pending commands (e.g. on new voice interrupt)."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except queue.Empty:
                break

    def _worker(self):
        while True:
            delay, func, args, kwargs = self._queue.get()
            if delay > 0:
                time.sleep(delay)
            try:
                func(*args, **kwargs)
            except Exception as e:
                print(f"[{self.name}] Error: {e}")
            self._queue.task_done()
