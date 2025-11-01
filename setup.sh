#!/bin/bash
trap "kill $SPIN_PID 2>/dev/null" EXIT

TARGET_HOME=$(eval echo ~$(logname))

# Spinner function
spin() {

  local msg="$1"
  local -a marks=( '-' '\' '|' '/' )
  while :; do
    for mark in "${marks[@]}"; do
      printf "\r\e[1;32m[+] $msg...\e[0m %s" "$mark"
      sleep 0.1
    done
  done
}

# Spinner starter (background-safe)
start_spinner() {
  spin "$1" &
  SPIN_PID=$!
}

# Spinner stopper (safe kill)
stop_spinner() {
  kill $SPIN_PID 2>/dev/null
  wait $SPIN_PID 2>/dev/null
  echo -e "\r\e[1;32m[✓] $1 complete! \e[0m"
}

# installing dependencies if not found on system
install_if_missing() {
        local pkg="$1"

        if ! dpkg -s $pkg >/dev/null 2>&1; then

                start_spinner "$pkg Installing..."
                sudo apt-get install $pkg -y > /dev/null 2>&1
                stop_spinner "$pkg Installation"

        else
                echo  -e "\e[33m$pkg Installation found...\e[0m"
        fi
}


start_spinner "System Updating"
sudo apt update > /dev/null 2>&1
stop_spinner "System Update"

install_if_missing python3
install_if_missing python3-pip
install_if_missing python3-venv

sudo python3 -m venv /opt/ExpoC
source /opt/ExpoC/bin/activate
cd /opt/ExpoC


if ! [[ -f "/opt/ExpoC/expoc.py" ]] ; then
  INSTALLER_PATH=$(find "$TARGET_HOME" -type d -name "ExpoC" -print -quit)
	sudo cp -r "$INSTALLER_PATH" "/opt/ExpoC"  # Copying Installer to /opt/ dir
fi


# installing python requirements
pip install requests colorama


# ExpoC Binary path
BIN_PATH="/usr/local/bin/expoc"

# Create launcher
echo ""
echo  -e "\e[34m[*] Creating launcher...\e[0m"
sudo tee "$BIN_PATH" > /dev/null <<'EOF'
#!/bin/bash

source /opt/ExpoC/bin/activate
cd /opt/ExpoC/

MODE="$1"
shift

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

	*)
	      python3 expoc.py "$@"
	      ;;

deactivate
EOF

# Make launcher executable
sudo chmod +x "$BIN_PATH"