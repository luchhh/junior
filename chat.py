#!/usr/bin/env python3

from lib.gpt import chat, chat_with_audio
from lib.audio_capture import AudioCapture, VAD_THRESHOLD
from lib.tts import TextToSpeech
from pathlib import Path
import argparse
import sys
import json
from datetime import datetime
from typing import Optional
import numpy as np
import soundfile as sf
from lib.sttt import SpeechToTextTranscriber
from models import Command, MovementCommand, SpeakCommand, CommandList
from pydantic import ValidationError
import lib.firmware as fw

def load_system_prompt() -> str:
    """Load the robot system prompt from prompts/system.md"""
    system_path = Path("prompts/system.md")
    if not system_path.exists():
        raise FileNotFoundError(f"System prompt file not found: {system_path}")
    return system_path.read_text(encoding="utf-8").strip()


def execute_command(cmd: Command, tts: TextToSpeech, audio_capture: Optional[AudioCapture] = None) -> None:
    """Execute a single robot command"""
    if isinstance(cmd, MovementCommand):
        sec = cmd.ms / 1000.0  # Convert milliseconds to seconds
        match cmd.command:
            case "forward":
                fw.forward(sec)
            case "backward":
                fw.reverse(sec)
            case "left":
                fw.left_turn(sec)
            case "right":
                fw.right_turn(sec)
    elif isinstance(cmd, SpeakCommand):
        # Pause audio capture to prevent feedback loop
        if audio_capture:
            audio_capture.pause()

        try:
            tts.speak(cmd.body)
        finally:
            # Always resume, even if TTS fails
            if audio_capture:
                audio_capture.resume()


def process_gpt_response(response: str, tts: TextToSpeech, audio_capture: Optional[AudioCapture] = None) -> None:
    """Parse GPT response and execute robot commands"""
    try:
        # Parse JSON response into CommandList
        response_json = json.loads(response)
        commands = CommandList(root=response_json).root

        print(f"🤖 Robot commands: {len(commands)} action(s)")
        for cmd in commands:
            if isinstance(cmd, MovementCommand):
                print(f"  → {cmd.command}: {cmd.ms}ms")
            elif isinstance(cmd, SpeakCommand):
                print(f"  → speak: {cmd.body}")
            execute_command(cmd, tts, audio_capture)

    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON response: {e}", file=sys.stderr)
    except ValidationError as e:
        print(f"❌ Invalid command format: {e}", file=sys.stderr)
    except Exception as e:
        print(f"❌ Command execution error: {e}", file=sys.stderr)


def process_transcription(transcribed_text: str, system_prompt: str, tts: TextToSpeech, audio_capture: Optional[AudioCapture] = None) -> None:
    """Send transcribed text to GPT and execute robot commands"""
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] 🎤 Transcribed: {transcribed_text}")
        gpt_start = datetime.now()
        response = chat(system_prompt, transcribed_text)
        gpt_end = datetime.now()
        print(f"[{gpt_end.strftime('%H:%M:%S.%f')[:-3]}] 🤖 GPT response: {response} (took {(gpt_end - gpt_start).total_seconds():.2f}s)")

        process_gpt_response(response, tts, audio_capture)

    except Exception as e:
        print(f"❌ Chat error: {e}", file=sys.stderr)


def process_audio(audio: np.ndarray, sample_rate: int, system_prompt: str, tts: TextToSpeech, audio_capture: Optional[AudioCapture] = None) -> None:
    """Send audio directly to GPT for transcription + command generation"""
    try:
        # Save audio to temp file
        audio_path = '/tmp/robot_command.wav'
        sf.write(audio_path, audio, sample_rate)
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Saved audio to {audio_path}")

        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] 🎤 Sending audio to GPT...")
        gpt_start = datetime.now()
        response = chat_with_audio(system_prompt, audio_path)
        gpt_end = datetime.now()
        print(f"[{gpt_end.strftime('%H:%M:%S.%f')[:-3]}] 🤖 GPT response: {response} (took {(gpt_end - gpt_start).total_seconds():.2f}s)")

        process_gpt_response(response, tts, audio_capture)

    except Exception as e:
        print(f"❌ Chat error: {e}", file=sys.stderr)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Voice-controlled robot using STT and GPT")
    parser.add_argument("--language", default="en", help="Language code (e.g., en, es, fr)")
    parser.add_argument("--vad-threshold", type=float, default=VAD_THRESHOLD, help=f"Voice activity detection threshold (default: {VAD_THRESHOLD})")
    parser.add_argument("--stt", choices=["whisper", "openai"], default="openai", help="Speech-to-text backend: whisper (local) or openai (cloud GPT-4o Audio)")
    parser.add_argument("--tts", choices=["piper", "openai"], default="openai", help="Text-to-speech backend: piper (local) or openai (cloud)")
    return parser.parse_args()


def main():
    print("VERSION 0.2")
    args = parse_arguments()

    tts = TextToSpeech(backend=args.tts, audio_device=1)

    # Initialize firmware
    fw.start()
    print("🤖 Firmware initialized!")

    # Load system prompt for robot commands
    system_prompt = load_system_prompt()
    print("🤖 Robot system loaded!")

    if args.stt == "openai":
        # Cloud mode: Use AudioCapture + send audio to GPT
        print("☁️  Cloud transcription mode (GPT-4o Audio)")
        audio_capture = AudioCapture(args.vad_threshold)

        try:
            audio_capture.capture(lambda audio, sr: process_audio(audio, sr, system_prompt, tts, audio_capture))
        except KeyboardInterrupt:
            print("\nStopped by user.")
    else:
        # Local mode: Use SpeechToTextTranscriber (AudioCapture + Whisper)
        print("🖥️  Local transcription mode (Whisper)")
        transcriber = SpeechToTextTranscriber(args.language, args.vad_threshold)

        # Get reference to the underlying AudioCapture for TTS pause/resume
        audio_capture = transcriber.audio_capture

        try:
            transcriber.call(lambda text: process_transcription(text, system_prompt, tts, audio_capture))
        except KeyboardInterrupt:
            print("\nStopped by user.")

if __name__ == "__main__":
    main()