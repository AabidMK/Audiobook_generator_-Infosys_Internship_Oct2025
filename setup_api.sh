#!/bin/bash
# Script to set up the API key for the audiobook generator

API_KEY="AIzaSyANGcvOBv4gBU5pXleVk_5R4J6qjSdOmak"

echo "Setting up Google Gemini API key..."

# Add to shell profile for permanent setup
if [[ "$SHELL" == *"zsh"* ]]; then
    PROFILE_FILE="$HOME/.zshrc"
elif [[ "$SHELL" == *"bash"* ]]; then
    PROFILE_FILE="$HOME/.bashrc"
else
    PROFILE_FILE="$HOME/.profile"
fi

# Check if already added
if grep -q "GEMINI_API_KEY" "$PROFILE_FILE" 2>/dev/null; then
    echo "⚠️  API key already found in $PROFILE_FILE"
    echo "You can update it manually or remove the old entry first."
else
    echo "" >> "$PROFILE_FILE"
    echo "# Google Gemini API Key for Audiobook Generator" >> "$PROFILE_FILE"
    echo "export GEMINI_API_KEY=\"$API_KEY\"" >> "$PROFILE_FILE"
    echo "✅ API key added to $PROFILE_FILE"
fi

# Export for current session
export GEMINI_API_KEY="$API_KEY"
echo "✅ API key set for current terminal session"
echo ""
echo "To use it in this session, run:"
echo "  source $PROFILE_FILE"
echo ""
echo "Or restart your terminal."

