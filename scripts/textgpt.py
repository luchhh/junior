#!/usr/bin/env python3

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
from lib.gpt import GPT


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Send a message to GPT using a fixed system prompt file and a user message")
    parser.add_argument("--user", required=True, help="User message content")
    parser.add_argument("--model", default="gpt-4o-mini", help="Model name (default: gpt-4o-mini)")
    args = parser.parse_args()

    system_path = Path("prompts/system.md")
    if not system_path.exists():
        raise FileNotFoundError(f"System prompt file not found: {system_path}")
    system_prompt = system_path.read_text(encoding="utf-8").strip()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to your environment or .env file.")

    print(GPT(api_key).chat(system_prompt, args.user, model=args.model))


if __name__ == "__main__":
    main()
