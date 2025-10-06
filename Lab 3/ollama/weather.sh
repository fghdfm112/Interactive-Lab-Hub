echo "I can tell you the weather in New York City. Please say yes if you want to know the weather. Or say no if you don't" | festival --tts

decision=$(python3 listen_once.py)

if [ "$decision" = "yes" ]; then
    answer=$(python3 weather.py)
    echo "$answer" | festival --tts
elif [ "$decision" = "no" ]; then
    echo "Okay, no problem." | festival --tts
else
    echo "I'm here if you need me." | festival --tts
fi