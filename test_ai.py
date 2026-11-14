
from ai_service import generate_questions

result = generate_questions(
    topic="Python Stack and Queue",
    mcq_count=3
)

for index, question in enumerate(result["questions"], start=1):
    print(f"\nQuestion {index}: {question['title']}")

    for option in question["options"]:
        print("-", option)

    print("Correct option:", question["correct_option"])
    print("Explanation:", question["explanation"])
