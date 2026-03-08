#!/usr/bin/env python3

import argparse
from lib.sources import MicrophoneSource, VAD_THRESHOLD
from lib.sttt import SpeechToTextTranscriber


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transcribe microphone audio with faster-whisper")
    parser.add_argument("--language", default="en", help="Language code (e.g., en, es, fr)")
    parser.add_argument("--vad-threshold", type=float, default=VAD_THRESHOLD, help=f"Voice activity detection threshold (default: {VAD_THRESHOLD})")
    return parser.parse_args()


def main():
    print("VERSION 0.1")
    args = parse_arguments()

    source = MicrophoneSource(args.vad_threshold)
    transcriber = SpeechToTextTranscriber(args.language)

    try:
        for audio, sr in source:
            text = transcriber.transcribe(audio, sr)
            if text:
                print("Transcription:", text)
    except KeyboardInterrupt:
        print("\nStopped by user.")


if __name__ == "__main__":
    main()
