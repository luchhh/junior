#!/usr/bin/env python3

from lib.gpt import chat
from pathlib import Path
import argparse
import sys
from lib.sttt import SpeechToTextTranscriber, VAD_THRESHOLD

def load_system_prompt() -> str:
    """Load the robot system prompt from prompts/system.md"""
    system_path = Path("prompts/system.md")
    if not system_path.exists():
        raise FileNotFoundError(f"System prompt file not found: {system_path}")
    return system_path.read_text(encoding="utf-8").strip()


def process_transcription_with_chat(transcribed_text: str, system_prompt: str) -> None:
    """Send transcribed text to chat and print the response"""
    try:
        print(f"🎤 Transcribed: {transcribed_text}")
        response = chat(system_prompt, transcribed_text)
        print(f"🤖 Robot response: {response}")
    except Exception as e:
        print(f"❌ Chat error: {e}", file=sys.stderr)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transcribe microphone audio with faster-whisper")
    parser.add_argument("--model", default="small", help="Whisper model: tiny (fastest), small (balanced), medium (best quality)")
    parser.add_argument("--language", default="es", help="Language code (e.g., en, es, fr)")
    parser.add_argument("--vad-threshold", type=float, default=VAD_THRESHOLD, help=f"Voice activity detection threshold (default: {VAD_THRESHOLD})")
    return parser.parse_args()


def main():
    print("VERSION 0.1")
    args = parse_arguments()

    # Create transcriber instance
    transcriber = SpeechToTextTranscriber(args.model, args.language, args.vad_threshold)


    # Load system prompt for robot commands
    system_prompt = load_system_prompt()
    print("🤖 Robot system loaded!")

    # Define callback function for transcription results
    def on_transcription(text: str):
        process_transcription_with_chat(text, system_prompt)

    try:
        transcriber.call(on_transcription)
    except KeyboardInterrupt:
        print("\nStopped by user.")

if __name__ == "__main__":
    main()