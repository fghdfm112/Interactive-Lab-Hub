#!/bin/bash
# voice_assistant.sh - Voice assistant using festival and vosk

echo "Voice assistant activated. Say exit or quit to stop." | festival --tts

while true; do
  echo "You can speak now." | festival --tts
  
  # Listen to user input
  user_input=$(python3 listen.py)
  
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
  
  # Ask the AI
  ai_response=$(python3 ask_ai.py "$user_input")
  
  # Speak the response
  echo "$ai_response" | festival --tts
  
done

