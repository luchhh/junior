# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based robot control system for "junior", a physical robot car that can be controlled via speech-to-text commands. The system runs on Raspberry Pi 5 (8GB RAM) and supports both local (Whisper) and cloud (GPT-4o Audio) transcription modes. Components:

1. **Main Application** (`chat.py`) - Orchestrates voice control with dual-mode support: local Whisper or cloud GPT-4o Audio transcription
2. **Audio Capture** (`lib/audio_capture.py`) - Pure audio capture service with VAD, independent of transcription backend
3. **Speech-to-Text Module** (`lib/sttt.py`) - Local transcription using AudioCapture + faster-whisper, optimized for Raspberry Pi 5
4. **GPT Integration** (`lib/gpt.py`) - OpenAI client supporting both text chat and audio input for command generation
5. **Firmware Control** (`lib/firmware/`) - GPIO-based motor control for Raspberry Pi 5
6. **Command Models** (`models.py`) - Pydantic models for validated robot commands
7. **Utilities** (`scripts/`) - Helper scripts for testing (transcription, recording, text-based GPT)

## Commands

### Environment Setup
```bash
# Install dependencies (Python virtual environment recommended)
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env  # if available, or create .env with OPENAI_API_KEY
```

### Running the System
```bash
# RECOMMENDED: Cloud transcription (fast, accurate, requires API key)
python chat.py --cloud --language en         # ~1.5s total latency

# Local transcription (slower, private, no API costs)
python chat.py --model small --language en   # ~8.5s total latency

# Testing utilities
python scripts/transcribe.py --model small --language en  # STT only
python scripts/record_mic.py --seconds 5 --out recording.wav  # Audio recording
python scripts/textgpt.py --user "move forward 50 centimeters"  # GPT only (no STT)
```

### Common Development Commands
```bash
# List available audio devices
python scripts/record_mic.py --list

# Cloud mode (GPT-4o Audio API)
python chat.py --cloud --language en                     # Fast, ~1.5s total latency
python chat.py --cloud --vad-threshold 0.003 --language en  # Adjust sensitivity

# Local mode (Whisper on Raspberry Pi)
python chat.py --model tiny --language en     # ~3s transcription, lower accuracy
python chat.py --model small --language en    # ~7s transcription, good accuracy
python chat.py --model medium --language en   # >15s transcription, best accuracy
python chat.py --vad-threshold 0.0035 --language en  # Adjust VAD sensitivity

# Text-only GPT testing
python scripts/textgpt.py --user "turn left 90 degrees" --model gpt-4o
```

## Architecture

### Core Components

- **`chat.py`**: Main application with dual-mode architecture. Supports both local (Whisper) and cloud (GPT-4o Audio) transcription. Orchestrates the complete voice control loop: audio capture → transcription → GPT command generation → firmware execution.

- **`lib/audio_capture.py`**: Pure audio capture service with `AudioCapture` class. Handles microphone input, VAD (Voice Activity Detection), speech segmentation, and audio preprocessing (mono conversion, normalization, 16kHz resampling). Independent of transcription backend - used by both local and cloud modes.

- **`lib/sttt.py`**: Local speech-to-text using `SpeechToTextTranscriber` class. Composes `AudioCapture` with faster-whisper for on-device transcription. Optimized for Raspberry Pi 5 with INT8 quantization and 4-thread CPU inference.

- **`lib/gpt.py`**: OpenAI client with two functions:
  - `chat(system_prompt, user_message)` - Text-based GPT chat for local transcription mode
  - `chat_with_audio(system_prompt, audio_file_path)` - GPT-4o Audio API for cloud transcription mode

- **`lib/firmware/__init__.py`**: Motor control via GPIO pins using lgpio library (Raspberry Pi 5 compatible). Provides `forward()`, `reverse()`, `left_turn()`, `right_turn()` functions with duration and power control.

- **`models.py`**: Pydantic data models for command validation (`MovementCommand`, `SpeakCommand`, `CommandList`).

- **`scripts/`**: Standalone utilities for testing individual components without full system integration.

