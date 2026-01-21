# StanzaCam

A Raspberry Pi instant camera that captures photos, generates AI poetry using Claude, and prints both on a thermal printer.

## Features

- Capture photos with Raspberry Pi Camera Module (with autofocus)
- Send photos to Claude AI to generate unique poems
- Print photos and poems on a thermal receipt printer
- RGB LED feedback for system status
- Rotary switch inputs for future customization

## Hardware Requirements

- Raspberry Pi (tested on Pi Zero 2 W)
- Raspberry Pi Camera Module 3 (with autofocus)
- Thermal receipt printer (e.g. Tiny, serial connection)
- RGB LED pushbutton
- 2x 8-position rotary switches
- Internet connection (for Claude API)

## Software Requirements

- Python 3
- Raspberry Pi OS

## Installation

### 1. Install system dependencies

```bash
sudo apt update
sudo apt install python3-pip python3-picamera2
```

### 2. Install Python packages

```bash
pip3 install "anthropic>=0.18.0" python-escpos Pillow RPi.GPIO
```

### 3. Configure your API key

Copy the example config file and add your API key:

```bash
cp config.example.py config.py
```

Edit `config.py` and replace `your-api-key-here` with your actual Anthropic API key:

```python
ANTHROPIC_API_KEY = "sk-ant-api03-xxxxx..."
```

**To get an API key:**
1. Go to [console.anthropic.com](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to API Keys
4. Create a new key and copy it

**Note:** `config.py` is in `.gitignore` to prevent accidentally committing your API key. The `config.example.py` file is safe to commit.

### 4. Configure serial port (for thermal printer)

Enable serial port on Raspberry Pi:

```bash
sudo raspi-config
```

Navigate to: Interface Options > Serial Port
- Login shell over serial: No
- Serial port hardware enabled: Yes

Reboot after changing settings.

## Configuration Options

Edit `config.py` to customize:

| Setting | Description | Default |
|---------|-------------|---------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | (required) |
| `CLAUDE_MODELS` | Claude model for poem generation | `claude-sonnet-4-5-20250929` |
| `POEM_MAX_TOKENS` | Maximum tokens for poem response | `300` |
| `POEM_PROMPTS` | Custom prompt for poem generation | (see config.py) |

## Usage

**Important:** Run the application from the project directory:

```bash
cd /path/to/StanzaCam
python3 Stanza_Main.py
```

**API Costs:** Each photo sent to Claude uses API credits. Monitor your usage at [console.anthropic.com](https://console.anthropic.com/). Typical poem generation costs a few cents per image.

### LED Status Colors

| Color | Meaning |
|-------|---------|
| Solid Magenta | Starting up |
| Solid Any | Camera focused, prompt chosen, ready to capture |
| Blinking Red | Camera not focused |
| Flashing Blue | Photo captured |
| Blinking White | Waiting for print confirmation |
| Blinking Cyan | Generating poem with Claude AI |

### Taking a Photo

1. Choose your prompt with rotary switch 1 and Claude model with switch 2
2. Wait for the LED be a solid color (camera focused)
3. Press the pushbutton to capture
4. LED flashes **blue** to confirm capture
5. LED blinks **white** - press again within 3 seconds to print
6. LED blinks **cyan** while generating poem
7. Photo and poem print automatically

## Troubleshooting

### "ERROR: config.py not found"
Make sure `config.py` exists in the same directory as `Stanza_Main.py`.

### "ERROR: Valid API key not configured"
Edit `config.py` and add your Anthropic API key.

### "ERROR: Could not connect to Claude API"
Check your internet connection. The Pi needs network access to reach the Claude API.

### "ERROR: Invalid API key"
Verify your API key is correct in `config.py`. Keys start with `sk-ant-`.

### Printer not responding
- Check serial cable connection
- Verify serial port is enabled in raspi-config
- Ensure printer is powered on
- Run `Sys_Check.py` to test hardware

## Files

| File | Description |
|------|-------------|
| `Stanza_Main.py` | Main application |
| `Sys_Check.py` | Hardware diagnostic utility |
| `config.example.py` | Example configuration (copy to config.py) |
| `config.py` | Your configuration with API key (git-ignored) |

## Running Diagnostics

To test all hardware components:

```bash
python3 Sys_Check.py
```

This will cycle through LED colors, test printer communication, and monitor inputs.

## License

MIT
