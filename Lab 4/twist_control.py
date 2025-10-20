#!/usr/bin/env python3
"""
twist_control.py - Monitor Qwiic Twist and manage AI assistant
Handles encoder rotation for conciseness level and button press to start assistant
"""

import time
import sys
import subprocess
import signal

try:
    import qwiic_twist
except ImportError:
    print("ERROR: qwiic_twist library not found!")
    sys.exit(1)

# Conciseness levels
LEVEL_VERBOSE = 1    # Red - Most info
LEVEL_MEDIUM = 2     # Yellow - Medium
LEVEL_CONCISE = 3    # Green - Most concise

# LED colors for each level
COLORS = {
    LEVEL_VERBOSE: (255, 0, 0),      # Red
    LEVEL_MEDIUM: (255, 255, 0),     # Yellow
    LEVEL_CONCISE: (0, 255, 0)       # Green
}

LEVEL_NAMES = {
    LEVEL_VERBOSE: "VERBOSE (Most Info)",
    LEVEL_MEDIUM: "MEDIUM (Balanced)",
    LEVEL_CONCISE: "CONCISE (Brief)"
}

class TwistController:
    def __init__(self, auto_start=False):
        self.twist = qwiic_twist.QwiicTwist()
        self.current_level = LEVEL_MEDIUM  # Start at medium
        self.assistant_process = None
        self.auto_start = auto_start  # Flag to auto-start assistant
        
    def initialize(self):
        """Initialize the Qwiic Twist device"""
        if not self.twist.connected:
            print("ERROR: Qwiic Twist not detected!")
            return False
        
        self.twist.begin()
        print(f"[OK] Qwiic Twist connected (Firmware v{self.twist.version})")
        
        # Set initial encoder position (0 = medium)
        self.twist.set_count(0)
        self.update_led()
        return True
    
    def update_led(self):
        """Update LED color based on current level"""
        r, g, b = COLORS[self.current_level]
        self.twist.set_color(r, g, b)
    
    def get_level_from_count(self, count):
        """Convert encoder count to conciseness level (1-3) with cycling"""
        # Divide encoder position into steps (every 5 clicks = one level change)
        step = count // 5
        
        # Cycle through 3 levels using modulo
        # step 0, 3, 6... -> level 2 (YELLOW/MEDIUM) - starting position
        # step 1, 4, 7... -> level 3 (GREEN/CONCISE)
        # step 2, 5, 8... -> level 1 (RED/VERBOSE)
        # step -1, -4... -> level 1 (RED/VERBOSE)
        # step -2, -5... -> level 3 (GREEN/CONCISE)
        
        levels = [LEVEL_MEDIUM, LEVEL_CONCISE, LEVEL_VERBOSE]
        return levels[step % 3]
    
    def start_voice_assistant(self):
        """Start the voice assistant with current conciseness level"""
        if self.assistant_process and self.assistant_process.poll() is None:
            print("Voice assistant is already running!")
            return
        
        print(f"\n{'='*60}")
        print(f"Starting Voice Assistant")
        print(f"Conciseness Level: {LEVEL_NAMES[self.current_level]}")
        print(f"{'='*60}\n")
        
        # Flash LED white to indicate starting
        self.twist.set_color(255, 255, 255)
        time.sleep(0.3)
        self.update_led()
        
        # Start voice assistant in background
        try:
            self.assistant_process = subprocess.Popen(
                ['bash', 'voice_assistant_concise.sh', str(self.current_level)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except Exception as e:
            print(f"Error starting voice assistant: {e}")
    
    def stop_voice_assistant(self):
        """Stop the voice assistant if running"""
        if self.assistant_process and self.assistant_process.poll() is None:
            print("\nStopping voice assistant...")
            self.assistant_process.terminate()
            try:
                self.assistant_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.assistant_process.kill()
            self.assistant_process = None
            print("[OK] Voice assistant stopped")
    
    def run(self):
        """Main control loop"""
        print("\n" + "="*60)
        print("AI Voice Assistant with Qwiic Twist Control")
        print("="*60)
        print("\nControls:")
        print("  ROTATE: Change conciseness level")
        print("     <- Left (Red):    Verbose responses")
        print("     O  Center (Yellow): Balanced responses")
        print("     -> Right (Green):  Concise responses")
        if not self.auto_start:
            print("  PRESS:  Start voice assistant")
        else:
            print("  AUTO:   Voice assistant will start automatically")
        print("  Ctrl+C: Exit")
        print("="*60)
        print(f"\nCurrent Level: {LEVEL_NAMES[self.current_level]}")
        
        last_count = 0
        last_button = False
        
        # Auto-start assistant if flag is set
        if self.auto_start:
            print("\n[AUTO-START] Starting voice assistant automatically...")
            time.sleep(1)  # Small delay for user to see the message
            self.start_voice_assistant()
        
        try:
            while True:
                # Read encoder position
                count = self.twist.count
                
                # Check if encoder moved
                if count != last_count:
                    last_count = count
                    new_level = self.get_level_from_count(count)
                    
                    if new_level != self.current_level:
                        self.current_level = new_level
                        self.update_led()
                        print(f"\n-> Level changed to: {LEVEL_NAMES[self.current_level]}")
                
                # Read button state
                button_pressed = self.twist.pressed
                
                # Check for button press (rising edge)
                if button_pressed and not last_button:
                    print("\n>>> BUTTON PRESSED <<<")
                    self.start_voice_assistant()
                
                last_button = button_pressed
                
                # Check if assistant process has ended
                if self.assistant_process and self.assistant_process.poll() is not None:
                    print("\n[OK] Voice assistant ended")
                    self.assistant_process = None
                
                time.sleep(0.05)
                
        except KeyboardInterrupt:
            print("\n\nShutting down...")
            self.stop_voice_assistant()
            self.twist.set_color(0, 0, 0)  # Turn off LED
            print("[OK] Goodbye!")

def main():
    # Check for auto-start flag
    auto_start = False
    if len(sys.argv) > 1 and sys.argv[1] == '--auto-start':
        auto_start = True
    
    controller = TwistController(auto_start=auto_start)
    
    if not controller.initialize():
        sys.exit(1)
    
    controller.run()

if __name__ == "__main__":
    main()

