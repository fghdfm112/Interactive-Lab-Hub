#!/usr/bin/env python3
# ai_core.py - Core AI function for voice assistant
# 
# This file contains the core ask_ai() function.
# For the voice assistant, run: ./voice_assistant.sh

import requests

def ask_ai(question):
    """Send a question to the Ollama AI and get a response."""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "qwen2.5:0.5b-instruct", "prompt": question, "stream": False}
        )
        return response.json().get('response', 'No response')
    except Exception as e:
        return f"Error: {str(e)}"

# Example usage if run directly
if __name__ == "__main__":
    print("Testing AI core function...")
    answer = ask_ai("What is the capital of France?")
    print(f"AI Response: {answer}")
