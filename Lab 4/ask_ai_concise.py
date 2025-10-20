#!/usr/bin/env python3
# ask_ai_concise.py - Send question to AI with conciseness control

import requests
import sys

def ask_ai_with_level(question, conciseness_level):
    """
    Ask AI with specific conciseness level
    Level 1 (RED): At most 5 sentences
    Level 2 (YELLOW): At most 3 sentences
    Level 3 (GREEN): Exactly 1 sentence
    """
    
    # Create different prompts based on conciseness level with strict sentence limits
    if conciseness_level == 1:
        # Verbose mode - up to 5 sentences
        system_prompt = "You are a helpful assistant. Answer the following question in AT MOST 5 sentences. Provide detailed information but stay within the sentence limit. Question: "
    elif conciseness_level == 2:
        # Medium mode - up to 3 sentences
        system_prompt = "You are a helpful assistant. Answer the following question in AT MOST 3 sentences. Be clear and informative. Question: "
    else:  # Level 3
        # Concise mode - exactly 1 sentence
        system_prompt = "You are a helpful assistant. Answer the following question in EXACTLY 1 sentence. Be brief and to the point. Question: "
    
    full_prompt = system_prompt + question
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "qwen2.5:0.5b-instruct", "prompt": full_prompt, "stream": False}
        )
        return response.json().get('response', 'No response')
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: ask_ai_concise.py <conciseness_level> <question>", file=sys.stderr)
        sys.exit(1)
    
    level = int(sys.argv[1])
    question = " ".join(sys.argv[2:])
    answer = ask_ai_with_level(question, level)
    print(answer)

