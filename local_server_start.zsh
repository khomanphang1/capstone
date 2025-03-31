#!/bin/zsh

# Default paths
DEFAULT_VENV_PATH="UPDATE/DEFAULT/PATH"
DEFAULT_SERVER_PATH="UPDATE/DEFAULT/PATH"

# Function to display help menu
show_help() {
    echo "Usage: ./local_server_start.zsh [options]"
    echo ""
    echo "Options:"
    echo "  -v, --venv-path <path>       Specify custom virtual environment activation path."
    echo "                              Default: $DEFAULT_VENV_PATH"
    echo "  -s, --server-path <path>     Specify custom server.py path."
    echo "                              Default: $DEFAULT_SERVER_PATH"
    echo "  -h, --help                   Show this help menu and exit."
}

# Parse command-line options
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -v|--venv-path) VENV_PATH="$2"; shift ;;
        -s|--server-path) SERVER_PATH="$2"; shift ;;
        -h|--help) show_help; exit 0 ;;
        *) echo "Unknown parameter passed: $1"; show_help; exit 1 ;;
    esac
    shift
done

# Set paths to defaults if not provided
VENV_PATH="${VENV_PATH:-$DEFAULT_VENV_PATH}"
SERVER_PATH="${SERVER_PATH:-$DEFAULT_SERVER_PATH}"

# Start the script
echo "Using virtual environment: $VENV_PATH"
echo "Using server script: $SERVER_PATH"

# Activate virtual environment
if [[ -f "$VENV_PATH" ]]; then
    source "$VENV_PATH"
else
    echo "Error: Virtual environment activation script not found at $VENV_PATH"
    exit 1
fi

# Start MongoDB
echo "Starting MongoDB..."
brew services start mongodb/brew/mongodb-community

# Launch the server
echo "Launching server script: $SERVER_PATH"
if [[ -f "$SERVER_PATH" ]]; then
    python3.11 "$SERVER_PATH"
else
    echo "Error: Server script not found at $SERVER_PATH"
    exit 1
fi