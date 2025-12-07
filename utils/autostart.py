"""
Autostart manager for Soplos Welcome Live.
Handles application autostart configuration in the user's session.
"""

import os
import shutil
from pathlib import Path
from typing import Optional


class AutostartManager:
    """
    Manages autostart configuration for Soplos Welcome Live.
    Creates/removes .desktop files in ~/.config/autostart/
    """
    
    DESKTOP_FILENAME = "org.soplos.welcomelive.desktop"
    
    def __init__(self):
        """Initialize the autostart manager."""
        self.autostart_dir = Path.home() / ".config" / "autostart"
        self.autostart_file = self.autostart_dir / self.DESKTOP_FILENAME
        
        # Source desktop file location
        self.source_desktop = Path(__file__).parent.parent / "assets" / self.DESKTOP_FILENAME
        
        # Alternative locations for the source desktop file
        self.system_desktop_locations = [
            Path("/usr/share/applications") / self.DESKTOP_FILENAME,
            Path("/usr/local/share/applications") / self.DESKTOP_FILENAME,
        ]
    
    def is_enabled(self) -> bool:
        """
        Check if autostart is enabled.
        
        Returns:
            True if autostart is enabled, False otherwise
        """
        if not self.autostart_file.exists():
            return False
        
        # Check if the file is not disabled (X-GNOME-Autostart-enabled=false)
        try:
            with open(self.autostart_file, 'r') as f:
                content = f.read()
                # If Hidden=true or X-GNOME-Autostart-enabled=false, it's disabled
                if 'Hidden=true' in content:
                    return False
                if 'X-GNOME-Autostart-enabled=false' in content:
                    return False
        except Exception:
            pass
        
        return True
    
    def enable(self) -> bool:
        """
        Enable autostart by creating the autostart desktop file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure autostart directory exists
            self.autostart_dir.mkdir(parents=True, exist_ok=True)
            
            # Find source desktop file
            source = self._find_source_desktop()
            
            if source and source.exists():
                # Copy the desktop file
                shutil.copy2(str(source), str(self.autostart_file))
            else:
                # Create a minimal desktop file
                self._create_desktop_file()
            
            # Ensure autostart is enabled in the file
            self._set_autostart_enabled(True)
            
            print(f"Autostart enabled: {self.autostart_file}")
            return True
            
        except Exception as e:
            print(f"Error enabling autostart: {e}")
            return False
    
    def disable(self) -> bool:
        """
        Disable autostart by removing or disabling the autostart file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.autostart_file.exists():
                # Option 1: Remove the file
                self.autostart_file.unlink()
                print(f"Autostart disabled: removed {self.autostart_file}")
            
            return True
            
        except Exception as e:
            print(f"Error disabling autostart: {e}")
            return False
    
    def toggle(self) -> bool:
        """
        Toggle autostart state.
        
        Returns:
            New state (True = enabled, False = disabled)
        """
        if self.is_enabled():
            self.disable()
            return False
        else:
            self.enable()
            return True
    
    def _find_source_desktop(self) -> Optional[Path]:
        """Find the source desktop file."""
        # First try the bundled one
        if self.source_desktop.exists():
            return self.source_desktop
        
        # Try system locations
        for location in self.system_desktop_locations:
            if location.exists():
                return location
        
        return None
    
    def _create_desktop_file(self):
        """Create a minimal desktop file for autostart."""
        desktop_content = """[Desktop Entry]
Type=Application
Name=Soplos Welcome Live
Comment=Welcome application for Soplos Linux Live ISO
Exec=soplos-welcome-live
Icon=org.soplos.welcomelive
Terminal=false
Categories=System;Utility;
StartupNotify=false
X-GNOME-Autostart-enabled=true
"""
        with open(self.autostart_file, 'w') as f:
            f.write(desktop_content)
    
    def _set_autostart_enabled(self, enabled: bool):
        """Set the autostart enabled flag in the desktop file."""
        if not self.autostart_file.exists():
            return
        
        try:
            with open(self.autostart_file, 'r') as f:
                content = f.read()
            
            # Update or add X-GNOME-Autostart-enabled
            value = 'true' if enabled else 'false'
            
            if 'X-GNOME-Autostart-enabled=' in content:
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith('X-GNOME-Autostart-enabled='):
                        lines[i] = f'X-GNOME-Autostart-enabled={value}'
                content = '\n'.join(lines)
            else:
                content = content.rstrip() + f'\nX-GNOME-Autostart-enabled={value}\n'
            
            # Remove Hidden=true if enabling
            if enabled and 'Hidden=true' in content:
                content = content.replace('Hidden=true', 'Hidden=false')
            
            with open(self.autostart_file, 'w') as f:
                f.write(content)
                
        except Exception as e:
            print(f"Error updating autostart file: {e}")
