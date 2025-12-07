#!/usr/bin/env python3
"""
GTK Bookmarks Updater for GNOME/Nautilus.
Updates ~/.config/gtk-3.0/bookmarks based on current XDG user directories.

This script reads the current XDG directories from ~/.config/user-dirs.dirs
and updates the GTK bookmarks file to point to the correct locations.

Usage:
    python3 update_gtk_bookmarks.py
    
For Calamares integration, this can be called as a shellprocess module.
"""

import os
from pathlib import Path


def get_xdg_directories() -> dict:
    """Read current XDG directories from user-dirs.dirs."""
    xdg_dirs = {}
    user_dirs_file = Path.home() / ".config" / "user-dirs.dirs"
    
    if not user_dirs_file.exists():
        return xdg_dirs
    
    with open(user_dirs_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') or '=' not in line:
                continue
            
            key, value = line.split('=', 1)
            # Remove quotes and expand $HOME
            value = value.strip('"').replace('$HOME', str(Path.home()))
            xdg_dirs[key] = value
    
    return xdg_dirs


def update_gtk_bookmarks():
    """
    Update GTK bookmarks to match current XDG directories.
    Handles both GTK 3.0 (standard) and GTK 4.0 (newer GNOME/XFCE).
    """
    home = Path.home()
    
    # Target files to update
    targets = [
        home / ".config" / "gtk-3.0" / "bookmarks",
        home / ".config" / "gtk-4.0" / "bookmarks"
    ]
    
    # Get current XDG directories
    xdg_dirs = get_xdg_directories()
    
    if not xdg_dirs:
        print("No XDG directories found, skipping bookmark update")
        return False
    
    # Standard XDG directory mappings for bookmarks
    bookmark_order = [
        'XDG_DOCUMENTS_DIR',
        'XDG_DOWNLOAD_DIR',
        'XDG_MUSIC_DIR',
        'XDG_PICTURES_DIR',
        'XDG_VIDEOS_DIR',
    ]
    
    # Build new bookmarks content
    new_bookmarks = []
    for xdg_key in bookmark_order:
        if xdg_key in xdg_dirs:
            path = xdg_dirs[xdg_key]
            # Ensure directory exists
            Path(path).mkdir(parents=True, exist_ok=True)
            new_bookmarks.append(f"file://{path}")
    
    # Process each target file
    for bookmarks_file in targets:
        # Ensure parent directory exists
        bookmarks_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Read existing bookmarks to preserve custom ones
        custom_bookmarks = []
        if bookmarks_file.exists():
            try:
                with open(bookmarks_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if not line: continue
                        
                        # Check if it's a custom bookmark
                        is_xdg = False
                        for path in xdg_dirs.values():
                            if f"file://{path}" in line:
                                is_xdg = True
                                break
                        if not is_xdg:
                            # Verify if path exists
                            uri = line.split()[0] if line else ""
                            if uri.startswith("file://"):
                                local_path = uri.replace("file://", "")
                                path_obj = Path(local_path)
                                
                                # HARDCORE FIX: Filter out old English XDG paths to prevent duplicates
                                # If the folder name is one of the standard English ones, we assume it's an old system folder
                                # and we DO NOT preserve it as a custom bookmark.
                                english_xdg_names = [
                                    "Documents", "Downloads", "Music", "Pictures", "Videos", 
                                    "Desktop", "Public", "Templates"
                                ]
                                
                                is_legacy_xdg = False
                                # Check if it is a standard folder in the home root
                                if path_obj.parent == home and path_obj.name in english_xdg_names:
                                    is_legacy_xdg = True
                                
                                # Also filter out the home directory itself (redundant in Thunar)
                                is_home_dir = (path_obj == home)
                                
                                if path_obj.exists() and not is_legacy_xdg and not is_home_dir:
                                    custom_bookmarks.append(line)
            except Exception as e:
                print(f"Error reading {bookmarks_file}: {e}")

        # Combine and write
        all_bookmarks = new_bookmarks + custom_bookmarks
        try:
            with open(bookmarks_file, 'w') as f:
                for bookmark in all_bookmarks:
                    f.write(bookmark + '\n')
            print(f"Updated {bookmarks_file}")
        except Exception as e:
            print(f"Error writing {bookmarks_file}: {e}")

    return True


def reload_file_managers():
    """Reload file managers (Nautilus, Thunar) to refresh bookmarks."""
    import subprocess
    
    # Nautilus (GNOME)
    try:
        subprocess.run(['nautilus', '-q'], check=False, timeout=5)
    except: pass
    
    # Thunar (XFCE)
    try:
        if subprocess.run(['pgrep', 'Thunar'], stdout=subprocess.DEVNULL).returncode == 0:
            subprocess.run(['thunar', '-q'], check=False, timeout=5)
            print("Thunar reloaded")
    except: pass


def main():
    """Main entry point."""
    print("Updating GTK bookmarks...")
    
    success = update_gtk_bookmarks()
    
    if success:
        # Reload file managers
        reload_file_managers()
        print("Bookmarks updated successfully")
    else:
        print("Failed to update bookmarks")
    
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
