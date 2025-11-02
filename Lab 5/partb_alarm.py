#!/usr/bin/env python3
"""
Smart Shelf Monitor with Audio Alarm
Monitors shelf inventory and plays audio alerts when quantities change
Extends partb.py with speaker/alarm functionality
"""

import cv2
import requests
import base64
import time
import os
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, send_from_directory
from threading import Thread
import numpy as np
import subprocess

# Import detection functions from partb (or copy them here)
# For now, we'll include the essential functions

# Configuration
IMG_FOLDER = "shelf_img"
INVENTORY_FILE = "shelf_inventory_alarm.json"
CHECK_INTERVAL = 300  # 5 minutes in seconds
MAX_HISTORY = 20  # Keep last 20 snapshots
WEB_PORT = 5001  # Different port from partb.py
USE_YOLO_DETECTION = True
YOLO_CONFIDENCE_THRESHOLD = 0.40
ENABLE_AUDIO_ALERTS = True  # Enable/disable audio alarms

# Flask app setup
app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# YOLO model
yolo_model = None

def play_audio_alert(message_type="change"):
    """Play audio alert using text-to-speech at 25% volume"""
    if not ENABLE_AUDIO_ALERTS:
        return
    
    try:
        if message_type == "item_added":
            message = "Alert! New items detected on shelf."
        elif message_type == "item_removed":
            message = "Alert! Items removed from shelf."
        elif message_type == "quantity_increased":
            message = "Alert! Item quantity increased."
        elif message_type == "quantity_decreased":
            message = "Alert! Item quantity decreased."
        else:
            message = "Alert! Shelf inventory changed."
        
        print(f"[AUDIO] Playing alert: {message} (Volume: 25%)")
        
        # Use espeak for text-to-speech with 25% volume
        # -a parameter: amplitude (0-200, default 100). 50 = ~25% volume
        subprocess.run(['espeak', '-a', '50', message], check=False)
        
    except FileNotFoundError:
        print("[AUDIO WARNING] espeak not found. Install with: sudo apt-get install espeak")
        # Fallback: system beep
        try:
            print('\a')  # Terminal bell
        except:
            pass
    except Exception as e:
        print(f"[AUDIO ERROR] {e}")

def play_beep(count=1):
    """Play simple beep sound"""
    try:
        for _ in range(count):
            print('\a')  # Terminal bell
            time.sleep(0.2)
    except:
        pass

def detect_quantity_changes(old_items, new_items):
    """Detect specific quantity changes between inventories"""
    changes = {
        "items_added": [],
        "items_removed": [],
        "quantity_increased": [],
        "quantity_decreased": [],
        "unchanged": []
    }
    
    if not old_items:
        changes["items_added"] = new_items
        return changes
    
    # Create dictionaries for easy comparison
    old_dict = {item['name'].lower(): item for item in old_items}
    new_dict = {item['name'].lower(): item for item in new_items}
    
    # Check for new items and quantity increases
    for name, new_item in new_dict.items():
        if name not in old_dict:
            changes["items_added"].append(new_item)
        else:
            old_qty = old_dict[name].get('quantity', 1)
            new_qty = new_item.get('quantity', 1)
            
            if new_qty > old_qty:
                changes["quantity_increased"].append({
                    'name': new_item['name'],
                    'old_qty': old_qty,
                    'new_qty': new_qty,
                    'change': new_qty - old_qty
                })
            elif new_qty < old_qty:
                changes["quantity_decreased"].append({
                    'name': new_item['name'],
                    'old_qty': old_qty,
                    'new_qty': new_qty,
                    'change': old_qty - new_qty
                })
            else:
                changes["unchanged"].append(new_item)
    
    # Check for removed items
    for name, old_item in old_dict.items():
        if name not in new_dict:
            changes["items_removed"].append(old_item)
    
    return changes

