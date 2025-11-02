#!/usr/bin/env python3
"""
Smart Shelf Monitor with Moondream AI
Monitors a shelf and automatically tracks inventory changes
Recognizes what's on the shelf, detects changes, and updates inventory
"""

import cv2
import requests
import base64
import time
import os
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, send_from_directory
from threading import Thread, Event

# Configuration
IMG_FOLDER = "shelf_img"
INVENTORY_FILE = "shelf_inventory.json"
CHECK_INTERVAL = 300  # 5 minutes in seconds
MAX_HISTORY = 20  # Keep last 20 snapshots
MAX_IMAGES = 12  # Keep only last 12 images (1 hour with 5 min interval)
WEB_PORT = 5000  # Web interface port

# Flask app setup
app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development

# Event to trigger immediate rescan from web interface
rescan_event = Event()

def setup_folder():
    """Create image folder if it doesn't exist"""
    if not os.path.exists(IMG_FOLDER):
        os.makedirs(IMG_FOLDER)
        print(f"Created folder: {IMG_FOLDER}")

def cleanup_old_images():
    """Keep only the most recent MAX_IMAGES images, delete older ones"""
    try:
        # Get all image files in the folder
        image_files = [f for f in os.listdir(IMG_FOLDER) if f.startswith('shelf_') and f.endswith('.jpg')]
        
        # Skip visualization files
        image_files = [f for f in image_files if '_yolo_viz' not in f and '_viz' not in f]
        
        if len(image_files) <= MAX_IMAGES:
            return  # No cleanup needed
        
        # Sort by filename (which contains timestamp) in descending order
        image_files.sort(reverse=True)
        
        # Get files to delete (keep only MAX_IMAGES most recent)
        files_to_delete = image_files[MAX_IMAGES:]
        
        # Delete old files
        for filename in files_to_delete:
            filepath = os.path.join(IMG_FOLDER, filename)
            try:
                os.remove(filepath)
                print(f"[CLEANUP] Deleted old image: {filename}")
            except Exception as e:
                print(f"[CLEANUP] Error deleting {filename}: {e}")
        
        print(f"[CLEANUP] Keeping {MAX_IMAGES} most recent images, deleted {len(files_to_delete)} old images")
    
    except Exception as e:
        print(f"[CLEANUP] Error during cleanup: {e}")

def load_inventory():
    """Load the current inventory from file"""
    if os.path.exists(INVENTORY_FILE):
        try:
            with open(INVENTORY_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"items": [], "last_updated": None, "history": []}
    return {"items": [], "last_updated": None, "history": []}

def save_inventory(inventory):
    """Save the current inventory to file"""
    with open(INVENTORY_FILE, 'w') as f:
        json.dump(inventory, f, indent=2)

def capture_shelf_image(cap, filename):
    """Capture image from camera with proper warm-up"""
    # Discard several frames to let camera adjust exposure
    for i in range(30):
        cap.read()
    
    # Small delay for stabilization
    time.sleep(0.5)
    
    # Capture the actual frame
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not capture image")
        return None
    
    # Verify frame is not all black
    mean_brightness = frame.mean()
    if mean_brightness < 5:
        print(f"[WARNING] Image appears very dark (brightness: {mean_brightness:.1f})")
        print("[WARNING] Trying again with more frames...")
        # Try again with more frames
        for i in range(50):
            cap.read()
        time.sleep(1)
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not capture image on retry")
            return None
        mean_brightness = frame.mean()
        print(f"[INFO] Retry brightness: {mean_brightness:.1f}")
    
    cv2.imwrite(filename, frame)
    return filename

def ask_moondream(image_path, prompt):
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
            timeout=300,  # 5 minutes timeout
            stream=True
        )
        
        if response.status_code == 200:
            full_response = ""
            for line in response.iter_lines():
                if line:
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

