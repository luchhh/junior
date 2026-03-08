import atexit
from datetime import datetime

from lib.command_queue import CommandQueue

try:
    import lgpio
except ImportError:
    from . import lgpio_mock as lgpio

MOTOR_DIR_PINS = [17, 22, 23, 24]
MOTOR_PWM_PINS = [12, 13]


class Firmware:
    def __init__(self):
        self._h = lgpio.gpiochip_open(4)  # RPi 5 uses gpiochip4
        self._queue = CommandQueue("FirmwareQueue")

        for pin in MOTOR_DIR_PINS:
            lgpio.gpio_claim_output(self._h, pin)
        for pin in MOTOR_PWM_PINS:
            lgpio.gpio_claim_output(self._h, pin)

        atexit.register(self._cleanup)

    def forward(self, sec: float, pw: int = 100) -> None:
        print(f"[FIRMWARE - {datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Moving forward for {sec} seconds at {pw}% power")
        self._queue.enqueue(self._set_motors, 0, 1, 0, 1, pw)
        self._queue.enqueue(self._stop_motors, delay=sec)

    def reverse(self, sec: float, pw: int = 100) -> None:
        print(f"[FIRMWARE - {datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Moving backward for {sec} seconds at {pw}% power")
        self._queue.enqueue(self._set_motors, 1, 0, 1, 0, pw)
        self._queue.enqueue(self._stop_motors, delay=sec)

    def left_turn(self, sec: float, pw: int = 100) -> None:
        print(f"[FIRMWARE - {datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Turning left for {sec} seconds at {pw}% power")
        self._queue.enqueue(self._set_motors, 0, 1, 1, 0, pw)
        self._queue.enqueue(self._stop_motors, delay=sec)

    def right_turn(self, sec: float, pw: int = 100) -> None:
        print(f"[FIRMWARE - {datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Turning right for {sec} seconds at {pw}% power")
        self._queue.enqueue(self._set_motors, 1, 0, 0, 1, pw)
        self._queue.enqueue(self._stop_motors, delay=sec)

    def stop(self) -> None:
        self._queue.clear()
        self._stop_motors()

    def clear(self) -> None:
        self._queue.clear()
        self._stop_motors()

    def _set_motors(self, pin17: int, pin22: int, pin23: int, pin24: int, pw: int = 100) -> None:
        lgpio.gpio_write(self._h, 17, pin17)
        lgpio.gpio_write(self._h, 22, pin22)
        lgpio.gpio_write(self._h, 23, pin23)
        lgpio.gpio_write(self._h, 24, pin24)
        lgpio.tx_pwm(self._h, 12, 1000, pw)
        lgpio.tx_pwm(self._h, 13, 1000, pw)

    def _stop_motors(self) -> None:
        print(f"[FIRMWARE - {datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Stopping motors")
        lgpio.tx_pwm(self._h, 12, 1000, 0)
        lgpio.tx_pwm(self._h, 13, 1000, 0)
        for pin in MOTOR_DIR_PINS:
            lgpio.gpio_write(self._h, pin, 0)

    def _cleanup(self) -> None:
        self.stop()
        lgpio.gpiochip_close(self._h)
