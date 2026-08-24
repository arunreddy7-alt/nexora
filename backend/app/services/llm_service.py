import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is not set"
    )


client = genai.Client(
    api_key=GEMINI_API_KEY
)


MODEL_NAME = "gemini-3.5-flash-lite"


def ask_llm(
    prompt: str,
) -> str:

    print(
        f"[LLM] Starting request "
        f"({len(prompt):,} characters)"
    )

    start_time = time.time()

    try:

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True
                ),
            ),
        )

    except Exception as exc:

        elapsed = time.time() - start_time

        print(
            f"[LLM] Request failed after "
            f"{elapsed:.1f}s: {exc}"
        )

        raise

    elapsed = time.time() - start_time

    print(
        f"[LLM] Response received "
        f"after {elapsed:.1f}s"
    )

    if response is None:
        raise RuntimeError(
            "Gemini returned no response."
        )

    text = getattr(
        response,
        "text",
        None,
    )

    if not text:
        raise RuntimeError(
            "Gemini returned an empty response."
        )

    print(
        f"[LLM] Response size: "
        f"{len(text):,} characters"
    )

    return text