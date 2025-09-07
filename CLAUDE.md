# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based robot control system for "junior", a physical robot car that can be controlled via speech-to-text commands. The system consists of three main components:

1. **Speech-to-Text Processing** (`stt_mic.py`) - Real-time microphone transcription using faster-whisper
2. **Chat Interface** (`chat.py`) - OpenAI GPT integration for converting natural language to robot commands
3. **Audio Recording** (`record_mic.py`) - Simple microphone recording utility

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
# Real-time speech-to-text transcription
python stt_mic.py --model small --vad --language en

# Send a chat command to the robot (requires system prompt)
python chat.py --user "move forward 50 centimeters"

# Record audio for testing
python record_mic.py --seconds 5 --out recording.wav
```

### Common Development Commands
```bash
# List available audio devices
python record_mic.py --list

# Test different Whisper models
python stt_mic.py --model tiny    # fastest, least accurate
python stt_mic.py --model small   # balanced
python stt_mic.py --model medium  # slower, more accurate

# Change OpenAI model
python chat.py --user "turn left 90 degrees" --model gpt-4o
```

## Architecture

### Core Components

- **`chat.py`**: Contains the OpenAI client setup and chat completion logic. The `chat()` function takes a system prompt and user message, returning the AI response.

- **`stt_mic.py`**: Real-time audio processing with VAD (Voice Activity Detection). Uses faster-whisper for local speech recognition with configurable models and parameters.

- **`record_mic.py`**: Simple audio recording utility for testing and debugging audio input.

### Robot Command System

The system uses a structured JSON command format defined in `prompts/system.md`. The robot "junior" responds to natural language with JSON arrays containing movement and speech commands:

- **Movement commands**: `forward`, `backward`, `left`, `right` with millisecond durations
- **Speech command**: `speak` with text body
- **Robot specifications**: 15x30x10 cm, 10 cm/s linear speed, 30°/s rotation speed

### Audio Processing Pipeline

1. **Audio Input**: Continuous microphone capture at 16kHz mono
2. **VAD Processing**: Energy-based voice activity detection with configurable thresholds
3. **Segmentation**: Automatic speech segment detection based on silence duration
4. **Transcription**: faster-whisper model processes audio segments
5. **Output**: Transcribed text for further processing

## Dependencies

- **OpenAI**: GPT model integration for natural language processing
- **faster-whisper**: Local speech-to-text processing
- **sounddevice/soundfile**: Audio I/O handling
- **numpy**: Audio data processing
- **python-dotenv**: Environment configuration

## Configuration

- **Environment**: API keys stored in `.env` file
- **Audio settings**: Configurable sample rates, device selection, and VAD thresholds
- **Model selection**: Support for different Whisper model sizes and OpenAI models
- **Robot timing**: Precise movement calculations based on physical robot specifications