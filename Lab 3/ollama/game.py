import requests
import sys
import re

def ask_ai(question):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "qwen2.5:0.5b-instruct", "prompt": question, "stream": False}
    )
    return response.json().get('response', 'No response')

# Expect 2 arguments: answer and guess
if len(sys.argv) != 3:
    print(f"Error: Expected 2 arguments, got {len(sys.argv)-1}", file=sys.stderr)
    sys.exit(1)

answer = sys.argv[1].strip().lower()
guess = sys.argv[2].strip().lower()

# Debug output
print(f"[DEBUG] Answer: '{answer}', Guess: '{guess}'", file=sys.stderr)

# Check if guess is correct - use only direct comparison
if answer == guess:
    result = "yes"
    print(f"[DEBUG] Direct match - CORRECT", file=sys.stderr)
else:
    result = "no"
    print(f"[DEBUG] No match - WRONG", file=sys.stderr)

# Generate hint
hint_raw = ask_ai(f'Describe "{answer}" in 6 words or less. Do not include the word "{answer}". Example: for "cat" say "furry pet that meows".')

# Clean the hint: remove the answer word and limit length
hint = hint_raw.replace(answer, "***").replace(answer.capitalize(), "***")
# Take only first sentence and limit to ~10 words
sentences = re.split(r'[.!?]', hint)
if sentences:
    hint = sentences[0].strip()
words = hint.split()
if len(words) > 10:
    hint = ' '.join(words[:10])

# Print result first, then hint (separated by newline)
print(result)
print(hint)