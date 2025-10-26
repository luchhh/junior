# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based robot control system for "junior", a physical robot car that can be controlled via speech-to-text commands. The system runs on Raspberry Pi 5 (8GB RAM) and consists of the following components:

1. **Main Application** (`chat.py`) - Integrates STT, GPT, and firmware to provide voice-controlled robot operation
2. **Speech-to-Text Module** (`lib/sttt.py`) - Real-time microphone transcription using faster-whisper with optimizations for Raspberry Pi
3. **GPT Integration** (`lib/gpt.py`) - OpenAI GPT client for converting natural language to structured robot commands
4. **Firmware Control** (`lib/firmware/`) - GPIO-based motor control for Raspberry Pi 5
5. **Command Models** (`models.py`) - Pydantic models for validated robot commands
6. **Utilities** (`scripts/`) - Helper scripts for testing (transcription, recording, text-based GPT)

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
# Main voice-controlled robot (recommended - runs STT + GPT + firmware)
python chat.py --model small --language en

# Testing utilities
python scripts/transcribe.py --model small --language en  # STT only
python scripts/record_mic.py --seconds 5 --out recording.wav  # Audio recording
python scripts/textgpt.py --user "move forward 50 centimeters"  # GPT only (no STT)
```

### Common Development Commands
```bash
# List available audio devices
python scripts/record_mic.py --list

# Test different Whisper models
python chat.py --model tiny --language en     # ~2-3s transcription, lower accuracy
python chat.py --model small --language en    # ~7s transcription, good accuracy (recommended)
python chat.py --model medium --language en   # >15s transcription, best accuracy

# Adjust VAD threshold (lower = more sensitive to quiet speech)
python chat.py --vad-threshold 0.0035 --language en

# Change OpenAI model
python scripts/textgpt.py --user "turn left 90 degrees" --model gpt-4o
```

## Architecture

### Core Components

- **`chat.py`**: Main application that orchestrates the complete voice control loop. Initializes firmware, creates STT transcriber, loads robot system prompt, and processes transcriptions through GPT to execute robot commands.

- **`lib/sttt.py`**: Speech-to-text module with `SpeechToTextTranscriber` class. Handles real-time audio capture, VAD (Voice Activity Detection), audio preprocessing (resampling, normalization), and faster-whisper integration. Optimized for Raspberry Pi 5 with INT8 quantization and multi-threaded CPU inference.

- **`lib/gpt.py`**: OpenAI GPT client wrapper for converting natural language to structured JSON robot commands.

- **`lib/firmware/__init__.py`**: Motor control via GPIO pins using lgpio library (Raspberry Pi 5 compatible). Provides `forward()`, `reverse()`, `left_turn()`, `right_turn()` functions with duration and power control.

- **`models.py`**: Pydantic data models for command validation (`MovementCommand`, `SpeakCommand`, `CommandList`).

- **`scripts/`**: Standalone utilities for testing individual components without full system integration.

### Robot Command System

The system uses a structured JSON command format defined in `prompts/system.md`. The robot "junior" responds to natural language with JSON arrays containing movement and speech commands:

- **Movement commands**: `forward`, `backward`, `left`, `right` with millisecond durations
- **Speech command**: `speak` with text body
- **Robot specifications**: 15x30x10 cm, 10 cm/s linear speed, 30°/s rotation speed

### Audio Processing Pipeline

1. **Audio Input**: Continuous microphone capture (device auto-selects 44100Hz or 16kHz based on hardware support)
2. **VAD Processing**: Energy-based voice activity detection (threshold: 0.0035). Buffer only accumulates audio **after** voice is detected to improve transcription quality
3. **Segmentation**: Speech segments detected after 800ms of silence following voice activity
4. **Preprocessing**: Audio is converted to mono, normalized to 90% dynamic range, and resampled to 16kHz using high-quality polyphase resampling
5. **Transcription**: faster-whisper model (INT8 quantized, 4 CPU threads) processes audio segments. Expected performance on Raspberry Pi 5: ~7 seconds for ~1.7s of speech with small model
6. **GPT Processing**: Transcribed text sent to OpenAI GPT which returns structured JSON commands
7. **Execution**: Commands validated via Pydantic models and executed through firmware layer

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

- **Raspberry Pi 5 Benchmarks**: Transcription time with small model is ~7 seconds for ~1.7s of speech. This is normal for CPU-based inference and matches published benchmarks for Pi 5.
- **Real-time limitations**: The small model cannot process audio faster than real-time on Pi 5, but this is acceptable for command-based control where accuracy matters more than latency.
- **Optimization applied**: INT8 quantization, multi-threaded inference, disabled redundant VAD filtering, optimized audio buffering.
- **ALSA mixer configuration**: Microphone capture volume should be set to 100% via `amixer sset Capture 100%` for optimal audio levels.