echo "Good day human. I am collecting numbers from you. Can I have a number from you? Please speak clearly and slowly." | festival --tts

python3 listen_once.py -m en-us
echo "Saved voice result to voice_result.txt"

echo "The response is recorded in voice_result.txt" | festival --tts