### Robot Command System

The system uses a structured JSON command format defined in `prompts/system.md`. The robot "junior" responds to natural language with JSON arrays containing movement and speech commands:

- **Movement commands**: `forward`, `backward`, `left`, `right` with millisecond durations
- **Speech command**: `speak` with text body
- **Robot specifications**: 15x30x10 cm, 10 cm/s linear speed, 30°/s rotation speed

### Audio Processing Pipelines

#### Local Mode (Whisper):
1. **Audio Capture**: Continuous microphone monitoring via `AudioCapture` (auto-selects 44100Hz or 16kHz)
2. **VAD Processing**: Energy-based detection (threshold: 0.0035). Buffer accumulates only **after** voice detected
3. **Segmentation**: Speech segments captured after 800ms silence
4. **Preprocessing**: Mono conversion, normalization (90% dynamic range), resampling to 16kHz
5. **Transcription**: Local faster-whisper (INT8, 4 CPU threads) → ~7s for 1.7s audio
6. **GPT Text API**: Transcribed text → GPT-4o-mini → JSON commands (~1s)
7. **Execution**: Pydantic validation → firmware execution
   - **Total latency: ~8.5 seconds**

#### Cloud Mode (GPT-4o Audio):
1. **Audio Capture**: Same `AudioCapture` service as local mode
2. **VAD Processing**: Same energy-based detection
3. **Segmentation**: Same 800ms silence threshold
4. **Preprocessing**: Same mono/normalize/resample pipeline
5. **Audio File**: Save preprocessed audio to `/tmp/robot_command.wav`
6. **GPT Audio API**: Audio file → GPT-4o Audio API → JSON commands (~1s)
7. **Execution**: Pydantic validation → firmware execution
   - **Total latency: ~1.5 seconds** (6x faster!)

## Dependencies

- **OpenAI**: GPT model integration for natural language processing
- **faster-whisper**: Local speech-to-text processing with CTranslate2 backend
- **sounddevice/soundfile**: Audio I/O handling
- **numpy/scipy**: Audio data processing and resampling
- **pydantic**: Data validation for robot commands
- **lgpio**: Raspberry Pi 5 GPIO control (falls back to mock for development)
- **python-dotenv**: Environment configuration

## Configuration

- **Environment**: API keys stored in `.env` file (requires `OPENAI_API_KEY`)
- **Audio settings**:
  - Sample rate: Auto-detected (fallback order: 16000, 44100, 48000, 8000 Hz)
  - VAD threshold: 0.0035 (adjustable via `--vad-threshold`)
  - Silence threshold: 800ms
  - Minimum audio duration: 0.5s
- **Model selection**:
  - Whisper: tiny/small/medium (small recommended for accuracy/speed balance)
  - Compute type: INT8 (optimized for CPU)
  - CPU threads: 4 (for Raspberry Pi 5)
- **Robot timing**: Precise movement calculations based on physical robot specifications (15x30x10 cm, 10 cm/s linear, 30°/s rotation)

## Performance Notes

### Local Mode (Whisper on Pi 5)
- **Transcription time**: ~7 seconds for ~1.7s of speech (normal for CPU inference, matches published Pi 5 benchmarks)
- **Total latency**: ~8.5 seconds (transcription + GPT API)
- **Optimizations**: INT8 quantization, 4-thread CPU inference, disabled redundant VAD filtering, optimized audio buffering
- **Trade-offs**: Slower but free, private, works offline

### Cloud Mode (GPT-4o Audio)
- **Total latency**: ~1.5 seconds (6x faster than local!)
- **API costs**: ~$0.006/minute of audio (~$0.01 per typical 1.7s command)
- **Trade-offs**: Fast and accurate but requires API key, internet connection, and incurs per-use costs

### System Configuration
- **ALSA mixer**: Set mic volume to 100% via `amixer sset Capture 100%` for optimal audio levels
- **VAD threshold**: 0.0035 default (adjust with `--vad-threshold` for different environments)
- **Silence threshold**: 800ms (optimal for command-based interaction)