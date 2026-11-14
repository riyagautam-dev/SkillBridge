
import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing in .env file")

client = genai.Client(api_key=api_key)

# Latest model first, fallback models after it
GEMINI_MODELS = [
    "gemini-3.7-flash",
   
]


def generate_questions(topic: str, mcq_count: int = 5):

    prompt = f"""
    You are an expert question paper creator for a college skill platform.

    Topic: {topic}

    Generate exactly {mcq_count} multiple-choice questions.

    Return JSON in this format:
    {{
        "questions": [
            {{
                "title": "Question text",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_option": 1,
                "explanation": "Why this option is correct",
                "difficulty": "easy"
            }}
        ]
    }}

    Rules:
    - Generate exactly the requested number of questions.
    - Every question must have exactly 4 options.
    - All options must be non-empty strings.
    - correct_option must be an integer from 1 to 4.
    - difficulty must be easy, medium, or hard.
    - explanation must not be empty.
    - Return valid JSON only.
    """

    for model in GEMINI_MODELS:

        try:
            print(f"Trying Gemini model: {model}")

            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config={
                    "response_mime_type": "application/json"
                }
            )

            if not response.text:
                raise ValueError("Gemini returned an empty response")

            result = json.loads(response.text)
            questions = result.get("questions")

            if not isinstance(questions, list):
                raise ValueError("Invalid questions format")

            if len(questions) != mcq_count:
                raise ValueError("Incorrect number of questions generated")

            for question in questions:

                if not isinstance(question, dict):
                    raise ValueError("Invalid question format")

                if not isinstance(question.get("title"), str) or not question["title"].strip():
                    raise ValueError("Question title is missing")

                options = question.get("options")

                if (
                    not isinstance(options, list)
                    or len(options) != 4
                    or not all(
                        isinstance(option, str) and option.strip()
                        for option in options
                    )
                ):
                    raise ValueError("Each question must have 4 valid options")

                correct_option = question.get("correct_option")

                if type(correct_option) is not int or correct_option not in [1, 2, 3, 4]:
                    raise ValueError("Invalid correct option")

                if question.get("difficulty") not in ["easy", "medium", "hard"]:
                    raise ValueError("Invalid difficulty")

                if not isinstance(question.get("explanation"), str) or not question["explanation"].strip():
                    raise ValueError("Question explanation is missing")

            print(f"Success with model: {model}")
            return result

        except Exception as e:

            error = str(e).upper()

            if any(code in error for code in [
                "429",
                "500",
                "503",
                "RESOURCE_EXHAUSTED",
                "UNAVAILABLE",
                "INTERNAL"
            ]):
                print(f"{model} failed: {repr(e)}")
                print("Trying next model...")
                continue

            raise

    raise Exception(
        "All configured Gemini models are currently unavailable."
    )
