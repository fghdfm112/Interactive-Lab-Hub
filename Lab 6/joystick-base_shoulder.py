from __future__ import print_function
import qwiic_joystick
import time
import sys
import paho.mqtt.client as mqtt
import json
import math # Added for angle calculations

# --- ADDED: Display Imports ---
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789
# ---

# --- MQTT Configuration ---
MQTT_BROKER = "farlab.infosci.cornell.edu"
MQTT_PORT = 1883
MQTT_TOPIC = "IDD/robotarm" 
MQTT_USER = "idd"
MQTT_PASSWORD = "device@theFarm"

# --- Servo Configuration ---
BASE_SERVO_MIN_ANGLE = 0
BASE_SERVO_MAX_ANGLE = 180
SHOULDER_SERVO_MIN_ANGLE = 70
SHOULDER_SERVO_MAX_ANGLE = 150

# --- Joystick Configuration ---
JOYSTICK_MIN = 0
JOYSTICK_MAX = 1023
JOYSTICK_CENTER = 512 # Assumes a 10-bit joystick (0-1023)
JOYSTICK_DEADZONE = 25 # +/- this value from center is treated as 0
SENSITIVITY = 0.5    # How fast the angle changes. Higher = faster.
LOOP_DELAY = 0.05    # Loop speed in seconds (20 Hz). Faster loop = smoother control.

# --- State Variables ---
# Store the current angle, starting at the middle position.
current_joint1_angle = (BASE_SERVO_MIN_ANGLE + BASE_SERVO_MAX_ANGLE) / 2
current_joint2_angle = (SHOULDER_SERVO_MIN_ANGLE + SHOULDER_SERVO_MAX_ANGLE) / 2

last_sent_joint1 = None
last_sent_joint2 = None
last_sent_button = None

# --- MQTT Setup ---
def on_connect(client, userdata, flags, rc):
	if rc == 0:
		print(f"Connected to MQTT Broker: {MQTT_BROKER}")
	else:
		print("Failed to connect, return code %d\n" % rc)

try:
	client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
except AttributeError:
	print("Using legacy MQTT Client initialization.")
	client = mqtt.Client()

client.on_connect = on_connect

client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

try:
	client.connect(MQTT_BROKER, MQTT_PORT, 60)
except Exception as e:
	print(f"Could not connect to MQTT broker: {e}", file=sys.stderr)
	sys.exit(1)

client.loop_start()

# --- Display Setup ---

# Configuration for CS and DC pins:
cs_pin = digitalio.DigitalInOut(board.D5) 
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None

# Config for display baudrate:
BAUDRATE = 64000000

# Setup SPI bus using hardware SPI:
spi = board.SPI()

# Create the ST7789 display:
disp = st7789.ST7789(
	spi,
	cs=cs_pin,
	dc=dc_pin,
	rst=reset_pin,
	baudrate=BAUDRATE,
	width=135,
	height=240,
	x_offset=53,
	y_offset=40,
)

# Create blank image for drawing.
height = disp.width  # swap height/width for landscape
width = disp.height
image = Image.new("RGB", (width, height))
rotation = 90

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Load font
try:
	font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
except IOError:
	print("Default font not found, using a basic bitmap font.")
	font = ImageFont.load_default()

# Turn on the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

# --- Visual Arm Parameters ---
ARM_SEGMENT_LENGTH = 70 # Length of the arm segment
BASE_X, BASE_Y = width // 2, height - 10 # Base of the arm on the screen (bottom center)
JOINT_THICKNESS = 3
JOINT_COLOR = (0, 255, 0) # Green for the arm
WHITE = (255, 255, 255)

