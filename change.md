# Change Log

## 2025-10-26

### Added trail.py - Background Change Monitor with Moondream AI
- Created new program `Lab 5/trail.py` that monitors camera for background changes every 60 seconds
- Implements circular buffer storage in `c_img` folder with max 10 images (11th replaces 1st)
- Uses OpenCV for camera capture and background change detection
- Integrates Moondream AI to describe detected changes
- Uses streaming response from Moondream API with 5-minute timeout to handle slow model processing
- Features: automatic folder creation, timestamp logging, change percentage calculation, keyboard interrupt handling

### Fixed Unicode Encoding Error in trail.py
- Replaced unicode characters (✓, 🔔, 📸, 🤖) with ASCII-safe alternatives ([OK], [!], [*], [AI])
- Fixed UnicodeEncodeError that occurred on terminals with latin-1 encoding

### Improved Change Detection Sensitivity in trail.py
- Lowered CHANGE_THRESHOLD from 30% to 5% for more sensitive detection
- Added Gaussian blur to reduce noise and improve detection accuracy
- Lowered binary threshold from 30 to 25 for better sensitivity

### Enhanced trail.py to Identify What Actually Changed
- Added `create_change_visualization()` function that highlights changed areas in red
- Now saves 3 images per detection: baseline (before), current (after), and change visualization
- Asks Moondream two specific questions: 1) Describe current scene, 2) Identify what's in the red highlighted change areas
- This allows the AI to specifically tell what changed rather than just describing the scene

### Fixed Circular Buffer Counter in trail.py
- Moved image_count increment to happen before saving images for clearer logging
- Added debug output showing total capture count and which slot in the circular buffer is being used
- Fixed duplicate increment that was happening after AI analysis
- Now clearly shows "Capture #X (will be saved as #Y in circular buffer)" for better tracking

### Added Debug Mode and Improved Change Detection in trail.py
- Lowered CHANGE_THRESHOLD from 5% to 2% for even more sensitive detection
- Added DEBUG mode that saves comparison images: debug_baseline.jpg, debug_current.jpg, debug_diff.jpg, debug_thresh.jpg
- Added real-time change percentage display for every check
- Debug images help diagnose why changes are or aren't being detected
- Users can now see exactly what the algorithm is comparing and how sensitive it is

### Created partb.py - Smart Shelf Monitor with AI Inventory Tracking
- New program that monitors a shelf and automatically tracks inventory changes every 5 minutes
- Uses Moondream AI to recognize and list all items on the shelf
- Maintains persistent inventory in `shelf_inventory.json` with full history
- Detects changes by comparing AI descriptions between scans
- When changes detected, asks AI to specifically identify what was added/removed/moved
- Stores timestamped images in `shelf_img` folder (keeps last 20 snapshots)
- Announces inventory updates with detailed change analysis
- Based on trail.py architecture but focused on inventory management rather than motion detection

### Added Web Dashboard to partb.py
- Integrated Flask web server running on port 5000 in background thread
- Created beautiful modern UI with gradient background and card-based layout
- Dashboard displays: current shelf image, inventory list, and change history
- Auto-refreshes every 10 seconds for near real-time updates
- REST API endpoint `/api/inventory` provides JSON data for external access
- Responsive design works on desktop and mobile devices
- Live status indicator shows system is running
- Added Flask to requirements.txt

### Created PROJECT.md - Comprehensive Project Documentation
- Complete project overview and goals
- Technology stack documentation (hardware and software)
- Detailed feature list and functionality description
- Installation and setup instructions
- Usage guide with examples
- Configuration options
- System workflow explanation
- Web dashboard documentation
- Use cases for retail, home, laboratory, and office
- Educational value and learning outcomes
- Example console and JSON outputs
- Known limitations and future enhancement ideas

### Fixed Camera Capture Issues in partb.py
- Improved camera initialization with auto-exposure and autofocus settings
- Increased warm-up time from 2s to 3s with 50 frame discard
- Added periodic delays during initialization to allow camera adjustment
- Enhanced capture_shelf_image() to discard 30 frames before each capture
- Added brightness detection to identify dark/black frames (threshold: 5)
- Automatic retry with 50 additional frames if image is too dark
- Added console feedback showing brightness values for debugging
- Prevents capturing invalid/black frames that confused Moondream AI

