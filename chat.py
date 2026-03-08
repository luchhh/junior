#!/usr/bin/env python3

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
from lib.firmware import Firmware
from lib.gpt import GPT
from lib.sources import MicrophoneSource, VAD_THRESHOLD
from lib.tts import TextToSpeech
from lib.robot import Robot


def load_system_prompt() -> str:
    system_path = Path("prompts/system.md")
    if not system_path.exists():
        raise FileNotFoundError(f"System prompt file not found: {system_path}")
    return system_path.read_text(encoding="utf-8").strip()


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Voice-controlled robot using STT and GPT")
    parser.add_argument("--language", default="en", help="Language code (e.g., en, es, fr)")
    parser.add_argument("--vad-threshold", type=float, default=VAD_THRESHOLD, help=f"Voice activity detection threshold (default: {VAD_THRESHOLD})")
    parser.add_argument("--stt", choices=["whisper", "openai"], default="openai", help="Speech-to-text backend: whisper (local) or openai (cloud GPT-4o Audio)")
    parser.add_argument("--tts", choices=["piper", "openai"], default="openai", help="Text-to-speech backend: piper (local) or openai (cloud)")
    return parser.parse_args()


def main():
    load_dotenv()
    print("VERSION 0.2")
    args = parse_arguments()

    tts = TextToSpeech(backend=args.tts)
    system_prompt = load_system_prompt()
    print("🤖 Robot system loaded!")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to your environment or .env file.")

    source = MicrophoneSource(args.vad_threshold)
    robot = Robot(tts, system_prompt, source, GPT(api_key), Firmware(), stt=args.stt, language=args.language)

    try:
        robot.run()
    except KeyboardInterrupt:
        print("\nStopped by user.")


if __name__ == "__main__":
    main()
