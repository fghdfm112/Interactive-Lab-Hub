echo "I can tell you the weather in New York City. Please say yes if you want to know the weather. Or say no if you don't" | festival --tts

answer=$(python3 weather.py)

echo "$answer" | festival --tts