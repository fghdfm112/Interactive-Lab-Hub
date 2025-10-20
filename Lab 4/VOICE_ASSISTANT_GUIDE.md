# AI Voice Assistant with Qwiic Twist Control

## Overview

An AI-powered voice assistant with adjustable response conciseness, controlled by a SparkFun Qwiic Twist rotary encoder.

## Features

- 🎤 Voice-activated AI assistant using Vosk speech recognition
- 🔊 Text-to-speech output via Festival
- 🎛️ Qwiic Twist encoder controls AI response style
- 💡 LED color feedback for current mode
- 🤖 Powered by Ollama AI (qwen2.5:0.5b-instruct)

## Conciseness Levels

| Level | LED Color | Description | Response Style |
|-------|-----------|-------------|----------------|
| 1 | 🔴 RED | Verbose | At most 5 sentences - detailed answers |
| 2 | 🟡 YELLOW | Medium | At most 3 sentences - balanced responses |
| 3 | 🟢 GREEN | Concise | Exactly 1 sentence - brief and to-the-point |

## How to Use

### 1. Start the Controller

**Option A: Manual Mode** (press button to start)
```bash
cd "/home/pi/Interactive-Lab-Hub/Lab 4"
python3 twist_control.py
```

**Option B: Auto-Start Mode** (starts immediately)
```bash
cd "/home/pi/Interactive-Lab-Hub/Lab 4"
python3 twist_control.py --auto-start
```

### 2. Adjust Conciseness Level

- **Rotate LEFT** ← : More verbose (towards RED)
- **Rotate RIGHT** → : More concise (towards GREEN)
- Watch the LED color change to see current level

### 3. Start Voice Assistant

- **Press the button** on the Qwiic Twist
- Wait for "You can speak now"
- Ask your question
- AI responds according to current conciseness level

### 4. Use Voice Assistant

- Speak your question clearly
- Wait for AI response
- Say "exit", "quit", or "stop" to end the session
- Press button again to restart with a different level

### 5. Exit

Press **Ctrl+C** to exit the controller

## File Structure

```
Lab 4/
├── twist_control.py              # Main controller (START HERE)
├── voice_assistant_concise.sh    # Voice assistant with levels
├── ask_ai_concise.py             # AI query with conciseness
├── listen.py                     # Speech recognition
└── qwiic_twist_test.py           # Hardware test script
```

## Testing Hardware

Before using the integrated system, test your Qwiic Twist:

```bash
python3 qwiic_twist_test.py
```

## Examples

### Verbose Mode (RED LED - Max 5 sentences)
**Q:** "What is Python?"  
**A:** "Python is a high-level, interpreted programming language known for its simplicity and readability. It was created by Guido van Rossum in 1991. Python supports multiple programming paradigms including procedural, object-oriented, and functional programming. It's widely used for web development, data analysis, artificial intelligence, and automation. Its extensive standard library and community make it excellent for beginners and professionals."

### Medium Mode (YELLOW LED - Max 3 sentences)
**Q:** "What is Python?"  
**A:** "Python is a popular high-level programming language known for its simplicity and readability. It supports multiple programming paradigms and is used for web development, data analysis, and AI. It has an extensive standard library and strong community support."

### Concise Mode (GREEN LED - Exactly 1 sentence)
**Q:** "What is Python?"  
**A:** "Python is a versatile, high-level programming language used for web development, data science, and automation."

## Troubleshooting

### No audio output
- Check speakers are connected
- Verify volume: `amixer get Master`
- Test Festival: `echo "test" | festival --tts`

### Qwiic Twist not detected
- Check I2C connections
- Verify I2C is enabled: `sudo raspi-config` → Interface Options
- Test device: `python3 qwiic_twist_test.py`

### Speech recognition not working
- Check microphone is connected
- Verify Vosk model is installed
- Test separately: `python3 listen.py`

### Ollama errors
- Start Ollama: `ollama run qwen2.5:0.5b-instruct`
- Verify it's running: `curl http://localhost:11434/api/version`

## Requirements

All dependencies listed in `req_2.txt`:
- vosk, sounddevice (speech recognition)
- requests (Ollama API)
- qwiic_twist (encoder control)
- festival, festvox packages (text-to-speech)

## Tips

- Start with **MEDIUM** level (yellow) for balanced responses
- Use **VERBOSE** (red) for learning/detailed explanations
- Use **CONCISE** (green) for quick facts/simple questions
- The LED provides instant visual feedback of your setting
- You can change the level anytime (even while assistant is running)