### Added Excel-like Inventory Table Feature to partb.py and Web Dashboard
- Created `parse_items_from_description()` function to extract structured data from Moondream's text
- Parses natural language into structured items with: name, quantity, and notes
- Supports numeric quantities (e.g., "3 books"), word quantities (e.g., "three laptops"), and implied quantities
- Uses regex patterns to extract items from descriptions like "a laptop, two books, and three pens"
- Backend API updated to return `structured_items` array in JSON response
- Inventory storage now includes structured items in history
- Added "Inventory Excel" section to web dashboard with professional spreadsheet-style table
- Excel-like styling: gradient header, alternating row colors, hover effects, bordered cells
- Table columns: # (row number), Item Name, Quantity (badge), Note, Status
- Quantity badges with colored styling for visual clarity
- Total row showing item count and total units
- Real-time updates synchronized with inventory scans
- Clean, professional look matching Excel/Google Sheets aesthetics

### Integrated YOLOv8 Object Detection for Accurate Classification
- Added `ultralytics` package for YOLOv8 object detection
- Created `load_yolo_model()` function to initialize YOLOv8n (nano) model optimized for Raspberry Pi
- Created `detect_objects_yolo()` function that analyzes images and returns structured item data
- YOLO provides accurate object detection with bounding boxes, class names, and confidence scores
- Counts multiple instances of same object type automatically
- Confidence threshold configurable (default: 30%)
- System now tries YOLO detection first, falls back to Moondream if YOLO unavailable
- Hybrid approach: YOLO for accurate detection + optional Moondream for context/change analysis
- Note field in Excel table shows confidence percentages from YOLO
- Graceful degradation: works with or without YOLO installed
- Console output shows detection method used ([YOLO] or [Moondream])
- Much more accurate item counting and classification than text parsing alone
- Added `USE_YOLO_DETECTION` config flag to enable/disable YOLO

### Enhanced YOLO Detection with Debugging and Adaptive Thresholding
- Lowered default confidence threshold from 30% to 15% for better detection
- Added comprehensive debug output showing detection counts and confidence levels
- Automatic fallback to 5% confidence threshold if nothing detected initially
- Added visualization saving feature to see what YOLO detected with bounding boxes
- Shows list of detectable object classes on startup (80 COCO classes)
- Full error traceback for troubleshooting YOLO issues
- Debug messages show detection attempts and results at each confidence level

### Implemented Hybrid Detection System Using Both YOLO and Moondream
- Lowered YOLO confidence threshold to 8% for maximum detection sensitivity
- System now ALWAYS uses both YOLO and Moondream together (not one or the other)
- Created `merge_detections()` function to intelligently combine results from both sources
- YOLO provides accurate object detection and counting for 80 common object classes
- Moondream captures additional items that YOLO cannot detect (tissues, papers, decorations, etc.)
- Priority system: YOLO items used for accuracy, Moondream adds items YOLO missed
- Each item tagged with source ('yolo' or 'moondream') in note field
- Excel table shows "YOLO XX%" for computer vision detections, "Moondream AI" for text-based detections
- Combined description format: "YOLO: [yolo items]. Moondream: [full description]"
- Console output shows separate counts from each source plus merged total
- Best of both worlds: precise counting + comprehensive coverage

### Improved Moondream Prompts and Filtering to Remove Non-Items
- Tailored Moondream prompt to focus ONLY on individual objects, not shelf/background/scene
- Added explicit instruction: "Do NOT describe the shelf itself, walls, or background"
- Created blacklist of non-item phrases: shelf, wall, background, setting, room, arranged, etc.
- Implemented filtering in `parse_items_from_description()` to remove blacklisted items
- Added length filter: items >50 characters are likely descriptions, not items
- Enhanced `merge_detections()` with similarity mapping to avoid duplicates
- Similarity map handles: stuffed animal→teddy bear, magazine→book, plush→teddy bear
- Console shows filtered items: "[FILTER] Removed non-item: 'White Shelf With Various Objects'"
- Merge logging: "[MERGE] Skipping duplicate/similar items"
- Results in cleaner, more accurate inventory with only actual shelf items

### Adjusted YOLO Confidence Threshold to 40% for Higher Accuracy
- Increased YOLO confidence threshold from 8% to 40%
- Higher threshold means YOLO only reports objects it's very confident about
- Reduces false positives and increases precision
- Moondream still captures items YOLO misses at this higher threshold
- Better balance: YOLO for highly confident detections, Moondream for comprehensive coverage

### Created Audio Alarm System for Quantity Changes
- Created `partb_alarm.py` with audio alert framework
- Created `shelf_monitor_with_alarm.py` as integration example
- Added `play_audio_alert()` function using espeak text-to-speech
- Created `detect_quantity_changes()` to detect specific changes between inventories
- Tracks: items added, items removed, quantity increased, quantity decreased
- `announce_changes_with_audio()` provides detailed console output + audio alerts
- Different audio messages for different types of changes
- Graceful fallback to system beep if espeak not installed
- Console shows visual indicators: ✚ for added, ✖ for removed, 📈 for increased, 📉 for decreased
- Can be integrated into partb.py for full shelf monitoring with audio alerts
- Useful for warehouses, stores, or any scenario requiring immediate notification of inventory changes

