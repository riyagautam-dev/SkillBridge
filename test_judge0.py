from judge0_service import run_code

result = run_code(
    source_code='print("Hello SkillBridge")',
    language="python"
)

print("Status:", result["status"]["description"])
print("Output:", result["stdout"])