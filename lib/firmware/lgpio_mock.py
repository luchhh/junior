"""
Mock lgpio module for local development.
On Raspberry Pi, install with: sudo apt-get install python3-lgpio
"""

def gpiochip_open(chip):
    """Mock: Open GPIO chip"""
    print(f"[MOCK] Opening gpiochip{chip}")
    return chip

def gpiochip_close(handle):
    """Mock: Close GPIO chip"""
    print(f"[MOCK] Closing gpiochip (handle={handle})")

def gpio_claim_output(handle, pin, level=0):
    """Mock: Claim GPIO pin as output"""
    print(f"[MOCK] Claiming GPIO {pin} as output (handle={handle})")

def gpio_write(handle, pin, level):
    """Mock: Write to GPIO pin"""
    print(f"[MOCK] GPIO {pin} = {level}")

def tx_pwm(handle, pin, freq, duty_cycle):
    """Mock: Set PWM output"""
    print(f"[MOCK] PWM GPIO {pin}: {freq}Hz, duty={duty_cycle}/255 ({duty_cycle/255*100:.1f}%)")
