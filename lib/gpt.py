import os
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
