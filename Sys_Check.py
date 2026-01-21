# StanzaCam V1.0 - SysCheck

import time
import RPi.GPIO as GPIO
import os
os.environ["LIBCAMERA_LOG_LEVELS"] = "ERROR"  # Only show errors, not INFO
from picamera2 import Picamera2
from escpos.printer import Serial
from PIL import Image
from io import BytesIO

# GPIO Pin Aliases
PB_Red = 19
PB_Green = 13
PB_Blue = 12
DTR = 18
PB_NO = 26
ROT_1_1 = 4
ROT_1_2 = 17
ROT_1_3 = 27
ROT_1_4 = 22
ROT_1_5 = 10
ROT_1_6 = 9
ROT_1_7 = 11
ROT_1_8 = 5
ROT_2_1 = 23
ROT_2_2 = 24
ROT_2_3 = 25
ROT_2_4 = 8
ROT_2_5 = 7
ROT_2_6 = 16
ROT_2_7 = 20
ROT_2_8 = 21


def pushbutton_led_test(delay=1.0):
    # Red
    GPIO.output(PB_Red,   GPIO.LOW)
    GPIO.output(PB_Green, GPIO.HIGH)
    GPIO.output(PB_Blue,  GPIO.HIGH)
    time.sleep(delay)

    # Green
    GPIO.output(PB_Red,   GPIO.HIGH)
    GPIO.output(PB_Green, GPIO.LOW)
    GPIO.output(PB_Blue,  GPIO.HIGH)
    time.sleep(delay)

    # Blue
    GPIO.output(PB_Red,   GPIO.HIGH)
    GPIO.output(PB_Green, GPIO.HIGH)
    GPIO.output(PB_Blue,  GPIO.LOW)
    time.sleep(delay)

    # Magenta
    GPIO.output(PB_Red,   GPIO.LOW)
    GPIO.output(PB_Green, GPIO.HIGH)
    GPIO.output(PB_Blue,  GPIO.LOW)
    time.sleep(delay)

    # Cyan
    GPIO.output(PB_Red,   GPIO.HIGH)
    GPIO.output(PB_Green, GPIO.LOW)
    GPIO.output(PB_Blue,  GPIO.LOW)
    time.sleep(delay)

    # Yellow
    GPIO.output(PB_Red,   GPIO.LOW)
    GPIO.output(PB_Green, GPIO.LOW)
    GPIO.output(PB_Blue,  GPIO.HIGH)
    time.sleep(delay)

    # White
    GPIO.output(PB_Red,   GPIO.LOW)
    GPIO.output(PB_Green, GPIO.LOW)
    GPIO.output(PB_Blue,  GPIO.LOW)
    time.sleep(delay)

    # Off
    GPIO.output(PB_Red,   GPIO.HIGH)
    GPIO.output(PB_Green, GPIO.HIGH)
    GPIO.output(PB_Blue,  GPIO.HIGH)
    time.sleep(delay)

def printer_comms_test():
    try:
        # Clear buffers
        printer.device.reset_input_buffer()
        printer.device.reset_output_buffer()

        # Request printer status
        printer._raw(b'\x10\x04\x01')  # DLE EOT 1 - Request printer status
        time.sleep(0.2)  # Give printer time to respond

        # Check for response
        if printer.device.in_waiting > 0:
            response = printer.device.read(printer.device.in_waiting)
            print("Printer connected and responding!")
            return True
        else:
            print("ERROR: No response from printer!")
            return False

    except Exception as e:
        print(f"ERROR: Printer test failed - {e}")
        return False

def printer_print_test():
    # Default (raster)
    # printer.image("lmao.PNG", center=True)
    #
    # Column mode (may fix stretching)
    # printer.image("lmao.PNG", center=True, impl="bitImageColumn")
    #
    # img = Image.open("lmao.PNG")
    # aspect_ratio = img.height / img.width
    # new_width = 384
    # new_height = int(new_width * aspect_ratio)
    # img = img.resize((new_width, new_height), Image.LANCZOS)

    # 32 characters per row
    printer.text("lmaolmaolmaolmaolmaolmaolmaolmao"
                 "lmaolmaolmaolmaolmaolmaolmaolmao"
                 "lmaolmaolmaolmaolmaolmaolmaolmao")

    printer.image("lmao.PNG", center=True, impl="bitImageColumn")
    printer.text("\n\n")

def is_focused(picam2):
    """Check if camera is currently focused"""
    # AfState values:
    # 0 = Idle
    # 1 = Scanning
    # 2 = Focused
    # 3 = Failed
    metadata = picam2.capture_metadata()
    af_state = metadata.get("AfState")
    return af_state == 2  # 2 = Focused

def take_image():
    filename = f"capture_{time.strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
    picam2.capture_file(filename)
    # picam2.capture_file("test.jpg")
    print(f"Image captured: {filename}")

