#!/bin/bash
# open_vlc.sh
# Accept a local file path or URL and open in VLC
file="$1"
if [ -z "$file" ]; then
    echo "Usage: $0 /path/to/video"
    exit 1
fi
vlc "$file"
