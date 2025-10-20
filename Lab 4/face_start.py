#!/usr/bin/env python3
"""
face_start.py - Automatically start voice assistant when face is detected
Uses lightweight OpenCV Haar Cascade for face detection
"""

import cv2
import subprocess
import time
import sys
import os

# Configuration
FACE_DETECTION_SCALE = 1.1
FACE_MIN_NEIGHBORS = 5
FACE_MIN_SIZE = (30, 30)
DETECTION_COOLDOWN = 5  # seconds before detecting again after program stops
CAMERA_INDEX = 0

class FaceDetectionStarter:
    def __init__(self):
        self.camera = None
        self.face_cascade = None
        self.twist_process = None
        self.last_detection_time = 0
        
    def initialize_camera(self):
        """Initialize the camera"""
        print("[1] Initializing camera...")
        self.camera = cv2.VideoCapture(CAMERA_INDEX)
        
        if not self.camera.isOpened():
            print("ERROR: Could not open camera!")
            return False
        
        # Set camera resolution (lower = faster)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        
        print("[OK] Camera initialized")
        return True
    
    def initialize_face_detection(self):
        """Initialize Haar Cascade face detector"""
        print("[2] Loading face detection model...")
        
        # Try to find the Haar Cascade XML file
        cascade_paths = [
            '/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml',
            '/usr/local/share/opencv4/haarcascades/haarcascade_frontalface_default.xml',
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        ]
        
        for path in cascade_paths:
            if os.path.exists(path):
                self.face_cascade = cv2.CascadeClassifier(path)
                if not self.face_cascade.empty():
                    print(f"[OK] Face detector loaded from: {path}")
                    return True
        
        print("ERROR: Could not load face detection model!")
        print("Install with: sudo apt-get install opencv-data")
        return False
    
    def detect_faces(self, frame):
        """Detect faces in a frame"""
        # Convert to grayscale for faster processing
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=FACE_DETECTION_SCALE,
            minNeighbors=FACE_MIN_NEIGHBORS,
            minSize=FACE_MIN_SIZE
        )
        
        return faces
    
    def start_twist_control(self):
        """Start the twist_control.py program"""
        if self.twist_process and self.twist_process.poll() is None:
            print("Voice assistant is already running!")
            return
        
        print("\n" + "="*60)
        print("FACE DETECTED! Starting Voice Assistant...")
        print("="*60)
        
        try:
            # Start twist_control.py with auto-start flag
            self.twist_process = subprocess.Popen(
                ['python3', 'twist_control.py', '--auto-start'],
                stdin=subprocess.PIPE,
                stdout=sys.stdout,
                stderr=sys.stderr
            )
            self.last_detection_time = time.time()
            print("[OK] Voice assistant started with auto-start (PID: {})".format(self.twist_process.pid))
        except Exception as e:
            print(f"ERROR starting voice assistant: {e}")
    
    def check_twist_control_status(self):
        """Check if twist_control is still running"""
        if self.twist_process and self.twist_process.poll() is not None:
            print("\n[OK] Voice assistant stopped")
            print("[Monitoring] Returning to face detection mode...")
            print("[Info] Waiting 5 seconds before next detection...")
            self.twist_process = None
            # Reset detection time to start cooldown period
            self.last_detection_time = time.time()
            return False
        return self.twist_process is not None
    
    def run(self):
        """Main detection loop"""
        print("\n" + "="*60)
        print("Face Detection Auto-Start System")
        print("="*60)
        print("\nThis program will automatically start the voice assistant")
        print("when it detects a human face in the camera.")
        print("\nFeatures:")
        print("- Continuous face detection")
        print("- Auto-restart when face detected after assistant ends")
        print("- 5-second cooldown between sessions")
        print("\nPress Ctrl+C to exit")
        print("="*60 + "\n")
        
        frame_count = 0
        detection_msg_shown = False
        
        try:
            while True:
                # Read frame from camera
                ret, frame = self.camera.read()
                
                if not ret:
                    print("ERROR: Failed to read from camera")
                    time.sleep(1)
                    continue
                
                # Only process every 5th frame for efficiency
                frame_count += 1
                if frame_count % 5 != 0:
                    time.sleep(0.01)
                    continue
                
                # Check if twist_control is running
                was_running = is_running if 'is_running' in locals() else False
                is_running = self.check_twist_control_status()
                
                # If it just stopped running, reset the detection message flag
                if was_running and not is_running:
                    detection_msg_shown = False
                
                # Only detect faces if program is not running and cooldown has passed
                cooldown_passed = (time.time() - self.last_detection_time) > DETECTION_COOLDOWN
                
                if not is_running and cooldown_passed:
                    if not detection_msg_shown:
                        print("[Monitoring] Waiting for face detection...")
                        detection_msg_shown = True
                    
                    # Detect faces
                    faces = self.detect_faces(frame)
                    
                    if len(faces) > 0:
                        print(f"[Detection] Found {len(faces)} face(s)!")
                        self.start_twist_control()
                        detection_msg_shown = False
                
                elif is_running:
                    if detection_msg_shown:
                        detection_msg_shown = False
                
                # Small delay to reduce CPU usage
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n\nShutting down...")
            if self.twist_process and self.twist_process.poll() is None:
                print("Stopping voice assistant...")
                self.twist_process.terminate()
                try:
                    self.twist_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.twist_process.kill()
            
            if self.camera:
                self.camera.release()
            
            print("[OK] Face detection system stopped")

def main():
    detector = FaceDetectionStarter()
    
    if not detector.initialize_camera():
        sys.exit(1)
    
    if not detector.initialize_face_detection():
        sys.exit(1)
    
    print("[3] Starting face detection loop...\n")
    detector.run()

if __name__ == "__main__":
    main()

