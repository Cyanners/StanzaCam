# StanzaCam V1.1 - Now with Claude AI Poetry!

import time
import RPi.GPIO as GPIO
import os
import base64
os.environ["LIBCAMERA_LOG_LEVELS"] = "ERROR"  # Only show errors, not INFO
from picamera2 import Picamera2
from escpos.printer import Serial
from PIL import Image
import anthropic

# Import configuration
try:
    from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, POEM_MAX_TOKENS, POEM_PROMPT
except ImportError:
    print("ERROR: config.py not found! Copy config.py and add your API key.")
    ANTHROPIC_API_KEY = None
    CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
    POEM_MAX_TOKENS = 300
    POEM_PROMPT = "Write a short poem about this image."

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

def print_image():
    # Default (raster)
    # printer.image("lmao.PNG", center=True)

    # Column mode (may fix stretching)
    # printer.image("lmao.PNG", center=True, impl="bitImageColumn")

    img = Image.open("test.jpg")
    aspect_ratio = img.height / img.width
    new_width = 384
    new_height = int(new_width * aspect_ratio)
    img = img.resize((new_width, new_height), Image.LANCZOS)

    printer.text("\n")
    # printer.image(img, center=True)  # Raster method, can cause stretching and weird buffer issues
    printer.image(img, center=True, impl="bitImageColumn")  # Column method, fixes stretching and buffer issues but has lines along image width
    printer.text("\n\n")


def generate_poem_from_image(image_path):
    """Send image to Claude API and get a poem back"""
    if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY == "your-api-key-here":
        print("ERROR: Valid API key not configured in config.py")
        return None

    try:
        # Read and encode image as base64
        with open(image_path, "rb") as image_file:
            image_data = base64.standard_b64encode(image_file.read()).decode("utf-8")

        # Determine media type
        if image_path.lower().endswith(".png"):
            media_type = "image/png"
        else:
            media_type = "image/jpeg"

        # Create Anthropic client
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        # Send image to Claude with poem prompt
        print("Sending image to Claude for poem generation...")
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=POEM_MAX_TOKENS,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": POEM_PROMPT
                        }
                    ],
                }
            ],
        )

        # Extract poem text from response (with safety check)
        if message.content and hasattr(message.content[0], 'text'):
            poem = message.content[0].text
            print("Poem generated successfully!")
            print("-" * 32)
            print(poem)
            print("-" * 32)
            return poem
        else:
            print("ERROR: Unexpected response format from Claude")
            return None

    except anthropic.APIConnectionError:
        print("ERROR: Could not connect to Claude API. Check internet connection.")
        return None
    except anthropic.AuthenticationError:
        print("ERROR: Invalid API key. Check config.py")
        return None
    except anthropic.RateLimitError:
        print("ERROR: API rate limit exceeded. Wait and try again.")
        return None
    except anthropic.APIStatusError as e:
        print(f"ERROR: API error {e.status_code} - {e.message}")
        return None
    except Exception as e:
        print(f"ERROR: Failed to generate poem - {e}")
        return None


def print_poem(poem_text):
    """Print poem text on thermal printer"""
    if not poem_text:
        return False

    try:
        printer.text("\n")
        printer.set(align='center')

        # Print each line of the poem
        for line in poem_text.strip().split('\n'):
            # Wrap long lines to fit 32 char width
            while len(line) > 32:
                # Find last space before 32 chars
                wrap_point = line[:32].rfind(' ')
                if wrap_point == -1:
                    wrap_point = 32
                printer.text(line[:wrap_point] + "\n")
                line = line[wrap_point:].strip()
            printer.text(line + "\n")

        printer.text("\n")
        printer.set(align='left')  # Reset alignment
        printer.text("~ StanzaCam + Claude AI ~\n")
        printer.text("\n\n\n")  # Feed paper
        print("Poem printed successfully!")
        return True

    except Exception as e:
        print(f"ERROR: Failed to print poem - {e}")
        return False


def print_image_with_poem():
    """Print the captured image followed by a Claude-generated poem"""
    # Print the image first
    img = Image.open("test.jpg")
    aspect_ratio = img.height / img.width
    new_width = 384
    new_height = int(new_width * aspect_ratio)
    img = img.resize((new_width, new_height), Image.LANCZOS)

    printer.text("\n")
    printer.image(img, center=True, impl="bitImageColumn")
    printer.text("\n")

    # Generate and print poem
    poem = generate_poem_from_image("test.jpg")
    if poem:
        print_poem(poem)
    else:
        printer.text("\n[Poem generation failed]\n\n\n")

def is_focused():
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
    # picam2.capture_file(filename)
    picam2.capture_file("test.jpg")
    print(f"Image captured: {filename}")

def take_image_cropped_rotated():
    filename = f"capture_{time.strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
    picam2.capture_file("temp.jpg")

    # Open full resolution image
    img = Image.open("temp.jpg")

    # Rotate first (since camera is mounted sideways)
    img = img.transpose(Image.Transpose.ROTATE_270)  # Or ROTATE_90 - try both

    # Now image is portrait (2592x4608)
    # Crop center to 1920x1080 landscape
    width, height = img.size

    # Calculate crop box for centered 1920x1080
    left = (width - 1920) // 2
    top = (height - 1080) // 2
    right = left + 1920
    bottom = top + 1080

    img = img.crop((left, top, right, bottom))
    img.save("test.jpg")
    print(f"Image captured: {filename}")