def parse_items_from_description(description):
    """Parse item list from Moondream's description into structured format"""
    if not description:
        return []
    
    import re
    
    # Blacklist of non-item phrases to filter out
    blacklist_phrases = [
        'shelf', 'wall', 'background', 'setting', 'room', 'area', 'space',
        'front', 'behind', 'next to', 'placed on', 'sitting on', 'arranged',
        'orderly fashion', 'various objects', 'several items', 'these items',
        'image shows', 'picture', 'view', 'scene'
    ]
    
    items = []
    
    # Common quantity words/patterns
    quantity_patterns = [
        # Handle "Book - 2" or "1. Book - 3" format (Moondream's numbered list with quantity)
        (r'(?:\d+\.\s*)?([a-zA-Z\s]+?)\s*-\s*(\d+)', lambda m: (int(m.group(2)), m.group(1).strip())),
        # Handle "a few books" (approximate 3)
        (r'(?:a\s+)?few\s+([a-zA-Z\s]+)', lambda m: (3, m.group(1).strip())),
        # Handle "several items" (approximate 3)
        (r'several\s+([a-zA-Z\s]+)', lambda m: (3, m.group(1).strip())),
        # Handle "3 books" format
        (r'(\d+)\s+([a-zA-Z\s]+)', lambda m: (int(m.group(1)), m.group(2).strip())),
        # Handle "a laptop" or "an item" or "one item"
        (r'(a|an|one)\s+([a-zA-Z\s]+)', lambda m: (1, m.group(2).strip())),
        # Handle "three books" (word numbers)
        (r'(two|three|four|five|six|seven|eight|nine|ten)\s+([a-zA-Z\s]+)', 
         lambda m: (word_to_num(m.group(1)), m.group(2).strip())),
        # Handle "some items" or "multiple items"
        (r'(some|multiple)\s+([a-zA-Z\s]+)', lambda m: (2, m.group(2).strip())),
    ]
    
    # Word to number mapping
    word_map = {
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
        'a': 1, 'an': 1
    }
    
    def word_to_num(word):
        return word_map.get(word.lower(), 1)
    
    # Split by common delimiters
    description_lower = description.lower()
    # Look for patterns like "item1, item2, and item3" or "item1. item2. item3"
    segments = re.split(r'[,.]|and(?=\s)', description)
    
    for segment in segments:
        segment = segment.strip()
        if not segment or len(segment) < 3:
            continue
        
        # Try to match quantity patterns
        matched = False
        for pattern, extractor in quantity_patterns:
            match = re.search(pattern, segment)
            if match:
                try:
                    qty, item_name = extractor(match)
                    # Clean up item name
                    item_name = re.sub(r'\b(is|are|has|have|the|this|that|there)\b', '', item_name).strip()
                    if item_name and len(item_name) > 2:
                        items.append({
                            'name': item_name.title(),
                            'quantity': qty,
                            'note': 'Moondream AI',
                            'source': 'moondream'
                        })
                        matched = True
                        break
                except:
                    continue
        
        # If no quantity pattern matched, assume single item
        if not matched and segment:
            # Extract noun-like words
            words = segment.split()
            if words:
                item_name = ' '.join([w for w in words if len(w) > 2 and w not in 
                                     ['the', 'is', 'are', 'has', 'have', 'there', 'this', 'that']])
                if item_name:
                    items.append({
                        'name': item_name.title(),
                        'quantity': 1,
                        'note': 'Moondream AI',
                        'source': 'moondream'
                    })
    
    # Filter out items containing blacklisted phrases
    filtered_items = []
    for item in items:
        item_name_lower = item['name'].lower()
        is_blacklisted = False
        
        for phrase in blacklist_phrases:
            if phrase in item_name_lower:
                is_blacklisted = True
                print(f"[FILTER] Removed non-item: '{item['name']}'")
                break
        
        # Also filter out items that are too long (likely descriptions, not items)
        if len(item_name_lower) > 50:
            is_blacklisted = True
            print(f"[FILTER] Removed overly long description: '{item['name'][:30]}...'")
        
        if not is_blacklisted:
            filtered_items.append(item)
    
    return filtered_items

