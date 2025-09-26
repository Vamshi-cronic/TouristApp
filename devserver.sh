#!/bin/sh
# Use pgrep to reliably find and kill the existing server process
PIDS=$(pgrep -f "python main.py")
if [ ! -z "$PIDS" ]; then
  echo "Found old server processes with PIDs: $PIDS. Terminating with kill -9."
  kill -9 $PIDS
  sleep 2 # Give the OS a moment to release the port
fi

# Activate virtual environment and start the new server
echo "Starting Flask server..."
. .venv/bin/activate
export TZ=UTC
python main.py
