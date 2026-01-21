# StanzaCam Configuration
# Copy this file to config.py and fill in your API key

# Anthropic API Key - Get yours at https://console.anthropic.com/
ANTHROPIC_API_KEY = "your-api-key-here"

# Claude model to use for poem generation
CLAUDE_MODEL = "claude-sonnet-4-5-20250929"

# Poem generation settings
POEM_MAX_TOKENS = 300
POEM_PROMPT = """Look at this photo and write a short, whimsical poem about what you see.
The poem should be 4-8 lines, suitable for printing on a small thermal receipt printer.
Keep lines short (under 32 characters each) so they fit nicely on the paper.
Be creative and capture the mood or essence of the image.
Only output the poem, nothing else."""