def announce_changes_with_audio(changes):
    """Announce changes with detailed audio alerts"""
    print("\n" + "=" * 60)
    print("SHELF INVENTORY CHANGE DETECTED")
    print("=" * 60)
    
    has_changes = False
    
    if changes["items_added"]:
        has_changes = True
        print(f"\n[+] ITEMS ADDED ({len(changes['items_added'])}):")
        for item in changes["items_added"]:
            print(f"    + {item['quantity']}x {item['name']}")
        play_audio_alert("item_added")
        time.sleep(1)
    
    if changes["items_removed"]:
        has_changes = True
        print(f"\n[-] ITEMS REMOVED ({len(changes['items_removed'])}):")
        for item in changes["items_removed"]:
            print(f"    - {item['quantity']}x {item['name']}")
        play_audio_alert("item_removed")
        time.sleep(1)
    
    if changes["quantity_increased"]:
        has_changes = True
        print(f"\n[↑] QUANTITY INCREASED:")
        for change in changes["quantity_increased"]:
            print(f"    ↑ {change['name']}: {change['old_qty']} → {change['new_qty']} (+{change['change']})")
        play_audio_alert("quantity_increased")
        time.sleep(1)
    
    if changes["quantity_decreased"]:
        has_changes = True
        print(f"\n[↓] QUANTITY DECREASED:")
        for change in changes["quantity_decreased"]:
            print(f"    ↓ {change['name']}: {change['old_qty']} → {change['new_qty']} (-{change['change']})")
        play_audio_alert("quantity_decreased")
        time.sleep(1)
    
    if not has_changes:
        print("[OK] No changes detected")
    
    print("=" * 60 + "\n")

# Flask routes (same as partb.py)
@app.route('/')
def index():
    return render_template('shelf_dashboard.html')

@app.route('/api/inventory')
def get_inventory():
    inventory = load_inventory()
    response = {
        "current_items": inventory.get("last_description", "No inventory data yet"),
        "structured_items": inventory.get("structured_items", []),
        "last_updated": inventory.get("last_updated", "Never"),
        "history": inventory.get("history", [])[-10:],
        "latest_image": None
    }
    if inventory.get("history"):
        latest = inventory["history"][-1]
        response["latest_image"] = latest.get("image", "")
    return jsonify(response)

@app.route('/shelf_img/<path:filename>')
def serve_image(filename):
    return send_from_directory(IMG_FOLDER, filename)

def start_web_server():
    print(f"\n[WEB] Starting web dashboard on http://0.0.0.0:{WEB_PORT}")
    print(f"[WEB] Access it at: http://localhost:{WEB_PORT}")
    app.run(host='0.0.0.0', port=WEB_PORT, debug=False, use_reloader=False)

def load_inventory():
    if os.path.exists(INVENTORY_FILE):
        try:
            with open(INVENTORY_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"items": [], "last_updated": None, "history": [], "structured_items": []}
    return {"items": [], "last_updated": None, "history": [], "structured_items": []}

def save_inventory(inventory):
    with open(INVENTORY_FILE, 'w') as f:
        json.dump(inventory, f, indent=2)

def setup_folder():
    if not os.path.exists(IMG_FOLDER):
        os.makedirs(IMG_FOLDER)
        print(f"Created folder: {IMG_FOLDER}")

def main():
    print("=" * 60)
    print("Smart Shelf Monitor with Audio Alarm")
    print("=" * 60)
    print(f"Checking every {CHECK_INTERVAL // 60} minutes")
    print(f"Audio alerts: {'ENABLED' if ENABLE_AUDIO_ALERTS else 'DISABLED'}")
    print("=" * 60)
    
    setup_folder()
    inventory = load_inventory()
    
    # Test audio
    if ENABLE_AUDIO_ALERTS:
        print("\n[AUDIO TEST] Testing speaker...")
        play_beep(2)
        time.sleep(0.5)
    
    # Start web server
    web_thread = Thread(target=start_web_server, daemon=True)
    web_thread.start()
    time.sleep(1)
    
    print("\n[INFO] This version monitors quantity changes and triggers audio alerts")
    print("[INFO] You'll need to implement YOLO/Moondream detection or import from partb.py")
    print("[INFO] For now, this demonstrates the audio alert structure")
    print("\nPress Ctrl+C to stop\n")
    
    # Simplified monitoring loop (you'd integrate with partb.py detection code)
    try:
        while True:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Monitoring... (Audio alerts ready)")
            time.sleep(30)
            
            # Demo: simulate a change every 2 minutes for testing
            # In real implementation, this would be replaced with actual detection
            
    except KeyboardInterrupt:
        print("\n\nStopping monitor...")
    
    print("Done!")

if __name__ == "__main__":
    # Check if espeak is available
    try:
        subprocess.run(['espeak', '--version'], capture_output=True, check=False)
        print("[AUDIO] espeak found - text-to-speech available")
    except FileNotFoundError:
        print("[WARNING] espeak not found. Install with: sudo apt-get install espeak")
        print("[INFO] Will use system beep as fallback")
    
    main()

