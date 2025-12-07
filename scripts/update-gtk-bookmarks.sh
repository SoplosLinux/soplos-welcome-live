#!/bin/bash
#
# update-gtk-bookmarks.sh
# Updates GTK bookmarks based on XDG directories after installation
# 
# This script is intended to be run by Calamares as a shellprocess
# It updates ~/.config/gtk-3.0/bookmarks for GNOME/Nautilus users
#
# Installation:
#   Copy to /usr/share/soplos/update-gtk-bookmarks.sh
#   chmod +x /usr/share/soplos/update-gtk-bookmarks.sh
#
# Calamares integration:
#   Add to shellprocess.conf:
#   script:
#     - "/usr/share/soplos/update-gtk-bookmarks.sh"
#

# CRITICAL: Do NOT run on XFCE (Tyron)
if [ -f "/usr/bin/xfce4-session" ]; then
    echo "XFCE detected. Skipping GTK bookmark update."
    exit 0
fi

# Get home directory (works in chroot context)
if [ -n "$USER" ]; then
    HOME_DIR="/home/$USER"
elif [ -d "/home/liveuser" ]; then
    HOME_DIR="/home/liveuser"
else
    # Find first non-root user
    HOME_DIR=$(getent passwd 1000 | cut -d: -f6)
fi

# Exit if no home directory found
if [ ! -d "$HOME_DIR" ]; then
    echo "No home directory found, skipping bookmark update"
    exit 0
fi

# Paths
USER_DIRS_FILE="$HOME_DIR/.config/user-dirs.dirs"
# Create config directories if needed
# Create config directories if needed
mkdir -p "$HOME_DIR/.config/gtk-3.0"

# Target files
GTK3_BOOKMARKS="$HOME_DIR/.config/gtk-3.0/bookmarks"

# Read XDG directories and create bookmarks
echo "Updating GTK bookmarks from XDG directories..."

# Helper function to update a bookmark file
update_bookmark_file() {
    local target_file="$1"
    
    # Clear old XDG bookmarks but preserve custom ones if possible (simplified here for install time)
    : > "$target_file"
    
    for key in $XDG_KEYS; do
        # Extract value from user-dirs.dirs
        value=$(grep "^$key=" "$USER_DIRS_FILE" | cut -d= -f2 | tr -d '"')
        
        # Replace $HOME with actual path
        value=$(echo "$value" | sed "s|\$HOME|$HOME_DIR|g")
        
        if [ -n "$value" ] && [ -d "$value" ]; then
            echo "file://$value" >> "$target_file"
        fi
    done
    echo "Updated $target_file"
}

# Update both
update_bookmark_file "$GTK3_BOOKMARKS"

echo "GTK bookmarks updated successfully"

# Fix ownership if running as root (typical in Calamares chroot)
if [ "$(id -u)" = "0" ]; then
    # Get the actual user who owns the home directory
    ACTUAL_USER=$(stat -c '%U' "$HOME_DIR")
    ACTUAL_GROUP=$(stat -c '%G' "$HOME_DIR")
    
    chown -R "$ACTUAL_USER:$ACTUAL_GROUP" "$HOME_DIR/.config/gtk-3.0" 2>/dev/null
    echo "Fixed ownership for $ACTUAL_USER"
fi

exit 0
