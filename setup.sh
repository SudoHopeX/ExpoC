#!/bin/bash
trap 'kill $SPIN_PID 2>/dev/null' EXIT

# Get home directory safely
TARGET_HOME=$(getent passwd $(logname) | cut -d: -f6)

# Define color variables
RED='\e[1;31m'
GREEN='\e[1;32m'
YELLOW='\e[1;33m'
BLUE='\e[1;34m'
CYAN='\e[1;36m'
RESET='\e[0m'  # Reset to default


# Spinner function
spin() {
    [[ -t 1 ]] || return 0  # Only spin if terminal
    local msg="$1"
    local -a marks=( '-' '\' '|' '/' )
    while :; do
        for mark in "${marks[@]}"; do
            printf "\r${GREEN}[+] $msg...${RESET} %s" "$mark"
            sleep 0.1
        done
    done
}

# Spinner starter (background-safe)
start_spinner() {
    stop_spinner 2>/dev/null  # Ensure no previous spinner
    spin "$1" &
    SPIN_PID=$!
    # Validate process exists
    kill -0 $SPIN_PID 2>/dev/null || unset SPIN_PID
}

# Spinner stopper (safe kill)
stop_spinner() {
    if [[ -n "$SPIN_PID" ]]; then
        kill $SPIN_PID 2>/dev/null
        wait $SPIN_PID 2>/dev/null
    fi
    printf '\r\e[K'  # Clear entire line
    echo -e "${GREEN}[✓] $1 complete! ${RESET}"
}


# installing dependencies if not found on system
install_if_missing() {
        local pkg="$1"

        if ! dpkg -s $pkg >/dev/null 2>&1; then

                start_spinner "$pkg Installing..."
                sudo apt-get install $pkg -y > /dev/null 2>&1
                stop_spinner "$pkg Installation"

        else
                echo  -e "${YELLOW}$pkg Installation found...${RESET}"
        fi
}


start_spinner "System Updating"
if ! sudo apt update > /dev/null 2>&1; then
    echo -e "${RED}[!] Failed to update package list${RESET}" >&2
    exit 1
fi
stop_spinner "System Update"

install_if_missing python3
install_if_missing python3-pip
install_if_missing python3-venv

sudo python3 -m venv /opt/ExpoC
source /opt/ExpoC/bin/activate
cd /opt/ExpoC


INSTALLER_PATH=$(find "$TARGET_HOME" -type d -name "ExpoC" -print -quit)

if [[ ! -f "$INSTALLER_PATH"/expoc.py ]]; then
    echo -e "${RED}[!] ExpoC source not found!${RESET}" >&2
    exit 1
fi

if ! [[ -f "/opt/ExpoC/expoc.py" ]] ; then
	sudo rsync -av "$INSTALLER_PATH/" "/opt/ExpoC/"
fi


# installing python requirements
start_spinner "Installing python Requirements.."
if ! pip install requests colorama > /dev/null 2>&1; then
    stop_spinner "Python requirements"
    echo -e "${RED}[!] Python requirements installation failed!${RESET}"
    exit 1
fi
stop_spinner "Python requirements"


# ExpoC Binary path
BIN_PATH="/usr/local/bin/expoc"

# Create launcher
echo ""
echo  -e "${CYAN}[*] Creating launcher...${RESET}"
sudo tee "$BIN_PATH" > /dev/null <<'EOF'
#!/bin/bash

source /opt/ExpoC/bin/activate
cd /opt/ExpoC/

MODE="$1"

case "$MODE" in
	--update|-u)
        echo "[*] Checking for updates..."
        git fetch origin
        LOCAL=$(git rev-parse HEAD)
        REMOTE=$(git rev-parse origin/main)

        if [ "$LOCAL" != "$REMOTE" ]; then
            echo "[*] Update available. Pulling latest changes..."
            git pull origin main
            echo "[✓] Updated successfully!"

        else
            echo "[✓] Already up to date."
        fi
        ;;
  # --fetch|f)
  #       fetch_n_check_files_4_info.py "$@"
  #       ;;
	*)
	      python3 ExpoC/expoc.py "$@"
	      ;;

esac

deactivate
EOF

# Make launcher executable
sudo chmod +x "$BIN_PATH"


echo -e "${BLUE} ExpoC Installation Succeed, COMMAND: ${YELLOW}expoc -h${RESET}"