# --- Main Program Logic ---
def runExample():
	global current_joint1_angle, current_joint2_angle
	global last_sent_joint1, last_sent_joint2, last_sent_button
	
	# Get display variables from the global scope for use in loop
	global image, draw, disp, rotation, width, height, font, BASE_X, BASE_Y

	myJoystick = qwiic_joystick.QwiicJoystick()

	if myJoystick.connected == False:
		print("The Qwiic Joystick device isn't connected...", file=sys.stderr)
		# Continue to run the display logic even if joystick is disconnected
		pass 

	myJoystick.begin()

	while True:
		# Read raw joystick values
		x_val = myJoystick.horizontal
		y_val = myJoystick.vertical
		button_val = myJoystick.button

		# 1. Calculate "speed" by subtracting the center
		x_speed = x_val - JOYSTICK_CENTER
		y_speed = y_val - JOYSTICK_CENTER
		
		# 2. Apply the dead zone
		if abs(x_speed) < JOYSTICK_DEADZONE:
			x_speed = 0
		if abs(y_speed) < JOYSTICK_DEADZONE:
			y_speed = 0

		# 3. Calculate the change (delta) based on speed and sensitivity
		if x_speed != 0:
			# Joint 1: Base (pan)
			delta_joint1 = x_speed * SENSITIVITY * LOOP_DELAY
			current_joint1_angle += delta_joint1

		if y_speed != 0:
			# Joint 2: Shoulder (tilt). Sensitivity adjusted by 0.25 as per original code.
			delta_joint2 = y_speed * SENSITIVITY * LOOP_DELAY * 0.25
			current_joint2_angle += delta_joint2
			
		# 4. Clamp the angles to stay within servo limits (using the specific BASE/SHOULDER limits)
		current_joint1_angle = max(BASE_SERVO_MIN_ANGLE, min(current_joint1_angle, BASE_SERVO_MAX_ANGLE))
		current_joint2_angle = max(SHOULDER_SERVO_MIN_ANGLE, min(current_joint2_angle, SHOULDER_SERVO_MAX_ANGLE))

		# Get the integer values for comparison and MQTT
		int_joint1 = int(current_joint1_angle) # Base
		int_joint2 = int(current_joint2_angle) # Shoulder
		
		# --- MQTT Logic (Send if any state changed) ---
		if (int_joint1 != last_sent_joint1) or \
		   (int_joint2 != last_sent_joint2) or \
		   (button_val != last_sent_button):
			
			# 5. Create JSON payload (Updated keys to "base" and "shoulder")
			payload_data = {
				"base": int_joint1,
				"shoulder": int_joint2,
				"button": button_val
			}
			json_payload = json.dumps(payload_data)
			
			# 6. Publish the message
			client.publish(MQTT_TOPIC, json_payload)

			print(f"Sending: Base: {int_joint1}, Shoulder: {int_joint2}")

			# 7. Update the last sent state
			last_sent_joint1 = int_joint1
			last_sent_joint2 = int_joint2
			last_sent_button = button_val
		
		# --- ADDED: Display Logic with Visual Arm ---
		draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))

		# --- Arm Segment Endpoints Calculation ---
		
		# The 'Base' joint (int_joint1) usually controls the rotation of the entire arm around the Z-axis (horizontal sweep).
		# For a simple 2D side view, we'll represent the BASE angle by a horizontal line, 
		# and the SHOULDER angle by the vertical sweep.
		
		# 1. Base Joint Visualization (Horizontal Line at the Bottom)
		base_viz_length = width // 3
		
		# Map 0-180 to a rotation angle. For a simple horizontal bar:
		# Let 90 degrees be straight. Base only controls the horizontal position of the start point.
		# Use the BASE angle to position the base point horizontally (X-axis).
		x_offset = (int_joint1 - 90) / 90 * (width // 4) # Maps 0-180 to approx -width/4 to +width/4
		base_start_x = (width // 2) + x_offset
		
		# Draw a simple vertical post for the Base
		draw.line((base_start_x, BASE_Y, base_start_x, BASE_Y - 10), fill=JOINT_COLOR, width=JOINT_THICKNESS)
		
		# 2. Shoulder Joint Visualization (The main arm segment)
		shoulder_start_x, shoulder_start_y = base_start_x, BASE_Y - 10

		# Shoulder Angle: Map servo limits (70-150) to an absolute angle for display (e.g., 90=straight up)
		# 70 (MIN) -> lowest position (e.g., 150 degrees, down-left)
		# 110 (MID) -> straight out (e.g., 90 degrees, straight up)
		# 150 (MAX) -> highest position (e.g., 30 degrees, up-right)
		
		# Interpolate the shoulder angle from its range (70 to 150) to a display angle range (e.g., 150 to 30)
		shoulder_range = SHOULDER_SERVO_MAX_ANGLE - SHOULDER_SERVO_MIN_ANGLE # 80 degrees
		shoulder_norm = (int_joint2 - SHOULDER_SERVO_MIN_ANGLE) / shoulder_range # 0.0 to 1.0
		
		# Map 0.0 to 150 degrees and 1.0 to 30 degrees for a rising sweep
		display_angle_deg = 150 - (shoulder_norm * 120) 
		shoulder_angle_rad = math.radians(display_angle_deg)
		
		shoulder_end_x = shoulder_start_x + ARM_SEGMENT_LENGTH * math.cos(shoulder_angle_rad)
		shoulder_end_y = shoulder_start_y - ARM_SEGMENT_LENGTH * math.sin(shoulder_angle_rad) # Subtract for screen Y

		# Draw the arm segment
		draw.line((shoulder_start_x, shoulder_start_y, shoulder_end_x, shoulder_end_y), fill=JOINT_COLOR, width=JOINT_THICKNESS)

		# Draw circles for the joints
		JOINT_DOT_RADIUS = 4
		# Shoulder Joint
		draw.ellipse((shoulder_start_x - JOINT_DOT_RADIUS, shoulder_start_y - JOINT_DOT_RADIUS,
					  shoulder_start_x + JOINT_DOT_RADIUS, shoulder_start_y + JOINT_DOT_RADIUS), fill=WHITE)
		# End Effector
		draw.ellipse((shoulder_end_x - JOINT_DOT_RADIUS, shoulder_end_y - JOINT_DOT_RADIUS,
					  shoulder_end_x + JOINT_DOT_RADIUS, shoulder_end_y + JOINT_DOT_RADIUS), fill=WHITE)

		# --- Text Display ---
		text_joint1 = f"Base: {int_joint1}°"
		text_joint2 = f"Shoulder: {int_joint2}°"
		# text_button = f"Btn: {'P' if button_val == 0 else 'R'}" # Qwiic Button is active LOW

		# Set coordinates for text (top-left adjusted)
		padding = 5
		text_x = padding
		text_y = padding

		# Draw the text
		draw.text((text_x, text_y), text_joint1, font=font, fill=WHITE)
		draw.text((text_x, text_y + 20), text_joint2, font=font, fill=WHITE)
		# draw.text((text_x, text_y + 40), text_button, font=font, fill=WHITE)

		# Display image.
		disp.image(image, rotation)
		# --- End Display Logic ---

		# Sleep for a short time
		time.sleep(LOOP_DELAY)

if __name__ == '__main__':
	try:
		runExample()
	except (KeyboardInterrupt, SystemExit) as exErr:
		print("\nEnding Program")
		client.loop_stop()
		client.disconnect()
		sys.exit(0)