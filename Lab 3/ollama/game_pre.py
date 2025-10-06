import requests
import re

def ask_ai(question):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "qwen2.5:0.5b-instruct", "prompt": question, "stream": False}
    )
    return response.json().get('response', 'No response')

# Use it anywhere!
answer = ask_ai("Generate one simple common English word. It must be: a concrete noun (like animals, objects, or food), easy to guess, and only ONE word. Examples: cat, apple, book. Reply with ONLY the single word, nothing else.")

# Extract just the word (remove extra text, punctuation, etc)
# Try to find a single word in the response
words = re.findall(r'\b[a-zA-Z]+\b', answer.lower())
if words:
    # Take the last word (often the actual answer after any preamble)
    clean_answer = words[-1]
else:
    # Fallback if no word found
    clean_answer = answer.strip().lower()

print(clean_answer)