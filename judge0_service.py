import os
import time
import requests

from dotenv import load_dotenv

load_dotenv()

JUDGE0_URL = os.getenv("JUDGE0_URL")

LANGUAGE_IDS = {
    "c": 50,
    "cpp": 54,
    "java": 62,
    "python": 71
}


def run_code(source_code, language, input_data=""):

    language_id = LANGUAGE_IDS.get(language)

    if not language_id:
        raise ValueError("Unsupported programming language")

    # Send code to Judge0
    response = requests.post(
        f"{JUDGE0_URL}/submissions?base64_encoded=false&wait=false",
        json={
            "source_code": source_code,
            "language_id": language_id,
            "stdin": input_data
        },
        timeout=15
    )

    response.raise_for_status()

    token = response.json()["token"]

    # Check execution result
    for _ in range(15):

        result = requests.get(
            f"{JUDGE0_URL}/submissions/{token}?base64_encoded=false",
            timeout=15
        )

        result.raise_for_status()
        result = result.json()

        status_id = result["status"]["id"]

        # 1 = In Queue, 2 = Processing
        if status_id not in [1, 2]:
            return result

        time.sleep(1)

    raise TimeoutError("Code execution is taking too long")