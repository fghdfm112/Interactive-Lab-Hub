# Smart Shelf Monitor Project

## Overview

The Smart Shelf Monitor is an AI-powered inventory tracking system that uses computer vision and natural language processing to automatically monitor a shelf, recognize items, detect changes, and provide real-time updates through a beautiful web dashboard.

## 🎯 Project Goal

Create an intelligent monitoring system that can:
- Automatically identify what items are on a shelf
- Detect when items are added, removed, or moved
- Provide detailed descriptions of inventory changes
- Display everything through a live web interface

## 🛠️ Technology Stack

### Hardware
- **Raspberry Pi** with camera module or USB webcam
- Standard shelf or surface to monitor

### Software
- **Python 3** - Core programming language
- **OpenCV** - Computer vision for image capture
- **Moondream AI** - Vision language model for object recognition and scene understanding
- **Flask** - Web framework for dashboard
- **Ollama** - Local AI model server

## 📋 Features

### Core Functionality
1. **Automatic Inventory Recognition**
   - Uses Moondream vision AI to identify all items on shelf
   - Generates natural language descriptions of inventory
   - Scans every 5 minutes (configurable)

2. **Change Detection**
   - Compares current shelf state with previous scan
   - Identifies specific changes (what was added/removed/moved)
   - Provides detailed change analysis

3. **Persistent Storage**
   - Saves inventory history in JSON format (`shelf_inventory.json`)
   - Stores timestamped images of shelf states
   - Maintains last 20 snapshots in circular buffer

4. **Live Web Dashboard**
   - Beautiful, modern UI with gradient design
   - Real-time inventory display
   - Change history timeline
   - Auto-refreshing every 10 seconds
   - Mobile-responsive design

### Web Interface Components
- **Current Shelf View** - Live camera image
- **Current Inventory** - AI-generated item list
- **Change History** - Timeline of all detected changes
- **Live Status Indicator** - Shows system is running
- **Access Web Dashboard**
   - Open browser to `http://localhost:5000`
   - Or from another device: `http://YOUR_PI_IP:5000`

## 💡 Usage

### Starting the System
```bash
cd /home/pi/Interactive-Lab-Hub/Lab\ 5/
./partb.py
```

The system will:
1. Start the web server on port 5000
2. Capture initial shelf inventory
3. Begin monitoring every 5 minutes
4. Update the dashboard automatically

### Stopping the System
Press `Ctrl+C` in the terminal to stop monitoring

### Viewing Results
- **Web Dashboard**: http://localhost:5000
- **Inventory File**: `shelf_inventory.json`
- **Images**: `shelf_img/` folder

## 📊 How It Works

### Workflow

1. **Initialization**
   - System captures initial shelf image
   - Moondream AI analyzes and describes all visible items
   - Inventory saved to JSON file
   - Web server starts in background

2. **Monitoring Loop**
   - Wait for configured interval (5 minutes)
   - Capture new shelf image
   - Ask Moondream to list current items
   - Compare with previous inventory

3. **Change Detection**
   - If inventory descriptions differ:
     - Ask AI to identify specific changes
     - Announce changes on console
     - Update inventory database
     - Add to change history
     - Dashboard auto-updates

4. **Web Dashboard**
   - Displays latest shelf image
   - Shows current inventory list
   - Presents change history
   - Auto-refreshes every 10 seconds

## 🔍 Use Cases

### Retail
- Monitor product displays
- Track inventory levels
- Detect restocking needs
- Prevent theft/shrinkage

### Home
- Smart pantry monitoring
- Medicine cabinet tracking
- Tool organization
- Collectible inventory

### Laboratory
- Chemical inventory tracking
- Equipment monitoring
- Sample storage management

### Office
- Supply closet monitoring
- Equipment checkout tracking
- Document tracking
