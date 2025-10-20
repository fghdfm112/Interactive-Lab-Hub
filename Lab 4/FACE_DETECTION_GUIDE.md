# Face Detection Auto-Start Guide

## Overview

`face_start.py` automatically launches the voice assistant when it detects a human face using the camera. This provides a hands-free, automatic activation experience.

## How It Works

1. **Camera monitors** for human faces using OpenCV Haar Cascade
2. **Face detected** → Automatically starts `twist_control.py --auto-start`
3. **Voice assistant starts immediately** (no button press needed!)
4. **Rotate encoder** to change conciseness level anytime
5. **Speak** to interact with the AI assistant
6. **Say "exit"** to stop assistant → System returns to monitoring mode
7. **5-second cooldown** → Face detection resumes
8. **Continuous loop** - repeats automatically when faces detected

## Usage

### Start Face Detection Mode

```bash
cd "/home/pi/Interactive-Lab-Hub/Lab 4"
python3 face_start.py
```

### What You'll See

```
[1] Initializing camera...
[OK] Camera initialized
[2] Loading face detection model...
[OK] Face detector loaded from: /usr/share/opencv4/haarcascades/...
[3] Starting face detection loop...

[Monitoring] Waiting for face detection...
[Detection] Found 1 face(s)!
============================================================
FACE DETECTED! Starting Voice Assistant...
============================================================
[OK] Voice assistant started (PID: 12345)
```

## Features

- **Lightweight**: Uses CPU-only Haar Cascade (no GPU needed)
- **Efficient**: Processes only every 5th frame at low resolution (320x240)
- **Smart Cooldown**: Won't restart immediately after assistant stops
- **Process Monitoring**: Tracks if voice assistant is still running
- **Low Resources**: Minimal CPU and memory usage

## Requirements

All installed automatically when you ran the setup:

- **opencv-python** - Computer vision library
- **opencv-data** - Haar Cascade face detection models
- **Camera** - USB webcam or Raspberry Pi camera module

## Configuration

Edit these settings in `face_start.py`:

```python
FACE_DETECTION_SCALE = 1.1      # Detection sensitivity
FACE_MIN_NEIGHBORS = 5           # Minimum detections to confirm face
FACE_MIN_SIZE = (30, 30)        # Minimum face size in pixels
DETECTION_COOLDOWN = 3           # Seconds before re-detecting
CAMERA_INDEX = 0                 # Camera device number
```

## Comparison: Manual vs Auto Mode

| Feature | Manual Mode (`twist_control.py`) | Auto Mode (`face_start.py`) |
|---------|-----------------------------------|------------------------------|
| Activation | Press button to start | Face detected to start |
| Best For | Deliberate interaction | Hands-free/automatic |
| Hardware | Qwiic Twist only | Qwiic Twist + Camera |
| Power Usage | Lower | Slightly higher (camera) |

## Troubleshooting

### Camera not found / "can't open camera by index"

**Most common cause**: Camera is already in use by another process

```bash
# Check if camera is in use
lsof /dev/video0

# If a process is using it, kill it:
kill <PID>

# Test which camera index works
python3 test_camera.py
```

**Other checks:**
```bash
# List available cameras
ls /dev/video*

# Check camera details
v4l2-ctl --list-devices

# Verify your user is in video group
groups | grep video
```

### Face not detected
- Ensure good lighting
- Face camera directly
- Move closer to camera
- Adjust `FACE_MIN_SIZE` to detect smaller faces

### Models not found
```bash
# Reinstall opencv-data
sudo apt-get install --reinstall opencv-data
```

### High CPU usage
- Increase frame skip (change `frame_count % 5` to higher number)
- Lower camera resolution in code
- Increase `DETECTION_COOLDOWN`

## Tips

- **Lighting**: Works best in well-lit environments
- **Position**: Face the camera at 1-3 feet distance
- **Angle**: Works best when facing camera directly
- **Multiple faces**: Detects any face, starts once
- **Privacy**: Camera only used for detection, no recording

## Exit

Press **Ctrl+C** to stop face detection and exit

