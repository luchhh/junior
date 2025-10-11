#!/usr/bin/env python3

import argparse
from lib.gpt import chat
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Send a message to GPT using a fixed system prompt file and a user message")
    parser.add_argument("--user", required=True, help="User message content")
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="Model name (default: gpt-4o-mini)",
    )
    args = parser.parse_args()

    system_path = Path("prompts/system.md")
    if not system_path.exists():
        raise FileNotFoundError(f"System prompt file not found: {system_path}")
    system_prompt = system_path.read_text(encoding="utf-8").strip()

    print(chat(system_prompt, args.user, model=args.model))


if __name__ == "__main__":
    main()