def camera_test():
    try:
        picam2 = Picamera2()
        config = picam2.create_still_configuration()
        picam2.configure(config)
        picam2.set_controls({
            "AfMode": 2,  # Continuous
            "AfSpeed": 1  # Fast
        })

        picam2.start()
        time.sleep(3)

        camera_working = False
        while not camera_working:
            if is_focused(picam2):
                print("\nFocus achieved!")
                print("Attempting to take image...")
                picam2.capture_file("test.jpg")
                print(f"Image captured!")
                camera_working = True
            else:
                print("Waiting for focus...", end="\r", flush=True)
                time.sleep(0.1)  # Check focus frequently

    except IndexError:
        print("ERROR: Camera not detected!")
    except Exception as e:
        print(f"ERROR: Camera test failed - {e}")

def read_rotary_position(rotary_num):
    pins = []
    if rotary_num == 1:
        pins = [ROT_1_1, ROT_1_2, ROT_1_3, ROT_1_4, ROT_1_5, ROT_1_6, ROT_1_7, ROT_1_8]
    elif rotary_num == 2:
        pins = [ROT_2_1, ROT_2_2, ROT_2_3, ROT_2_4, ROT_2_5, ROT_2_6, ROT_2_7, ROT_2_8]

    for i, pin in enumerate(pins, start=1):
        if GPIO.input(pin) == GPIO.HIGH:
            return i

    return 0  # No position detected

def read_pushbutton_state():
    if GPIO.input(PB_NO) == GPIO.HIGH:
        return 1
    else:
        return 0

def rotary_pushbutton_test():
    while True:
        rot_1_pos = read_rotary_position(1)
        rot_2_pos = read_rotary_position(2)
        pushbutton_state = read_pushbutton_state()
        print(f"Rotary Switch 1:  {rot_1_pos}")  # 0 means unconnected
        print(f"Rotary Switch 2:  {rot_2_pos}")  # 0 means unconnected
        print(f"Pushbutton State: {pushbutton_state}")  # 0 means not pressed/unconnected
        print("\033[3A", end='')  # Move up 3 lines
        time.sleep(0.1)


try:
    print("Beginning system check...")

    # Setup GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PB_Red, GPIO.OUT)
    GPIO.setup(PB_Green, GPIO.OUT)
    GPIO.setup(PB_Blue, GPIO.OUT)
    GPIO.setup(PB_NO, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(ROT_1_1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(ROT_1_2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(ROT_1_3, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(ROT_1_4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(ROT_1_5, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(ROT_1_6, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(ROT_1_7, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(ROT_1_8, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(ROT_2_1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(ROT_2_2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(ROT_2_3, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(ROT_2_4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(ROT_2_5, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(ROT_2_6, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(ROT_2_7, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(ROT_2_8, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    # Start all OFF
    GPIO.output(PB_Red, GPIO.HIGH)
    GPIO.output(PB_Green, GPIO.HIGH)
    GPIO.output(PB_Blue, GPIO.HIGH)

    # Create PWM objects
    # pwm_r = GPIO.PWM(PB_Red, 1000)
    # pwm_b = GPIO.PWM(PB_Blue, 1000)

    # Printer Setup
    printer = Serial(devfile='/dev/serial0', baudrate=9600, timeout=1)
    printer.profile.profile_data['media']['width']['pixels'] = 384
    printer.profile.profile_data['media']['width']['mm'] = 48  # Effective, Actual is 57.5mm
    printer._raw(b'\x1B\x40')  # ESC @ - Initialize printer (clears buffer)
    # printer.set(density=4)
    time.sleep(0.5)
    # Clear any junk from serial buffers
    printer.device.reset_input_buffer()
    printer.device.reset_output_buffer()
    time.sleep(0.5)


    print("Testing pushbutton LEDs...")
    # FLASH ALL COLORS OF PUSHBUTTON
    pushbutton_led_test(1.0)
    pushbutton_led_test(0.5)

    print("Testing thermal printer...")
    # PRINT SOME TEST TEXT AND A TEST IMAGE (LMAO)
    if printer_comms_test():
        print("Performing test print...")
        printer_print_test()

    print("Testing camera...")
    # TRY TO CHECK AUTOFOCUS AND TAKE A PICTURE IF SUCCESSFUL
    camera_test()

    print("Testing rotary switch and pushbutton states...")
    # VERIFY SWITCHES ARE CONNECTED THEN DISPLAY THE CORRESPONDING POSITION IN A LOOP
    # ROTARY KNOBS CAN READ AS UNCONNECTED INBETWEEN POSITIONS! MAKE SURE TO ADD AN APPROPRIATE DELAY WHEN POLLING
    # ALSO ADD CASE FOR IF A 0 IS READ - E.G. IF A 0 IS READ TRY REREADING A FEW MORE TIMES TO CONFIRM IF TRANSIENT OR NOT
    # ALSO ADD DEBOUNCING FOR PUSHBUTTON
    rotary_pushbutton_test()


except KeyboardInterrupt:
    print("\n\n\nStopping...")
    GPIO.cleanup()

# ALT+A, ALT+/, CTRL+K quick delete nano file