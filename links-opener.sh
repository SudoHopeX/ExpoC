#!/bin/bash

# SudoHopeX
# ExpoC v0.2
# Expoc Tool: Opens Multiple URLs from a file in Firefox tabs

# Function to open URLs in Firefox
open_urls() {
    local url="$1"
    # Open a URL in a new tab
    firefox --new-tab "$url" >/dev/null 2>&1 &
}

# Function to read URLs from file and open them one by one
get_urls_from_file_n_open_1_by_1() {
    local file="$1"
    local count=0

    # Count number of URLs (non-empty lines)
    count=$(grep -c '^[^[:space:]]' "$file")
    echo "Found $count URLs in '$file'. Opening in Firefox..."

    # Read each line and open in a new tab
    while IFS= read -r line; do
        # Skip empty lines and comments
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
        # echo "Opening: $line"
        open_urls "$line"
        sleep 1  # Slight delay to ensure Firefox handles each tab
    done < "$file"

    echo "All URLs opened."
}

# Main script execution
# if [[ $# -eq 0 ]]; then
#     echo "Usage: $0 <filename>"
#     echo "Example: $0 urls.txt"
#     exit 1
# fi

# Check if file exists and is readable
if [[ ! -f "$1" || ! -r "$1" ]]; then
    echo "[!] Error: File '$1' not found or not readable."
    exit 1
fi


# Call the function to process the file
get_urls_from_file_n_open_1_by_1 "$1" 
