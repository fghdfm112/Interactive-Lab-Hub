import paho.mqtt.client as mqtt
import json
import time
import board
import busio
import adafruit_pca9685
from adafruit_motor import servo

# =========================
# Servo Setup
# =========================
i2c = busio.I2C(board.SCL, board.SDA)
pca = adafruit_pca9685.PCA9685(i2c)
pca.frequency = 50

# Assign servos to PCA9685 channels
servo_channels = {
    "base": servo.Servo(pca.channels[0]),
    "shoulder": servo.Servo(pca.channels[1]),
    "elbow": servo.Servo(pca.channels[2]),
    "wrist": servo.Servo(pca.channels[3])
}

# =========================
# MQTT Setup
# =========================
MQTT_SERVER = "farlab.infosci.cornell.edu"
MQTT_PORT = 1883
MQTT_TOPIC_BASE = "IDD/robotarm"

MQTT_USER = "idd"
MQTT_PASSWORD = "device@theFarm"

# =========================
# MQTT Callbacks
# =========================
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(f"{MQTT_TOPIC_BASE}/#")  # Subscribe to all subtopics

def on_message(client, userdata, msg):
    print(f"Message received on topic: {msg.topic}")
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        print(f"Decoded payload: {payload}")

        # Move servos according to payload
        for joint, angle in payload.items():
            if joint in servo_channels:
                angle = float(angle)
                servo_channels[joint].angle = angle
                print(f"Moved {joint} to {angle} degrees")
            else:
                print(f"Unknown servo joint: {joint}")

    except Exception as e:
        print(f"Error handling message: {e}")

# =========================
# MQTT Client Initialization
# =========================
client = mqtt.Client()
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_SERVER, MQTT_PORT, 60)

# =========================
# Loop Forever
# =========================
print(f"Listening to topic: {MQTT_TOPIC_BASE}/# ...")
client.loop_forever()
