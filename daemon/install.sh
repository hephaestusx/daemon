#!/bin/bash
set -e

DAEMON_DIR="$HOME/.daemon"
REPO="https://github.com/yourusername/daemon"

echo ""
echo "  ⚡ Daemon installer"
echo "  Ask your homelab anything."
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
  echo "  ✗ Python 3 not found. Install it first: https://python.org"
  exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(sys.version_info.minor)')
if [ "$PYTHON_VERSION" -lt 9 ]; then
  echo "  ✗ Python 3.9+ required. You have 3.$PYTHON_VERSION"
  exit 1
fi

echo "  ✓ Python 3.$PYTHON_VERSION found"

# Check pip
if ! command -v pip3 &>/dev/null; then
  echo "  ✗ pip3 not found. Install it with: sudo apt install python3-pip"
  exit 1
fi

echo "  ✓ pip found"

# Clone or update
if [ -d "$DAEMON_DIR" ]; then
  echo "  → Updating existing install at $DAEMON_DIR"
  cd "$DAEMON_DIR" && git pull
else
  echo "  → Installing to $DAEMON_DIR"
  git clone "$REPO" "$DAEMON_DIR"
fi

cd "$DAEMON_DIR"

# Install deps
echo "  → Installing dependencies..."
pip3 install -r requirements.txt -q

# Make CLI executable
chmod +x daemon.py

# Add to PATH if not already there
SHELL_RC="$HOME/.bashrc"
if [[ "$SHELL" == *"zsh"* ]]; then
  SHELL_RC="$HOME/.zshrc"
fi

if ! grep -q "daemon" "$SHELL_RC" 2>/dev/null; then
  echo "alias daemon='python3 $DAEMON_DIR/daemon.py'" >> "$SHELL_RC"
  echo "  ✓ Added 'daemon' command to $SHELL_RC"
fi

# Init notes file
if [ ! -f "$DAEMON_DIR/notes.json" ]; then
  echo "[]" > "$DAEMON_DIR/notes.json"
fi

echo ""
echo "  ✓ Daemon installed."
echo ""
echo "  Starting setup..."
echo ""

# Open browser and start server
if command -v xdg-open &>/dev/null; then
  (sleep 1.5 && xdg-open http://localhost:6789) &
elif command -v open &>/dev/null; then
  (sleep 1.5 && open http://localhost:6789) &
fi

echo "  ⚡ Opening http://localhost:6789 in your browser..."
echo "  Complete setup there — no config files to edit."
echo ""
echo "  Press Ctrl+C to stop Daemon."
echo ""

python3 "$DAEMON_DIR/daemon.py" serve
