import base64
from pathlib import Path

from openai import OpenAI


class GPT:
    def __init__(self, api_key: str):
        self._client = OpenAI(api_key=api_key)

    def chat(self, system_prompt: str, user_message: str, model: str = "gpt-4o-mini") -> str:
        response = self._client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content  # type: ignore[return-value]

    def chat_with_audio(self, system_prompt: str, audio_file_path: str, model: str = "gpt-4o-audio-preview") -> str:
        audio_data = base64.b64encode(Path(audio_file_path).read_bytes()).decode("utf-8")
        response = self._client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {"data": audio_data, "format": "wav"},
                        }
                    ],
                },
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content  # type: ignore[return-value]
