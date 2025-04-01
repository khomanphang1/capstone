# README: Local Setup Guide for macOS Users

This guide helps you set up the SigFlow tool locally on a macOS machine.

---

## 1. Install Homebrew (if not already installed)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew --version
# Example output: Homebrew 4.4.27
```

---

## 2. Install Python 3.11.7

```bash
brew install python@3.11
python3.11 --version
# Expected output: Python 3.11.7
```

---

## 3. Install Virtual Environment & Git (if not already installed)

```bash
pip3 install virtualenv
brew install git
```

---

## 4. Clone the Repository

```bash
git clone <url>
cd <repo-name>
git remote -v
# Should display:
# origin	<url> (fetch)
# origin	<url>> (push)
```

---

## 5. Create and Activate Virtual Environment

```bash
python3.11 -m venv <destination_dir>

# Activate (bash/zsh):
source <destination_dir>/bin/activate

# Activate (c shell):
source <destination_dir>/bin/activate.csh
```

---

## 6. Install Python Dependencies

```bash
pip install -r <path_to_requirements.txt>
```

---

## 7. Install MongoDB Community Edition

```bash
brew install mongodb-community@7.0
```

---

## 8. Run Server Locally

```bash
# Activate virtual environment
source <destination_dir>/bin/activate

# Start MongoDB
brew services start mongodb/brew/mongodb-community

# Launch Flask server
python3.11 <path_to_server.py>
```

Landing page should now be available at:
**http://127.0.0.1:5000/app/landing.html**

---

## Automated Local Setup

### `local_server_start.zsh`

Note 1: This script is written for zsh (z-shell). If you’re using a different shell (e.g., bash, fish, or csh), you may need to adapt the script accordingly.

Note 2: You can customize the values of DEFAULT_VENV_PATH and DEFAULT_SERVER_PATH at the top of the script. Doing so allows you to run the script without needing to pass command-line arguments each time.
```zsh
Usage: ./local_server_start.zsh [options]

Options:
  -v, --venv-path <path>       Specify custom virtual environment activation path.
                              Default: UPDATE/DEFAULT/PATH
  -s, --server-path <path>     Specify custom server.py path.
                              Default: UPDATE/DEFAULT/PATH
  -h, --help                   Show this help menu and exit.
```

---

Update all placeholder paths (`<...>`) with actual values before using or distributing the scripts.

