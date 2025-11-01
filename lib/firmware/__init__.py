import time
import atexit

try:
    import lgpio
except ImportError:
    from . import lgpio_mock as lgpio

# GPIO chip handle (global)
h = None

# Pin definitions
MOTOR_DIR_PINS = [17, 22, 23, 24]
MOTOR_PWM_PINS = [12, 13]

def start():
    """Initialize GPIO - call once at startup"""
    global h
    if h is None:
        h = lgpio.gpiochip_open(4)  # RPi 5 uses gpiochip4

        # Set up direction pins as outputs
        for pin in MOTOR_DIR_PINS:
            lgpio.gpio_claim_output(h, pin)

        # Set up PWM pins
        for pin in MOTOR_PWM_PINS:
            lgpio.gpio_claim_output(h, pin)

        # Register cleanup on exit
        atexit.register(_cleanup)

def stop():
    """Stop all motors"""
    if h is not None:
        lgpio.tx_pwm(h, 12, 1000, 0)
        lgpio.tx_pwm(h, 13, 1000, 0)
        for pin in MOTOR_DIR_PINS:
            lgpio.gpio_write(h, pin, 0)

def _cleanup():
    """Internal cleanup - called automatically on exit"""
    global h
    if h is not None:
        stop()
        lgpio.gpiochip_close(h)
        h = None

def _set_motors(pin17, pin22, pin23, pin24, pw=100):
    """Internal helper to set motor directions and PWM"""
    lgpio.gpio_write(h, 17, pin17)
    lgpio.gpio_write(h, 22, pin22)
    lgpio.gpio_write(h, 23, pin23)
    lgpio.gpio_write(h, 24, pin24)

    # Set PWM duty cycle (pw is already 0-100 percentage)
    lgpio.tx_pwm(h, 12, 1000, pw)  # 1kHz frequency, duty cycle 0-100%
    lgpio.tx_pwm(h, 13, 1000, pw)

def forward(sec, pw=50):
    """Move forward for specified seconds at given power (0-100)"""
    _set_motors(0, 1, 0, 1, pw)
    time.sleep(sec)
    stop()

def left_turn(sec, pw=50):
    """Turn left for specified seconds at given power (0-100)"""
    _set_motors(0, 1, 1, 0, pw)
    time.sleep(sec)
    stop()

def reverse(sec, pw=50):
    """Move backward for specified seconds at given power (0-100)"""
    _set_motors(1, 0, 1, 0, pw)
    time.sleep(sec)
    stop()

def right_turn(sec, pw=50):
    """Turn right for specified seconds at given power (0-100)"""
    _set_motors(1, 0, 0, 1, pw)
    time.sleep(sec)
    stop()  