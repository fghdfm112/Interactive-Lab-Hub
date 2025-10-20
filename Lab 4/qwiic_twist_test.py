#!/usr/bin/env python3
"""
Qwiic Twist Test Script
Tests the SparkFun Qwiic Twist rotary encoder with RGB LED
"""

import time
import sys

try:
    import qwiic_twist
except ImportError:
    print("ERROR: qwiic_twist library not found!")
    print("Install with: pip3 install sparkfun-qwiic-twist")
    sys.exit(1)

def test_qwiic_twist():
    """Test all features of the Qwiic Twist"""
    
    print("=" * 60)
    print("Qwiic Twist Test Script")
    print("=" * 60)
    
    # Initialize the device
    print("\n[1] Initializing Qwiic Twist...")
    twist = qwiic_twist.QwiicTwist()
    
    if not twist.connected:
        print("ERROR: Qwiic Twist not detected on I2C bus!")
        print("Check your connections:")
        print("  - Is the device powered?")
        print("  - Are SDA and SCL connected correctly?")
        print("  - Is I2C enabled? (sudo raspi-config -> Interface Options)")
        sys.exit(1)
    
    print("✓ Qwiic Twist connected successfully!")
    
    # Begin communication
    twist.begin()
    
    # Get firmware version
    version = twist.version
    print(f"✓ Firmware version: {version}")
    
    # Test RGB LED
    print("\n[2] Testing RGB LED...")
    print("  - Setting LED to RED")
    twist.set_color(255, 0, 0)
    time.sleep(1)
    
    print("  - Setting LED to GREEN")
    twist.set_color(0, 255, 0)
    time.sleep(1)
    
    print("  - Setting LED to BLUE")
    twist.set_color(0, 0, 255)
    time.sleep(1)
    
    print("  - Setting LED to WHITE")
    twist.set_color(255, 255, 255)
    time.sleep(1)
    
    print("✓ RGB LED test complete!")
    
    # Reset encoder count
    print("\n[3] Resetting encoder count to 0...")
    twist.set_count(0)
    print("✓ Encoder reset")
    
    # Interactive test
    print("\n[4] Interactive Test Mode")
    print("=" * 60)
    print("Instructions:")
    print("  - Turn the knob to see encoder values")
    print("  - Press the knob to see button events")
    print("  - LED color changes based on position")
    print("  - Press Ctrl+C to exit")
    print("=" * 60)
    
    last_count = 0
    last_button = False
    
    try:
        while True:
            # Read encoder position
            count = twist.count
            
            # Read button state
            button_pressed = twist.pressed
            
            # Check if encoder moved
            if count != last_count:
                print(f"Encoder Position: {count:4d} (moved {count - last_count:+d})")
                last_count = count
                
                # Change LED color based on position
                # Create a rainbow effect based on encoder value
                hue = (count * 10) % 360
                r, g, b = hsv_to_rgb(hue, 1.0, 1.0)
                twist.set_color(r, g, b)
            
            # Check if button state changed
            if button_pressed != last_button:
                last_button = button_pressed
                if button_pressed:
                    print(">>> BUTTON PRESSED <<<")
                    # Flash white when pressed
                    twist.set_color(255, 255, 255)
                else:
                    print(">>> BUTTON RELEASED <<<")
            
            time.sleep(0.05)  # Small delay to prevent CPU spinning
            
    except KeyboardInterrupt:
        print("\n\n[5] Shutting down...")
        print("✓ Test complete!")
        twist.set_color(0, 0, 0)  # Turn off LED
        print("=" * 60)

def hsv_to_rgb(h, s, v):
    """Convert HSV color to RGB (0-255)"""
    h = h / 60.0
    i = int(h)
    f = h - i
    
    v = int(v * 255)
    p = int(v * (1 - s))
    q = int(v * (1 - s * f))
    t = int(v * (1 - s * (1 - f)))
    
    i = i % 6
    
    if i == 0:
        return v, t, p
    elif i == 1:
        return q, v, p
    elif i == 2:
        return p, v, t
    elif i == 3:
        return p, q, v
    elif i == 4:
        return t, p, v
    else:
        return v, p, q

if __name__ == "__main__":
    test_qwiic_twist()
