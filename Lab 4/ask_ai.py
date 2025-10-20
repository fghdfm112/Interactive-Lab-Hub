#!/usr/bin/env python3
# ask_ai.py - Send question to AI and return response

import requests
import sys

def ask_ai(question):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "qwen2.5:0.5b-instruct", "prompt": question, "stream": False}
        )
        return response.json().get('response', 'No response')
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: No question provided", file=sys.stderr)
        sys.exit(1)
    
    question = " ".join(sys.argv[1:])
    answer = ask_ai(question)
    print(answer)

