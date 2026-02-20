import logging
import os
import sys
from typing import Optional

from dotenv import load_dotenv
from google import genai

logger = logging.getLogger(__name__)


def get_api_key() -> str:
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "No API key found. Set GEMINI_API_KEY (or GOOGLE_API_KEY) in your environment or .env file."
        )
    return api_key


def ask_gemini(
    prompt: str,
    model_name: str = "gemini-3-flash-preview",
    api_key: str | None = None,
) -> str:
    resolved_api_key = (api_key or "").strip() or get_api_key()
    try:
        logger.info("Calling Gemini model=%s prompt_len=%d api_key_provided=%s", model_name, len(prompt or ""), bool(api_key))
        preview = (prompt or "")[:1000]
        logger.debug("Prompt preview: %s", preview)

        client = genai.Client(api_key=resolved_api_key)
        response = client.models.generate_content(model=model_name, contents=prompt)
        text = (response.text or "").strip()
        logger.info("Gemini response received model=%s resp_len=%d", model_name, len(text))
        logger.debug("Response preview: %s", (text or "")[:1000])
        return text
    except Exception as exc:
        logger.exception("Gemini request failed for model=%s", model_name)
        raise


def chat_loop(model_name: str = "gemini-3-flash-preview") -> None:
    print(f"Gemini chat started with model: {model_name}")
    print("Type 'exit' to quit.\n")

    client = genai.Client(api_key=get_api_key())
    chat = client.chats.create(model=model_name)

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            return

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            return

        try:
            response = chat.send_message(message=user_input)
            text = (response.text or "").strip()
            print(f"Gemini: {text}\n")
        except Exception as exc:
            print(f"Error: {exc}\n")


def main(argv: Optional[list[str]] = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    model_name = args[0] if args else "gemini-3-flash-preview"

    try:
        chat_loop(model_name=model_name)
        return 0
    except Exception as exc:
        print(f"Startup error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
