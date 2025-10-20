#!/bin/bash
# voice_assistant_concise.sh - Voice assistant with conciseness control
# Usage: ./voice_assistant_concise.sh <conciseness_level>

if [ -z "$1" ]; then
  CONCISENESS_LEVEL=2  # Default to medium
else
  CONCISENESS_LEVEL=$1
fi

# Announce the conciseness level
case $CONCISENESS_LEVEL in
  1)
    echo "Voice assistant activated in verbose mode. Say exit or quit to stop." | festival --tts
    ;;
  2)
    echo "Voice assistant activated in medium mode. Say exit or quit to stop." | festival --tts
    ;;
  3)
    echo "Voice assistant activated in concise mode. Say exit or quit to stop." | festival --tts
    ;;
esac

while true; do
  echo "You can speak now." | festival --tts
  
  # Listen to user input
  user_input=$(python3 listen.py 2>/dev/null)
  
  # Check if listening failed
  if [ $? -ne 0 ] || [ -z "$user_input" ]; then
    echo "I didn't catch that. Please try again." | festival --tts
    continue
  fi
  
  echo "You said: $user_input" | festival --tts
  
  # Check for exit commands
  if [[ "$user_input" == *"exit"* ]] || [[ "$user_input" == *"quit"* ]] || [[ "$user_input" == *"stop"* ]] || [[ "$user_input" == *"goodbye"* ]]; then
    echo "Goodbye! Voice assistant shutting down." | festival --tts
    break
  fi
  
  # Ask the AI with conciseness level
  ai_response=$(python3 ask_ai_concise.py "$CONCISENESS_LEVEL" "$user_input")
  
  # Speak the response
  echo "$ai_response" | festival --tts
  
done

