import qwiic_twist
import time
import sys

def run_qwiic_twist_test():
    print("\nSparkFun Qwiic Twist Example Test\n")

    # Create a QwiicTwist object
    myTwist = qwiic_twist.QwiicTwist()

    # Check if the device is connected
    if not myTwist.connected:
        print("The Qwiic Twist device isn't connected. Please check your connection.", file=sys.stderr)
        return

    # Begin communication with the device
    if not myTwist.begin():
        print("Failed to initialize the Qwiic Twist.", file=sys.stderr)
        return

    print("Qwiic Twist initialized successfully.")

    # Set an initial color (e.g., a shade of purple)
    myTwist.set_color(100, 10, 50) 
    print("Initial LED color set to Red: 100, Green: 10, Blue: 50")

    print("Monitoring Qwiic Twist... Turn the knob or press the button.")

    while True:
        try:
            # Get the current count from the rotary encoder
            current_count = myTwist.count

            # Check if the button is pressed
            button_pressed = myTwist.pressed

            print(f"Count: {current_count}, Pressed: {'YES' if button_pressed else 'NO'}")

            time.sleep(0.3) # Adjust sleep time as needed for responsiveness vs. console spam

        except (KeyboardInterrupt, SystemExit):
            print("\nEnding Qwiic Twist Test.")
            sys.exit(0)
        except Exception as e:
            print(f"An error occurred: {e}", file=sys.stderr)
            time.sleep(1) # Wait before retrying

if __name__ == '__main__':
    run_qwiic_twist_test()