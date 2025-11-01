"""
Audio device detection utilities for ALSA
"""
import subprocess
import re
from typing import Optional


def detect_usb_audio_device() -> Optional[int]:
    """
    Auto-detect USB audio output device by parsing aplay -l output.
    Looks for devices with "USB" in their description.

    Returns:
        Card number of USB audio device, or None if not found
    """
    try:
        result = subprocess.run(
            ["aplay", "-l"],
            capture_output=True,
            text=True,
            check=True
        )

        # Parse output line by line
        # Format: "card 1: UACDemoV10 [UACDemoV1.0], device 0: USB Audio [USB Audio]"
        for line in result.stdout.split('\n'):
            # Look for lines starting with "card" that contain "USB"
            if line.startswith('card') and 'USB' in line.upper():
                match = re.match(r'^card (\d+):', line)
                if match:
                    card_num = int(match.group(1))
                    # Extract device name for logging
                    name_match = re.search(r'\[([^\]]+)\]', line)
                    device_name = name_match.group(1) if name_match else "Unknown"
                    print(f"🔊 Auto-detected USB audio device: card {card_num} [{device_name}]")
                    return card_num

        print("⚠️  No USB audio device found")
        return None

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to detect audio devices: {e}")
        return None
    except Exception as e:
        print(f"❌ Audio device detection error: {e}")
        return None


def get_audio_device() -> int:
    """
    Get the audio output device card number.

    Strategy:
    1. Auto-detect USB audio device
    2. Fallback to card 1

    Returns:
        ALSA card number for audio output
    """
    device = detect_usb_audio_device()
    if device is not None:
        return device

    # Final fallback
    print("⚠️  Using fallback audio device: card 1")
    return 1
