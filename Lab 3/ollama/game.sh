echo "    Hi, Welcome to this game. I have randomly selected a word for you to guess." | festival --tts

# Get the answer from AI
answer=$(python3 game_pre.py)

while true; do
  echo "You can guess the word now." | festival --tts
  guess=$(python3 listen_guess.py)
  
  # Get result and hint from game.py (prints 2 lines: result, then hint)
  output=$(python3 game.py "$answer" "$guess")
  result=$(echo "$output" | head -n 1)
  hint=$(echo "$output" | tail -n 1)
  
  if [[ "$result" == *"yes"* ]]; then
    echo "You guessed the word correctly." | festival --tts
    break
  else
    echo "That's not correct." | festival --tts
    echo "Here is the hint: $hint" | festival --tts
  fi
done