### Fixed Quantity Parsing for Moondream's Numbered List Format
- Fixed bug where "1. Book - 2" was being parsed as quantity 1 instead of 2
- Added regex pattern to handle "Item Name - Quantity" format from Moondream
- Pattern: `(?:\d+\.\s*)?([a-zA-Z\s]+?)\s*-\s*(\d+)` captures the actual quantity after the dash
- Now correctly extracts quantity from formats like "1. Book - 2", "2. Bottle - 3", "Book - 5"
- Pattern placed first in priority list to match before simpler patterns
- Fixes discrepancy between console output and web dashboard display

### Set Audio Alerts to 25% Volume
- Modified `play_audio_alert()` in both alarm files to play at 25% volume
- Added `-a 50` parameter to espeak (amplitude 0-200, where 50 = ~25%)
- Prevents alerts from being too loud/startling
- Console shows "(Volume: 25%)" in audio messages
- Updated documentation with volume adjustment instructions
- Volume can be easily adjusted by changing the `-a` parameter value

### Enhanced Moondream Prompt for More Comprehensive Item Detection
- Rewrote Moondream prompt to be more thorough and capture more items
- Added instruction: "list EVERY SINGLE OBJECT you can see placed on it, even if you're not completely certain"
- Expanded item examples to include: snack packages, food items, cans, CD cases, DVDs, magazines, notebooks, pens, containers
- Emphasizes "Be thorough and detailed - don't skip anything"
- Encourages Moondream to report items even with lower confidence
- Better captures edge cases like snack packages, papers, and small items that might be missed
- Results in more complete inventory listings from Moondream
- YOLO still provides accurate counts for common objects, Moondream adds everything else

### Fixed Moondream Prompt to Prevent Repetitive Listings
- Fixed bug where Moondream was listing each individual book separately (Book 1, Book 2, Book 3, etc.)
- Changed prompt to "list all TYPES of objects, grouped by category"
- Added explicit instruction: "don't list each individual item separately"
- Provided format example: "Books - 5, Bottles - 2" to guide output structure
- Changed from "EVERY SINGLE OBJECT" to "all TYPES of objects" for clarity
- Asks Moondream to count items of same type together
- Prevents infinite loops of repetitive item listings
- Still captures comprehensive inventory but in concise grouped format

### Adjusted Moondream to Give Approximate Counts to Prevent Over-Counting
- Fixed issue where Moondream was over-counting items when asked for exact counts
- Changed prompt to request "approximate count" using natural language (e.g. "a few books", "several bottles")
- Focuses Moondream on identifying item types rather than precise counting
- Added parsing for approximate terms: "a few" → 3, "several" → 3, "some" → 2
- YOLO provides accurate counts for detectable items (books, bottles, teddy bears)
- Moondream identifies additional item types that YOLO missed (tissue boxes, snacks, papers)
- Hybrid approach: YOLO for accuracy, Moondream for coverage
- Reduces over-counting errors while maintaining comprehensive item detection

### Restructured to New Strategy: Moondream Identifies, YOLO Counts
- **Complete strategy reversal**: Moondream runs FIRST, YOLO runs SECOND
- **Step 1 (Moondream)**: Identifies ALL item types present on shelf with approximate counts
- **Step 2 (YOLO)**: Provides accurate counts for items it CAN detect (books, bottles, teddy bears, etc.)
- **Step 3 (Merge)**: For each Moondream-identified item, use YOLO count if available, otherwise use Moondream's approximate count
- Console shows clear 3-step process with detailed merge decisions
- Merge function now prioritizes YOLO counts over Moondream approximations
- Items show source: "YOLO XX%" for accurate counts, "Moondream approx." for items YOLO can't detect
- Better overall accuracy: Moondream provides comprehensive coverage, YOLO corrects counts where possible
- Example: Moondream sees "books, tissue box, snacks" → YOLO counts books accurately → Final: accurate book count + approximate tissue/snack counts
- Solves the problem of YOLO missing items while still getting accurate counts for common objects

### Code Cleanup: Removed Unused Code
- Removed unused `compare_inventory()` function (was defined but never called)
- Removed unused `numpy` import (np was imported but never used)
- Removed redundant `if moondream_description:` check (already validated above)
- Removed unused `change_analysis` feature (was asking Moondream for change comparison but never effectively used)
- Simplified history storage by removing unused `changes` field
- Code is now cleaner with only actively used functions and imports