def announce_changes(old_description, new_description, changes):
    """Announce what changed on the shelf"""
    print("\n" + "=" * 60)
    print("SHELF INVENTORY UPDATE")
    print("=" * 60)
    
    if not changes["changed"]:
        print("[OK] No changes detected - shelf inventory unchanged")
    else:
        print("[!] CHANGES DETECTED!")
        print("\nPrevious inventory:")
        print(f"  {old_description if old_description else 'Empty or unknown'}")
        print("\nCurrent inventory:")
        print(f"  {new_description}")
    
    print("=" * 60 + "\n")

# Flask routes for web interface
@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('shelf_dashboard.html')

@app.route('/api/inventory')
def get_inventory():
    """API endpoint to get current inventory data"""
    inventory = load_inventory()
    
    # Format the data for display
    response = {
        "current_items": inventory.get("last_description", "No inventory data yet"),
        "structured_items": inventory.get("structured_items", []),
        "last_updated": inventory.get("last_updated", "Never"),
        "history": inventory.get("history", [])[-10:],  # Last 10 entries
        "latest_image": None
    }
    
    # Get the latest image path
    if inventory.get("history"):
        latest = inventory["history"][-1]
        response["latest_image"] = latest.get("image", "")
    
    return jsonify(response)

@app.route('/shelf_img/<path:filename>')
def serve_image(filename):
    """Serve images from the shelf_img folder"""
    return send_from_directory(IMG_FOLDER, filename)

@app.route('/api/rescan', methods=['POST'])
def trigger_rescan():
    """API endpoint to trigger immediate rescan"""
    rescan_event.set()  # Signal the monitoring loop to scan immediately
    return jsonify({"status": "success", "message": "Rescan triggered"})

def start_web_server():
    """Start the Flask web server in a separate thread"""
    print(f"\n[WEB] Starting web dashboard on http://0.0.0.0:{WEB_PORT}")
    print(f"[WEB] Access it at: http://localhost:{WEB_PORT}")
    app.run(host='0.0.0.0', port=WEB_PORT, debug=False, use_reloader=False)

