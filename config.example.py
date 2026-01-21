# StanzaCam Configuration
# Copy this file to config.py and fill in your API key

# Anthropic API Key - Get yours at https://console.anthropic.com/
ANTHROPIC_API_KEY = "your-api-key-here"

POEM_MAX_TOKENS = 300

# Multiple poem prompts - selected by rotary switch 1
POEM_PROMPTS = {
    1: "Write a short poem about this image.",
    2: "Write a haiku about this image.",
    3: "Write a limerick about this image.",
    4: "Write a short, whimsical poem about this image in the style of Shel Silverstein.",
    5: "Write a dramatic, emotional poem about this image.",
    6: "Write a humorous poem about this image.",
    7: "Write a minimalist, zen-like poem about this image.",
    8: "Describe this image as if you're a pirate writing in your ship's log."
}

# Model options - selected by rotary switch 2
CLAUDE_MODELS = {
    1: "claude-sonnet-4-5-20250929", # Balanced
    2: "claude-haiku-4-5-20251001",  # Fast & cheap
    3: "claude-sonnet-4-5-20250929", # Balanced (saving to file)
    4: "claude-haiku-4-5-20251001",  # Fast & cheap (saving to file)
}