### Removed YOLO Completely - Moondream Only
- **User Feedback**: YOLO was not detecting items that Moondream found (e.g. Ritz Crackers, bottles of wine)
- **Removed all YOLO code**: Deleted `load_yolo_model()`, `detect_objects_yolo()`, and `merge_detections()` functions
- **Removed YOLO configuration**: Deleted `USE_YOLO_DETECTION`, `YOLO_CONFIDENCE_THRESHOLD`, and `yolo_model` global variable
- **Simplified detection logic**: Now uses ONLY Moondream for all item identification and counting
- **Removed multi-step process**: No more Step 1/Step 2/Step 3 - just direct Moondream identification
- **Cleaner output**: Console now shows simple Moondream results without YOLO/merge noise
- **All items labeled**: Every item now shows "Moondream AI" as source with "moondream" as source field
- **Faster execution**: No time wasted on YOLO inference that wasn't helpful
- **Simpler codebase**: Reduced from ~717 lines to ~475 lines by removing YOLO complexity
- **User preference**: YOLO was "not helpful at all" so removed entirely per user request

### Added Automatic Image Cleanup - Keep Only Last 12 Images (1 Hour)
- **Configuration**: Added `MAX_IMAGES = 12` to limit stored images to 1 hour of history
- **New Function**: `cleanup_old_images()` automatically removes old images after each capture
- **Smart Cleanup**: Sorts images by timestamp, keeps 12 most recent, deletes older ones
- **Automatic Execution**: Runs after both initial capture and each monitoring scan
- **Storage Management**: Prevents unlimited disk usage from continuous monitoring
- **Calculation**: 12 images × 5 minutes interval = 60 minutes (1 hour) of image history
- **Safe Cleanup**: Skips visualization files, handles errors gracefully
- **Console Feedback**: Shows which files are deleted and how many are kept
- **Benefit**: System can run indefinitely without filling up disk space

### Fixed Camera Index - Use /dev/video1 Instead of /dev/video0
- **Issue**: Program couldn't open camera because `/dev/video0` doesn't exist on this system
- **Error**: "VIDEOIO(V4L2:/dev/video0): can't open camera by index"
- **Fix**: Changed camera index from 0 to 1 in `cv2.VideoCapture(1)`
- **System**: This Raspberry Pi has cameras at `/dev/video1`, `/dev/video2`, etc., but not `/dev/video0`
- **Result**: Camera now opens successfully

### Added Manual Rescan Button in Web Dashboard
- **New Feature**: Added "🔄 Rescan Now" button in web dashboard header
- **Backend**: New Flask API endpoint `/api/rescan` (POST) to trigger immediate scan
- **Threading**: Uses `Event` object to signal monitoring loop for immediate rescan
- **Smart Waiting**: Main loop checks for rescan event every second instead of blocking for full 5 minutes
- **Button Feedback**: Shows "⏳ Scanning..." during scan, "✓ Scan Started!" on success
- **Auto-refresh**: Dashboard automatically refreshes 3 seconds after triggering rescan
- **User Experience**: No need to wait 5 minutes for next scan - can trigger manually anytime
- **Console Output**: Shows "[MANUAL RESCAN] Triggered from web dashboard!" when activated
- **UI Design**: Beautiful gradient button with hover effects and smooth animations
- **Error Handling**: Shows "✗ Error" if scan fails, button re-enables after 2 seconds

## 2025-11-06

### Created Lab 6 Project Documentation - Collaborative Robot Arm Control System
- **File**: Created `Lab 6/document.md` with comprehensive project documentation
- **Content**: Full documentation of collaborative robot arm project controlled by 3 Raspberry Pis
- **System Architecture**: Detailed description of Controller A (base/shoulder), Controller B (elbow/wrist), and Receiver (arm controller)
- **MQTT Communication**: Explained MQTT topic structure (`IDD/robotarm/#`), JSON payload format, and real-time message flow
- **Gameplay Concept**: Documented collaborative drawing game where 2 players control arm, 1 player guesses object
- **Technical Components**: Listed hardware (3× RPi 4, PCA9685 driver, 4× servos) and software (paho-mqtt, Adafruit libraries, Mosquitto broker)
- **Key Features**: Highlighted real-time distributed control, multi-user interaction, and creative engineering collaboration
- **Formatting**: Well-structured markdown with proper headings, bullet points, code formatting for topics/commands

### Added Technical Implementation Section to Lab 6 Documentation
- **Section Added**: "Technical Implementation" explaining the publisher-subscriber architecture
- **Content**: Detailed explanation of joystick input → JSON encoding → MQTT publish → subscribe → PWM signal generation flow
- **Architecture Details**: Describes Mosquitto MQTT broker, paho-mqtt asynchronous callbacks, and real-time operation
- **Scalability**: Documents modular design enabling easy integration of additional controllers or sensors
- **Technical Depth**: Explains PCA9685 servo driver usage, JSON payload parsing, and topic-based message routing
