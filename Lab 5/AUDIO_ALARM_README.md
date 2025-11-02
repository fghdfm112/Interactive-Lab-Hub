# 🔊 Audio Alarm System for Shelf Monitor

## Overview

This extension adds audio alerts to the smart shelf monitor system. When inventory quantities change, the system plays spoken audio messages through the speaker.

## Files Created

1. **`partb_alarm.py`** - Framework with audio alert functions
2. **`shelf_monitor_with_alarm.py`** - Integration example and standalone tester

## Features

### Audio Alert Types

- 🔔 **Items Added** - "Alert! New items detected on shelf"
- 🔔 **Items Removed** - "Alert! Items removed from shelf"  
- 🔔 **Quantity Increased** - "Attention! Item quantity increased"
- 🔔 **Quantity Decreased** - "Warning! Item quantity decreased"

### Change Detection

The system detects:
- New item types added to shelf
- Item types removed from shelf
- Quantity increases for existing items
- Quantity decreases for existing items

### Console Output

```
🔔==========================================================🔔
   SHELF INVENTORY CHANGE DETECTED - AUDIO ALERT ACTIVE
🔔==========================================================🔔

[+] NEW ITEMS ADDED (1):
    ✚ 1x Box Of Tissues

[↑] QUANTITY INCREASED:
    📈 Book: 5 → 7 (+2)

[↓] QUANTITY DECREASED:
    📉 Teddy Bear: 2 → 1 (-1)

=============================================================
```

## Installation

### 1. Install espeak (Text-to-Speech)

```bash
sudo apt-get update
sudo apt-get install espeak
```

### 2. Test espeak

```bash
espeak "Testing audio system"
```

### 3. Adjust Volume (if needed)

```bash
alsamixer
```

## Usage

### Option 1: Test the Audio System

Run the standalone tester:

```bash
cd /home/pi/Interactive-Lab-Hub/Lab\ 5/
./shelf_monitor_with_alarm.py
```

This will:
- Test if espeak is installed
- Play a test audio message
- Show integration instructions

### Option 2: Integrate into partb.py

To add audio alerts to your existing `partb.py`:

1. **Copy the functions** from `shelf_monitor_with_alarm.py`:
   - `play_audio_alert()`
   - `detect_quantity_changes()`
   - `announce_changes_with_audio()`

2. **Add to partb.py** after the imports:
   ```python
   ENABLE_AUDIO_ALERTS = True  # Add to configuration section
   ```

3. **In the monitoring loop**, replace inventory comparison with:
   ```python
   # After getting structured_items
   old_items = inventory.get("structured_items", [])
   new_items = structured_items
   
   # Detect specific changes
   changes = detect_quantity_changes(old_items, new_items)
   
   if changes["has_changes"]:
       announce_changes_with_audio(changes)
   ```

4. **Save and run**:
   ```bash
   ./partb.py
   ```

## Configuration

### Enable/Disable Audio

In the file, set:
```python
ENABLE_AUDIO_ALERTS = True   # Enable audio
ENABLE_AUDIO_ALERTS = False  # Disable audio (silent mode)
```

### Adjust Volume

**Default: 25% volume** (to avoid being too loud)

Modify in `play_audio_alert()`:
```python
subprocess.run(['espeak', '-a', '50', message])  # 50 = ~25% volume
```

Volume options (`-a` parameter, range 0-200):
- `-a 20` - Very quiet (~10%)
- `-a 50` - Quiet (25%) **[DEFAULT]**
- `-a 100` - Normal volume (50%)
- `-a 150` - Loud (75%)
- `-a 200` - Maximum (100%)

### Adjust Speech Speed

Modify in `play_audio_alert()`:
```python
subprocess.run(['espeak', '-s', '150', '-a', '50', message])  # Speed + Volume
```

Speed options:
- `-s 120` - Slower
- `-s 150` - Normal (default)
- `-s 180` - Faster

### Change Voice

```python
subprocess.run(['espeak', '-v', 'en-us', message])  # US English
subprocess.run(['espeak', '-v', 'en-uk', message])  # UK English
```

## Troubleshooting

### No Sound?

1. **Check if espeak is installed:**
   ```bash
   espeak --version
   ```

2. **Test audio output:**
   ```bash
   speaker-test -t wav -c 2
   ```

3. **Check volume:**
   ```bash
   amixer set 'Master' 80%
   ```

4. **Verify audio device:**
   ```bash
   aplay -l
   ```

### espeak Not Found?

The system will automatically fall back to system beep (`\a`).

To install espeak:
```bash
sudo apt-get install espeak
```

### No Speakers/Headphones?

- Connect speakers or headphones to the 3.5mm jack
- Or use HDMI audio if connected to a monitor
- Or use a USB speaker

## Use Cases

### 🏪 Retail Store
Monitor product shelves and alert staff when stock is low

### 🏭 Warehouse
Track inventory movements with audio confirmation

### 🏠 Smart Home
Monitor pantry/fridge and alert when items are running out

### 🏥 Medical Storage
Alert when critical supplies change quantities

## Advanced: Custom Audio Messages

Edit the messages in `play_audio_alert()`:

```python
messages = {
    "item_added": "New product detected!",
    "item_removed": "Product taken from shelf!",
    "quantity_increased": "Stock increased!",
    "quantity_decreased": "Low stock warning!",
}
```

## Example Output

```bash
[00:54:12] Scan #5 - Checking shelf...

🔔==========================================================🔔
   SHELF INVENTORY CHANGE DETECTED - AUDIO ALERT ACTIVE
🔔==========================================================🔔

[↓] QUANTITY DECREASED:
    📉 Book: 6 → 4 (-2)

=============================================================

[🔊 AUDIO] Warning! Item quantity decreased. Book decreased by 2
```

## Notes

- Audio alerts play in sequence (not simultaneously)
- 1-second delay between different alert types
- System beep used as fallback if espeak unavailable
- Works best with speakers/headphones connected

---

**Created**: November 2, 2025  
**Part of**: Interactive Lab Hub - Lab 5

