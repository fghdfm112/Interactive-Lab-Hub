#!/usr/bin/env python3
"""
Complete Smart Shelf Monitor with Audio Alarm
Integrates YOLO + Moondream detection with audio alerts for quantity changes
"""

# Import everything from partb.py and add audio functionality
import sys
import subprocess
import time

# Try to import partb module functions
sys.path.insert(0, '/home/pi/Interactive-Lab-Hub/Lab 5')

# Copy the configuration but with audio enabled
IMG_FOLDER = "shelf_img"
INVENTORY_FILE = "shelf_inventory.json" 
CHECK_INTERVAL = 300
ENABLE_AUDIO_ALERTS = True

def play_audio_alert(message_type="change", details=""):
    """Play audio alert using text-to-speech at 25% volume"""
    if not ENABLE_AUDIO_ALERTS:
        return
    
    try:
        messages = {
            "item_added": f"Alert! New items detected on shelf. {details}",
            "item_removed": f"Alert! Items removed from shelf. {details}",
            "quantity_increased": f"Attention! Item quantity increased. {details}",
            "quantity_decreased": f"Warning! Item quantity decreased. {details}",
            "change": "Alert! Shelf inventory changed."
        }
        
        message = messages.get(message_type, messages["change"])
        print(f"[🔊 AUDIO] {message} (Volume: 25%)")
        
        # Use espeak for text-to-speech with 25% volume
        # -a parameter: amplitude (0-200, default 100). 50 = ~25% volume
        subprocess.run(['espeak', '-s', '150', '-a', '50', message], check=False, capture_output=True)
        
    except FileNotFoundError:
        print("[AUDIO] espeak not installed, using beep")
        print('\a' * 3)  # Triple beep
    except Exception as e:
        print(f"[AUDIO ERROR] {e}")

def detect_quantity_changes(old_items, new_items):
    """Detect specific quantity changes between inventories"""
    changes = {
        "items_added": [],
        "items_removed": [],
        "quantity_increased": [],
        "quantity_decreased": [],
        "has_changes": False
    }
    
    if not old_items:
        if new_items:
            changes["items_added"] = new_items
            changes["has_changes"] = True
        return changes
    
    if not new_items:
        changes["items_removed"] = old_items
        changes["has_changes"] = True
        return changes
    
    # Create dictionaries for comparison
    old_dict = {item['name'].lower(): item for item in old_items}
    new_dict = {item['name'].lower(): item for item in new_items}
    
    # Check for new items and quantity changes
    for name, new_item in new_dict.items():
        if name not in old_dict:
            changes["items_added"].append(new_item)
            changes["has_changes"] = True
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
                changes["has_changes"] = True
            elif new_qty < old_qty:
                changes["quantity_decreased"].append({
                    'name': new_item['name'],
                    'old_qty': old_qty,
                    'new_qty': new_qty,
                    'change': old_qty - new_qty
                })
                changes["has_changes"] = True
    
    # Check for removed items
    for name, old_item in old_dict.items():
        if name not in new_dict:
            changes["items_removed"].append(old_item)
            changes["has_changes"] = True
    
    return changes

def announce_changes_with_audio(changes):
    """Announce changes with detailed audio alerts"""
    print("\n" + "🔔" + "=" * 58 + "🔔")
    print("   SHELF INVENTORY CHANGE DETECTED - AUDIO ALERT ACTIVE")
    print("🔔" + "=" * 58 + "🔔")
    
    if not changes["has_changes"]:
        print("[OK] No changes detected")
        print("=" * 60 + "\n")
        return
    
    # Items Added
    if changes["items_added"]:
        print(f"\n[+] NEW ITEMS ADDED ({len(changes['items_added'])}):")
        details_list = []
        for item in changes["items_added"]:
            print(f"    ✚ {item['quantity']}x {item['name']}")
            details_list.append(f"{item['quantity']} {item['name']}")
        
        details = ", ".join(details_list)
        play_audio_alert("item_added", f"Added: {details}")
        time.sleep(1)
    
    # Items Removed
    if changes["items_removed"]:
        print(f"\n[-] ITEMS REMOVED ({len(changes['items_removed'])}):")
        details_list = []
        for item in changes["items_removed"]:
            print(f"    ✖ {item['quantity']}x {item['name']}")
            details_list.append(f"{item['quantity']} {item['name']}")
        
        details = ", ".join(details_list)
        play_audio_alert("item_removed", f"Removed: {details}")
        time.sleep(1)
    
    # Quantity Increased
    if changes["quantity_increased"]:
        print(f"\n[↑] QUANTITY INCREASED:")
        for change in changes["quantity_increased"]:
            print(f"    📈 {change['name']}: {change['old_qty']} → {change['new_qty']} (+{change['change']})")
            play_audio_alert("quantity_increased", 
                           f"{change['name']} increased by {change['change']}")
            time.sleep(1)
    
    # Quantity Decreased
    if changes["quantity_decreased"]:
        print(f"\n[↓] QUANTITY DECREASED:")
        for change in changes["quantity_decreased"]:
            print(f"    📉 {change['name']}: {change['old_qty']} → {change['new_qty']} (-{change['change']})")
            play_audio_alert("quantity_decreased", 
                           f"{change['name']} decreased by {change['change']}")
            time.sleep(1)
    
    print("\n" + "=" * 60 + "\n")

def main():
    print("=" * 60)
    print("🔊 SMART SHELF MONITOR WITH AUDIO ALARM 🔊")
    print("=" * 60)
    print(f"Audio alerts: {'✅ ENABLED' if ENABLE_AUDIO_ALERTS else '❌ DISABLED'}")
    print("=" * 60)
    
    # Test audio system
    if ENABLE_AUDIO_ALERTS:
        print("\n[AUDIO TEST] Testing speaker system...")
        try:
            subprocess.run(['espeak', '--version'], capture_output=True, check=True)
            print("[✓] espeak detected - text-to-speech ready")
            play_audio_alert("change", "Audio system test successful")
        except:
            print("[!] espeak not found. Install: sudo apt-get install espeak")
            print("[!] Using system beep as fallback")
            print('\a' * 2)
        time.sleep(2)
    
    print("\n" + "=" * 60)
    print("INTEGRATION INSTRUCTIONS:")
    print("=" * 60)
    print("To use this with full detection:")
    print("1. This file contains the audio alert functions")
    print("2. Import these into partb.py:")
    print("   - detect_quantity_changes()")
    print("   - announce_changes_with_audio()")
    print("   - play_audio_alert()")
    print("3. Replace announce_changes() calls with announce_changes_with_audio()")
    print("4. Compare old and new structured_items to detect quantity changes")
    print("=" * 60)
    
    print("\n[INFO] Press Ctrl+C to exit")
    
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n\nExiting...")

if __name__ == "__main__":
    main()

