import time
import sounddevice as sd
import soundfile as sf
import numpy as np


def list_devices() -> None:
    for i, d in enumerate(sd.query_devices()):
        print(f"{i}: {d['name']} (in:{d['max_input_channels']}, out:{d['max_output_channels']})")


def record_wav(path: str, seconds: float, samplerate: int, device: int | None) -> None:
    print(f"Recording {seconds}s @ {samplerate}Hz to {path} (device={device})...")
    audio = sd.rec(int(seconds * samplerate), samplerate=samplerate, channels=1, dtype="float32", device=device)
    sd.wait()
    sf.write(path, audio, samplerate)
    print("Saved:", path)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Record microphone to a WAV file")
    parser.add_argument("--seconds", type=float, default=3.0)
    parser.add_argument("--samplerate", type=int, default=16000)
    parser.add_argument("--device", type=int, default=None, help="Input device index (see list)")
    parser.add_argument("--out", default="test.wav")
    parser.add_argument("--list", action="store_true", help="List audio devices and exit")
    args = parser.parse_args()

    if args.list:
        list_devices()
        return

    record_wav(args.out, args.seconds, args.samplerate, args.device)


if __name__ == "__main__":
    main()





