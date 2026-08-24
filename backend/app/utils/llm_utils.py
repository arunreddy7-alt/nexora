import json
import time

from backend.app.services.llm_service import ask_llm


def clean_json_response(response: str) -> str:
    response = response.strip()

    # Remove markdown code fences
    if response.startswith("```json"):
        response = response[7:]
    elif response.startswith("```"):
        response = response[3:]

    if response.endswith("```"):
        response = response[:-3]

    return response.strip()


def extract_json(response: str) -> str:
    """
    Extract the first complete JSON object from a model response.
    Handles cases where the model adds text before/after the JSON.
    """

    cleaned = clean_json_response(response)

    # First try the complete response directly.
    try:
        json.loads(cleaned)
        return cleaned

    except json.JSONDecodeError:
        pass

    # Find the beginning of a JSON object.
    start = cleaned.find("{")

    if start == -1:
        raise ValueError(
            "No JSON object found in LLM response."
        )

    depth = 0
    in_string = False
    escape = False

    for index in range(
        start,
        len(cleaned),
    ):

        char = cleaned[index]

        if in_string:

            if escape:
                escape = False

            elif char == "\\":
                escape = True

            elif char == '"':
                in_string = False

            continue

        if char == '"':
            in_string = True

        elif char == "{":
            depth += 1

        elif char == "}":

            depth -= 1

            if depth == 0:

                candidate = cleaned[
                    start:index + 1
                ]

                try:
                    json.loads(candidate)

                    return candidate

                except json.JSONDecodeError as exc:

                    raise ValueError(
                        f"LLM returned invalid JSON: {exc}"
                    ) from exc

    raise ValueError(
        "LLM returned incomplete JSON."
    )


def parse_json_response(
    response: str,
) -> dict:

    json_text = extract_json(
        response
    )

    parsed = json.loads(
        json_text
    )

    if not isinstance(
        parsed,
        dict,
    ):
        raise ValueError(
            "LLM response must be a JSON object."
        )

    return parsed


def ask_llm_json(
    prompt: str,
    max_retries: int = 3,
) -> dict:

    last_error = None

    current_prompt = prompt

    for attempt in range(
        max_retries
    ):

        try:

            response = ask_llm(
                current_prompt
            )

            return parse_json_response(
                response
            )

        # --------------------------------------------------
        # INVALID JSON
        # --------------------------------------------------

        except ValueError as exc:

            last_error = exc

            if attempt < max_retries - 1:

                current_prompt = f"""
Your previous response was not valid JSON.

The error was:

{exc}

You MUST return ONLY a valid JSON object.

Do not use markdown.
Do not use ```json.
Do not add explanations.
Do not add text before or after the JSON.

Original task:

{prompt}
"""

                # Small delay before retry.
                time.sleep(1)

        # --------------------------------------------------
        # TEMPORARY LLM/API ERROR
        # --------------------------------------------------

        except Exception as exc:

            last_error = exc

            error_text = str(exc).lower()

            temporary_error = any(
                keyword in error_text
                for keyword in [
                    "503",
                    "unavailable",
                    "overloaded",
                    "timeout",
                    "timed out",
                    "temporarily",
                    "internal server error",
                    "rate limit",
                    "429",
                    "500",
                ]
            )

            if not temporary_error:
                raise

            if attempt < max_retries - 1:

                # Exponential backoff:
                #
                # attempt 0 -> 2 seconds
                # attempt 1 -> 4 seconds
                # attempt 2 -> 8 seconds
                # attempt 3 -> 16 seconds
                #
                # This gives Gemini time to recover.

                delay = min(
                    2 ** (attempt + 1),
                    16,
                )

                print(
                    f"LLM temporarily unavailable. "
                    f"Retrying in {delay} seconds... "
                    f"({attempt + 1}/{max_retries})"
                )

                time.sleep(
                    delay
                )

            else:
                break

    raise RuntimeError(
        "LLM request failed after "
        f"{max_retries} attempts. "
        f"Last error: {last_error}"
    )