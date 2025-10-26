import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI


def get_client() -> OpenAI:
    """Create and return an OpenAI client using the API key from env."""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to your environment or .env file."
        )
    return OpenAI(api_key=api_key)


def chat(system_prompt: str, user_message: str, model: str = "gpt-4o-mini") -> str:
    """Send a chat completion with a system and user message and return the reply."""
    client = get_client()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content  # type: ignore[return-value]


def chat_with_audio(system_prompt: str, audio_file_path: str, model: str = "gpt-4o-audio-preview") -> str:
    """
    Send an audio file to GPT-4o Audio model for transcription + command generation.

    Args:
        system_prompt: System instructions for the robot
        audio_file_path: Path to the audio file (WAV format recommended)
        model: Model to use (gpt-4o-audio-preview supports audio input)

    Returns:
        JSON string with robot commands
    """
    client = get_client()

    # Read audio file as base64
    import base64
    audio_path = Path(audio_file_path)
    with open(audio_path, 'rb') as audio_file:
        audio_data = base64.b64encode(audio_file.read()).decode('utf-8')

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": audio_data,
                            "format": "wav"
                        }
                    }
                ]
            },
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content  # type: ignore[return-value]
