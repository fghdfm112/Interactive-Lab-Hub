#!/usr/bin/env python3
"""
Background Change Monitor with Moondream AI Description
Monitors camera feed for background changes and stores images in circular buffer
Uses Moondream to describe what's happening when changes are detected
"""

import cv2
import requests
import base64
import time
import os
import numpy as np
from datetime import datetime

# Configuration
IMG_FOLDER = "c_img"
MAX_IMAGES = 10
CHECK_INTERVAL = 60  # seconds between checks
CHANGE_THRESHOLD = 2  # sensitivity for detecting changes (lower = more sensitive)
DEBUG = True  # Save debug images to see what's being compared

def setup_folder():
    """Create image folder if it doesn't exist"""
    if not os.path.exists(IMG_FOLDER):
        os.makedirs(IMG_FOLDER)
        print(f"Created folder: {IMG_FOLDER}")

def get_next_image_path(image_count):
    """Get the next image filename using circular buffer (1-10)"""
    image_num = (image_count % MAX_IMAGES) + 1
    return os.path.join(IMG_FOLDER, f"capture_{image_num}.jpg")

def get_baseline_path(image_count):
    """Get the baseline image filename"""
    image_num = (image_count % MAX_IMAGES) + 1
    return os.path.join(IMG_FOLDER, f"baseline_{image_num}.jpg")

def create_change_visualization(baseline, current, image_count):
    """Create a side-by-side comparison with highlighted changes"""
    # Convert to grayscale for diff
    gray1 = cv2.cvtColor(baseline, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(current, cv2.COLOR_BGR2GRAY)
    
    # Blur to reduce noise
    gray1 = cv2.GaussianBlur(gray1, (21, 21), 0)
    gray2 = cv2.GaussianBlur(gray2, (21, 21), 0)
    
    # Get difference
    diff = cv2.absdiff(gray1, gray2)
    _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
    
    # Create colored overlay on current frame
    current_with_changes = current.copy()
    # Highlight changed areas in red
    current_with_changes[thresh > 0] = [0, 0, 255]  # Red overlay
    
    # Blend the overlay with original
    result = cv2.addWeighted(current, 0.7, current_with_changes, 0.3, 0)
    
    # Save the visualization
    image_num = (image_count % MAX_IMAGES) + 1
    viz_path = os.path.join(IMG_FOLDER, f"changes_{image_num}.jpg")
    cv2.imwrite(viz_path, result)
    
    return viz_path

def capture_frame(cap):
    """Capture a single frame from the camera"""
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not capture frame")
        return None
    return frame

def detect_change(frame1, frame2, threshold=CHANGE_THRESHOLD):
    """Detect if there's significant change between two frames"""
    if frame1 is None or frame2 is None:
        return False, 0
    
    # Convert to grayscale
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur to reduce noise
    gray1 = cv2.GaussianBlur(gray1, (21, 21), 0)
    gray2 = cv2.GaussianBlur(gray2, (21, 21), 0)
    
    # Calculate absolute difference
    diff = cv2.absdiff(gray1, gray2)
    
    # Save debug diff if enabled
    if DEBUG:
        debug_diff_path = os.path.join(IMG_FOLDER, "debug_diff.jpg")
        cv2.imwrite(debug_diff_path, diff)
    
    # Threshold the difference (lower = more sensitive)
    _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
    
    # Save debug threshold if enabled
    if DEBUG:
        debug_thresh_path = os.path.join(IMG_FOLDER, "debug_thresh.jpg")
        cv2.imwrite(debug_thresh_path, thresh)
    
    # Calculate percentage of changed pixels
    change_percent = (np.sum(thresh) / 255) / (thresh.shape[0] * thresh.shape[1]) * 100
    
    return change_percent > threshold, change_percent

def ask_moondream(image_path, prompt="What changed in this image? Describe what you see."):
    """Ask Moondream about the image with streaming response"""
    
    # Encode image to base64
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    print(f"\n[AI] Asking Moondream: {prompt}")
    print("Moondream: ", end="", flush=True)
    
    try:
        # Query Moondream with streaming
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "moondream:latest",
                "prompt": prompt,
                "images": [image_data],
                "stream": True
            },
            timeout=300,  # 5 minutes timeout (model is slow)
            stream=True
        )
        
        if response.status_code == 200:
            full_response = ""
            for line in response.iter_lines():
                if line:
                    import json
                    chunk = json.loads(line)
                    token = chunk.get('response', '')
                    print(token, end="", flush=True)
                    full_response += token
            
            print("\n")  # New line after response
            return full_response
        else:
            print(f"\nError: {response.status_code}")
            return None
    except requests.exceptions.Timeout:
        print("\n[TIMEOUT] Moondream is taking too long. Continuing monitoring...")
        return None
    except Exception as e:
        print(f"\n[ERROR] {e}")
        return None

