#!/usr/bin/env python3

import argparse
from lib.sttt import SpeechToTextTranscriber, VAD_THRESHOLD


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transcribe microphone audio with faster-whisper")
    parser.add_argument("--model", default="small", help="Whisper model: tiny (fastest), small (balanced), medium (best quality)")
    parser.add_argument("--language", default="en", help="Language code (e.g., en, es, fr)")
    parser.add_argument("--vad-threshold", type=float, default=VAD_THRESHOLD, help=f"Voice activity detection threshold (default: {VAD_THRESHOLD})")
    return parser.parse_args()


def main():
    print("VERSION 0.1")
    args = parse_arguments()

    # Create transcriber instance
    transcriber = SpeechToTextTranscriber(args.model, args.language, args.vad_threshold)

    # Define callback function for transcription results
    def on_transcription(text: str):
        print("Transcription:", text)

    try:
        transcriber.call(on_transcription)
    except KeyboardInterrupt:
        print("\nStopped by user.")


if __name__ == "__main__":
    main()