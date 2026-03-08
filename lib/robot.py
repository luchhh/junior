import json
import sys
from datetime import datetime

import numpy as np
import soundfile

from lib.firmware import Firmware
from lib.gpt import GPT
from lib.sources import MicrophoneSource
from lib.tts import TextToSpeech
from lib.sttt import SpeechToTextTranscriber
from lib.models import MovementCommand, SpeakCommand, CommandList
from pydantic import ValidationError


class Robot:
    def __init__(self, tts: TextToSpeech, system_prompt: str, source: MicrophoneSource, gpt: GPT, firmware: Firmware, transcriber: SpeechToTextTranscriber | None = None, stt: str = "openai"):
        self.tts = tts
        self.system_prompt = system_prompt
        self.source = source
        self.stt = stt
        self.gpt = gpt
        self.firmware = firmware
        self.transcriber = transcriber

    def run(self) -> None:
        match self.stt:
            case "openai":
                print("☁️  Cloud transcription mode (GPT-4o Audio)")
                for audio, sample_rate in self.source:
                    audio_path = '/tmp/robot_command.wav'
                    soundfile.write(audio_path, audio, sample_rate)
                    self._call_gpt("🎤 Sending audio to GPT...", lambda: self.gpt.chat_with_audio(self.system_prompt, audio_path))
            case "whisper":
                print("🖥️  Local transcription mode (Whisper)")
                for audio, sr in self.source:
                    text = self.transcriber.transcribe(audio, sr)
                    if text:
                        self._call_gpt(f"🎤 Transcribed: {text}", lambda: self.gpt.chat(self.system_prompt, text))

    def _call_gpt(self, label: str, gpt_fn) -> None:
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] {label}")
            start = datetime.now()
            response = gpt_fn()
            end = datetime.now()
            print(f"[{end.strftime('%H:%M:%S.%f')[:-3]}] 🤖 GPT response: {response} (took {(end - start).total_seconds():.2f}s)")
            self._handle_response(response)
        except Exception as e:
            print(f"❌ Chat error: {e}", file=sys.stderr)

    def _handle_response(self, response: str) -> None:
        self.firmware.clear()
        try:
            commands = CommandList(root=json.loads(response)).root
            print(f"🤖 Robot commands: {len(commands)} action(s)")
            for cmd in commands:
                if isinstance(cmd, MovementCommand):
                    print(f"  → {cmd.command}: {cmd.ms}ms")
                elif isinstance(cmd, SpeakCommand):
                    print(f"  → speak: {cmd.body}")
                self._execute(cmd)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON response: {e}", file=sys.stderr)
        except ValidationError as e:
            print(f"❌ Invalid command format: {e}", file=sys.stderr)
        except Exception as e:
            print(f"❌ Command execution error: {e}", file=sys.stderr)

    def _execute(self, cmd) -> None:
        if isinstance(cmd, MovementCommand):
            sec = cmd.ms / 1000.0
            match cmd.command:
                case "forward":
                    self.firmware.forward(sec)
                case "backward":
                    self.firmware.reverse(sec)
                case "left":
                    self.firmware.left_turn(sec)
                case "right":
                    self.firmware.right_turn(sec)
        elif isinstance(cmd, SpeakCommand):
            self.source.pause()
            try:
                self.tts.speak(cmd.body)
            finally:
                self.source.resume()