def main():
    print("=" * 60)
    print("Smart Shelf Monitor with Moondream AI")
    print("=" * 60)
    print(f"Checking every {CHECK_INTERVAL // 60} minutes")
    print(f"Storing images in '{IMG_FOLDER}' folder")
    print(f"Inventory tracked in '{INVENTORY_FILE}'")
    print("=" * 60)
    
    # Setup
    setup_folder()
    inventory = load_inventory()
    
    # Start web server in background thread
    web_thread = Thread(target=start_web_server, daemon=True)
    web_thread.start()
    time.sleep(1)  # Give server time to start
    
    # Open camera (using index 1 since /dev/video0 doesn't exist)
    print("\nOpening camera...")
    cap = cv2.VideoCapture(1)  # Changed from 0 to 1
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # Enable auto-exposure and auto-white-balance
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3)  # Auto mode
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)  # Enable autofocus if available
    
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    
    print("Camera opened successfully!")
    print("Warming up camera (this may take a few seconds)...")
    time.sleep(3)  # Increased warm-up time
    
    # Discard many frames for auto-exposure adjustment
    print("Adjusting camera exposure...")
    for i in range(50):
        cap.read()
        if i % 10 == 0:
            time.sleep(0.2)  # Pause periodically to let camera adjust
    
    print("Camera ready!")
    
    print("\nInitial shelf scan...")
    
    # Capture initial inventory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    initial_image = os.path.join(IMG_FOLDER, f"shelf_{timestamp}.jpg")
    
    if capture_shelf_image(cap, initial_image):
        print(f"Initial image captured: {initial_image}")
        
        # Cleanup old images (keep only last 12 images = 1 hour)
        cleanup_old_images()
        
        # Use Moondream to identify items on shelf
        print("\n[Moondream] Identifying items on shelf...")
        initial_description = ask_moondream(
            initial_image,
            "List all types of objects you can see on the shelf. For each type, give an approximate count (e.g. 'a few books', 'several bottles', 'one tissue box'). Include items like: books, toys, stuffed animals, tissue boxes, snack packages, food items, bottles, cans, decorations, electronics, CD cases, magazines, papers, containers. Keep it brief - just identify what types of items are present. Only list objects on the shelf, not the shelf or background."
        )
        
        if initial_description:
            # Parse Moondream description into structured items
            structured_items = parse_items_from_description(initial_description)
            print(f"[Moondream] Identified {len(structured_items)} item types:")
            for item in structured_items:
                print(f"  - {item['quantity']}x {item['name']}")
        else:
            initial_description = "No items detected"
            structured_items = []
        
        print(f"\nTotal {len(structured_items)} item types identified")
        
        # Save inventory
        inventory["items"] = [initial_description]
        inventory["last_updated"] = timestamp
        inventory["last_description"] = initial_description
        inventory["structured_items"] = structured_items
        inventory["history"] = [{
            "timestamp": timestamp,
            "description": initial_description,
            "image": initial_image,
            "structured_items": structured_items
        }]
        save_inventory(inventory)
        
        print("\n[*] Initial inventory recorded:")
        print(f"    {initial_description}")
    
    print("\nMonitoring started! Press Ctrl+C to stop.\n")
    
    scan_count = 0
    
    try:
        while True:
            # Wait for the check interval OR until manual rescan is triggered
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting {CHECK_INTERVAL // 60} minutes until next scan (or manual trigger)...")
            
            # Check for rescan event every second
            waited = 0
            while waited < CHECK_INTERVAL:
                if rescan_event.is_set():
                    print("\n[MANUAL RESCAN] Triggered from web dashboard!")
                    rescan_event.clear()  # Reset the event
                    break
                time.sleep(1)
                waited += 1
            
            scan_count += 1
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Scan #{scan_count} - Checking shelf...")
            
            # Capture current shelf state
            current_image = os.path.join(IMG_FOLDER, f"shelf_{timestamp}.jpg")
            
            if not capture_shelf_image(cap, current_image):
                continue
            
            print(f"Image captured: {current_image}")
            
            # Cleanup old images (keep only last 12 images = 1 hour)
            cleanup_old_images()
            
            # Use Moondream to identify items on shelf
            print("\n[Moondream] Identifying items on shelf...")
            current_description = ask_moondream(
                current_image,
                "List all types of objects you can see on the shelf. For each type, give an approximate count (e.g. 'a few books', 'several bottles', 'one tissue box'). Include items like: books, toys, stuffed animals, tissue boxes, snack packages, food items, bottles, cans, decorations, electronics, CD cases, magazines, papers, containers. Keep it brief - just identify what types of items are present. Only list objects on the shelf, not the shelf or background."
            )
            
            if not current_description:
                print("[WARNING] Moondream could not identify items. Skipping this scan.")
                continue
            
            # Parse Moondream description into structured items
            structured_items = parse_items_from_description(current_description)
            print(f"[Moondream] Identified {len(structured_items)} item types:")
            for item in structured_items:
                print(f"  - {item['quantity']}x {item['name']}")
            
            print(f"\nTotal {len(structured_items)} item types identified")
            
            # Compare with previous inventory
            previous_description = inventory.get("last_description", "")
            
            # Compare both description and structured items
            items_changed = (current_description.strip().lower() != previous_description.strip().lower())
            
            changes = {"changed": items_changed}
            
            # Announce changes
            announce_changes(previous_description, current_description, changes)
            
            if items_changed:
                # Update inventory
                inventory["last_description"] = current_description
                inventory["last_updated"] = timestamp
                inventory["structured_items"] = structured_items
                
                # Add to history (keep only last MAX_HISTORY entries)
                inventory["history"].append({
                    "timestamp": timestamp,
                    "description": current_description,
                    "image": current_image,
                    "structured_items": structured_items
                })
                
                if len(inventory["history"]) > MAX_HISTORY:
                    inventory["history"] = inventory["history"][-MAX_HISTORY:]
                
                save_inventory(inventory)
                print(f"\n[*] Inventory updated and saved to {INVENTORY_FILE}")
            
            print()
    
    except KeyboardInterrupt:
        print("\n\nStopping shelf monitor...")
    
    finally:
        cap.release()
        print(f"\nCamera released. Total scans: {scan_count}")
        print(f"Inventory saved in: {INVENTORY_FILE}")
        print(f"Images saved in: {IMG_FOLDER}/")
        print("Done!")

if __name__ == "__main__":
    main()

