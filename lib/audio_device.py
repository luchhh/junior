"""
Audio device detection utilities
"""
from typing import Optional

import sounddevice as sd


def get_input_device() -> Optional[int]:
    """
    Find the input (microphone) device index.
    Looks for the first USB device with input channels.
    Falls back to None (system default).
    """
    for i, d in enumerate(sd.query_devices()):
        if "USB" in d["name"].upper() and d["max_input_channels"] > 0:
            print(f"🎤 Auto-detected USB microphone: [{i}] {d['name']}")
            return i

    print("⚠️  No USB microphone found, using system default")
    return None


def get_output_device() -> Optional[int]:
    """
    Find the output (speaker) device index.
    Looks for the first USB device with output channels.
    Falls back to None (system default).
    """
    for i, d in enumerate(sd.query_devices()):
        if "USB" in d["name"].upper() and d["max_output_channels"] > 0:
            print(f"🔊 Auto-detected USB speaker: [{i}] {d['name']}")
            return i

    print("⚠️  No USB speaker found, using system default")
    return None