def camera_focus_loop():
    global focus_count

    if is_focused():
        if focus_count < 10:  # Must achieve focus 10 times
            focus_count += 1
            if focus_count == 10:
                print("Focus achieved!")
    else:
        if focus_count >= 10:
            print("Lost focus!")
        focus_count = 0

    if focus_count >= 10:
        focused = True
        pb_change_led("GREEN")
    else:
        focused = False
        pb_change_led("RED")

    return focused

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

def wait_for_pushbutton_press(timeout=3.0):
    start_time = time.time()

    while time.time() - start_time < timeout:
        if read_pushbutton_state() == 1:
            return True  # Button was pressed
        time.sleep(0.01)  # Check every 10ms

    return False  # Timeout - button not pressed

def pb_change_led(colour):
    if colour == "RED":
        GPIO.output(PB_Red,   GPIO.LOW)
        GPIO.output(PB_Green, GPIO.HIGH)
        GPIO.output(PB_Blue,  GPIO.HIGH)
    elif colour == "GREEN":
        GPIO.output(PB_Red,   GPIO.HIGH)
        GPIO.output(PB_Green, GPIO.LOW)
        GPIO.output(PB_Blue,  GPIO.HIGH)
    elif colour == "BLUE":
        GPIO.output(PB_Red,   GPIO.HIGH)
        GPIO.output(PB_Green, GPIO.HIGH)
        GPIO.output(PB_Blue,  GPIO.LOW)
    elif colour == "MAGENTA":
        GPIO.output(PB_Red,   GPIO.LOW)
        GPIO.output(PB_Green, GPIO.HIGH)
        GPIO.output(PB_Blue,  GPIO.LOW)
    elif colour == "CYAN":
        GPIO.output(PB_Red,   GPIO.HIGH)
        GPIO.output(PB_Green, GPIO.LOW)
        GPIO.output(PB_Blue,  GPIO.LOW)
    elif colour == "YELLOW":
        GPIO.output(PB_Red,   GPIO.LOW)
        GPIO.output(PB_Green, GPIO.LOW)
        GPIO.output(PB_Blue,  GPIO.HIGH)
    elif colour == "WHITE":
        GPIO.output(PB_Red,   GPIO.LOW)
        GPIO.output(PB_Green, GPIO.LOW)
        GPIO.output(PB_Blue,  GPIO.LOW)
    elif colour == "OFF":
        GPIO.output(PB_Red,   GPIO.HIGH)
        GPIO.output(PB_Green, GPIO.HIGH)
        GPIO.output(PB_Blue,  GPIO.HIGH)

def pb_flash_colour(col, num=3, delay=0.25):
    for _ in range(num):
        pb_change_led(col)
        time.sleep(delay)
        pb_change_led("OFF")
        time.sleep(delay)


try:
    print("StanzaCam V1.1")

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

    # Start PB LED magenta to indicate starting up
    pb_change_led("MAGENTA")

    # Camera Setup
    picam2 = Picamera2()
    config = picam2.create_still_configuration()
    picam2.configure(config)
    picam2.set_controls({
        "AfMode": 2,  # Continuous
        "AfSpeed": 1  # Fast
    })

    picam2.start()
    time.sleep(3)

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

    # -------------------- MAIN --------------------

    rot_1_old = 0
    rot_2_old = 0
    pb_state_old = 0
    focus_count = 0
    focused = False
    while True:
        # Get latest state of switches
        rot_1 = read_rotary_position(1)
        rot_2 = read_rotary_position(2)
        pb_state = read_pushbutton_state()

        # Stuff here will run continuously

        focused = camera_focus_loop()

        # print(f"DEBUG: focused={focused}, focus_count={focus_count}")

        # Check switches AFTER updating everything else (e.g. focus)
        # One of the switches has changed
        if rot_1 != rot_1_old or rot_2 != rot_2_old or pb_state != pb_state_old:
            while rot_1 == 0 or rot_2 == 0:  # If rotarys read a 0, loop and re-read
                time.sleep(0.02)  # 20ms of debounce then re-read states
                rot_1 = read_rotary_position(1)
                rot_2 = read_rotary_position(2)
                pb_state = read_pushbutton_state()

            # Stuff here will only run once on change of any of the switches

            # Taking image when properly focused
            if focused and pb_state == 1:
                print("Taking image...")
                pb_change_led("YELLOW")
                take_image()
                pb_flash_colour("BLUE", num=5, delay=0.2)
                pb_change_led("WHITE")
                print_requested = wait_for_pushbutton_press()
                if print_requested:
                    if printer_comms_test():
                        pb_change_led("CYAN")  # Cyan = generating poem
                        print_image_with_poem()
                focused = False
                focus_count = 0

            # Taking image when NOT properly focused
            elif not focused and pb_state == 1:
                print("Not focused!")
                pb_flash_colour("RED", num=3, delay=0.2)

        # Store old states of switches for comparison next loop
        rot_1_old = rot_1
        rot_2_old = rot_2
        pb_state_old = pb_state

        # Run 50 times a second
        time.sleep(0.02)

except KeyboardInterrupt:
    print("\n\n\nStopping...")
    GPIO.cleanup()

# ALT+A, ALT+/, CTRL+K quick delete nano file