def main():
    print("=" * 60)
    print("Background Change Monitor with Moondream AI")
    print("=" * 60)
    print(f"Checking every {CHECK_INTERVAL} seconds")
    print(f"Storing up to {MAX_IMAGES} images in '{IMG_FOLDER}' folder")
    print(f"Change threshold: {CHANGE_THRESHOLD}%")
    if DEBUG:
        print(f"DEBUG MODE: Saving debug images to see frame comparisons")
    print("=" * 60)
    
    # Setup
    setup_folder()
    
    # Open camera
    print("\nOpening camera...")
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    
    print("Camera opened successfully!")
    print("Warming up camera...")
    time.sleep(2)
    
    # Discard first few frames for auto-exposure
    for i in range(10):
        cap.read()
    
    # Capture baseline frame
    print("Capturing baseline frame...")
    baseline_frame = capture_frame(cap)
    if baseline_frame is None:
        print("Failed to capture baseline. Exiting.")
        cap.release()
        return
    
    print("Baseline captured. Monitoring started!\n")
    
    image_count = 0
    
    try:
        while True:
            # Wait for the check interval
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting {CHECK_INTERVAL} seconds...")
            time.sleep(CHECK_INTERVAL)
            
            # Capture current frame
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking for changes...")
            current_frame = capture_frame(cap)
            
            if current_frame is None:
                continue
            
            # Save debug frames if enabled
            if DEBUG:
                debug_baseline = os.path.join(IMG_FOLDER, "debug_baseline.jpg")
                debug_current = os.path.join(IMG_FOLDER, "debug_current.jpg")
                cv2.imwrite(debug_baseline, baseline_frame)
                cv2.imwrite(debug_current, current_frame)
            
            # Detect change
            changed, change_percent = detect_change(baseline_frame, current_frame, CHANGE_THRESHOLD)
            print(f"    -> Change detected: {change_percent:.2f}% (threshold: {CHANGE_THRESHOLD}%)")
            
            if changed:
                image_count += 1  # Increment BEFORE to show correct capture number
                print(f"[!] CHANGE DETECTED! ({change_percent:.1f}% of frame changed)")
                print(f"[*] Capture #{image_count} (will be saved as #{(image_count-1) % MAX_IMAGES + 1} in circular buffer)")
                
                # Save baseline for reference
                baseline_path = get_baseline_path(image_count - 1)
                cv2.imwrite(baseline_path, baseline_frame)
                
                # Save current image
                image_path = get_next_image_path(image_count - 1)
                cv2.imwrite(image_path, current_frame)
                
                # Create visualization showing what changed
                viz_path = create_change_visualization(baseline_frame, current_frame, image_count - 1)
                
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"[*] Images saved at {timestamp}")
                print(f"    - Before: {baseline_path}")
                print(f"    - After: {image_path}")
                print(f"    - Changes highlighted: {viz_path}")
                
                # Ask Moondream to describe what changed
                # First, describe the current scene
                print("\n--- Analyzing current scene ---")
                current_description = ask_moondream(image_path, "Describe what you see in this image. Focus on objects, people, and their locations.")
                
                # Then, ask about the highlighted changes
                if current_description:
                    print("\n--- Identifying what changed ---")
                    ask_moondream(viz_path, "In this image, the red highlighted areas show what changed from the previous frame. What objects or movements do you see in the red highlighted regions? Be specific about what changed.")
                
                # Update baseline to current frame for next comparison
                baseline_frame = current_frame.copy()
                
            else:
                print(f"[OK] No significant change detected ({change_percent:.1f}% changed)")
            
            print()
    
    except KeyboardInterrupt:
        print("\n\nStopping monitor...")
    
    finally:
        cap.release()
        print(f"\nCamera released. Total images captured: {min(image_count, MAX_IMAGES)}")
        print("Done!")

if __name__ == "__main__":
    main()

