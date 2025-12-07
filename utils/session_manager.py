"""
Session manager for Soplos Welcome Live.
Handles session restart, logout, and desktop-specific session operations.
"""

import os
import subprocess
import time
from pathlib import Path
from typing import Optional, Tuple
from enum import Enum

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.environment import get_environment_detector, DesktopEnvironment


class SessionAction(Enum):
    """Session actions."""
    LOGOUT = "logout"
    RESTART = "restart"
    SHUTDOWN = "shutdown"


class SessionManager:
    """
    Manages desktop session operations.
    Provides desktop-specific logout, restart, and session refresh functionality.
    """
    
    def __init__(self):
        """Initialize the session manager."""
        self.env_detector = get_environment_detector()
        self.env_detector.detect_all()
        
        self.desktop = self.env_detector.desktop_environment
        self.edition = self.env_detector.get_edition_name()
    
    def logout(self, save_session: bool = False) -> Tuple[bool, str]:
        """
        Log out of the current session.
        
        Args:
            save_session: Whether to save the session state
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if self.desktop == DesktopEnvironment.XFCE:
                return self._logout_xfce(save_session)
            elif self.desktop == DesktopEnvironment.KDE:
                return self._logout_kde(save_session)
            elif self.desktop == DesktopEnvironment.GNOME:
                return self._logout_gnome(save_session)
            else:
                return self._logout_generic()
        except Exception as e:
            return (False, f"Logout failed: {e}")
    
    def restart_session(self) -> Tuple[bool, str]:
        """
        Restart the current desktop session.
        
        Returns:
            Tuple of (success, message)
        """
        # Most desktops don't support true "restart", so we logout
        return self.logout()
    
    def refresh_desktop(self) -> Tuple[bool, str]:
        """
        Refresh the desktop without logging out.
        Useful for applying some settings without full logout.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            if self.desktop == DesktopEnvironment.XFCE:
                return self._refresh_xfce()
            elif self.desktop == DesktopEnvironment.KDE:
                return self._refresh_kde()
            elif self.desktop == DesktopEnvironment.GNOME:
                return self._refresh_gnome()
            else:
                return (False, "Desktop refresh not supported for this environment")
        except Exception as e:
            return (False, f"Desktop refresh failed: {e}")
    
    def _logout_xfce(self, save_session: bool = False) -> Tuple[bool, str]:
        """Logout from XFCE session."""
        try:
            # Try xfce4-session-logout
            cmd = ['xfce4-session-logout', '--logout']
            if not save_session:
                cmd.append('--fast')
            
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            if result.returncode == 0:
                return (True, "Logging out of XFCE session...")
            
            # Fallback to xfce4-session-logout without --fast
            result = subprocess.run(['xfce4-session-logout', '--logout'], 
                                   capture_output=True, timeout=10)
            if result.returncode == 0:
                return (True, "Logging out of XFCE session...")
            
            # Last resort: kill session
            return self._logout_generic()
            
        except subprocess.TimeoutExpired:
            return (True, "Logout initiated...")
        except Exception as e:
            return (False, f"XFCE logout failed: {e}")
    
    def _logout_kde(self, save_session: bool = False) -> Tuple[bool, str]:
        """Logout from KDE Plasma session."""
        try:
            # Try qdbus for Plasma
            cmd = ['qdbus', 'org.kde.ksmserver', '/KSMServer', 'logout', 
                   '0',  # Confirm immediately
                   '0',  # Logout (not shutdown)
                   '0']  # Default
            
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            if result.returncode == 0:
                return (True, "Logging out of KDE Plasma session...")
            
            # Try qdbus6 for Plasma 6
            cmd[0] = 'qdbus6'
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            if result.returncode == 0:
                return (True, "Logging out of KDE Plasma session...")
            
            # Fallback to loginctl
            result = subprocess.run(['loginctl', 'terminate-user', os.environ.get('USER', '')],
                                   capture_output=True, timeout=10)
            if result.returncode == 0:
                return (True, "Session terminated...")
            
            return self._logout_generic()
            
        except subprocess.TimeoutExpired:
            return (True, "Logout initiated...")
        except Exception as e:
            return (False, f"KDE logout failed: {e}")
    
    def _logout_gnome(self, save_session: bool = False) -> Tuple[bool, str]:
        """Logout from GNOME session."""
        try:
            # Try gnome-session-quit
            cmd = ['gnome-session-quit', '--logout']
            if not save_session:
                cmd.append('--no-prompt')
            
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            if result.returncode == 0:
                return (True, "Logging out of GNOME session...")
            
            # Try via DBus
            cmd = ['dbus-send', '--session', '--type=method_call',
                   '--dest=org.gnome.SessionManager',
                   '/org/gnome/SessionManager',
                   'org.gnome.SessionManager.Logout',
                   'uint32:1']  # Logout without confirmation
            
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            if result.returncode == 0:
                return (True, "Logging out of GNOME session...")
            
            return self._logout_generic()
            
        except subprocess.TimeoutExpired:
            return (True, "Logout initiated...")
        except Exception as e:
            return (False, f"GNOME logout failed: {e}")
    
    def _logout_generic(self) -> Tuple[bool, str]:
        """Generic logout using loginctl or pkill."""
        try:
            # Try loginctl first
            user = os.environ.get('USER', '')
            if user:
                result = subprocess.run(['loginctl', 'terminate-user', user],
                                       capture_output=True, timeout=10)
                if result.returncode == 0:
                    return (True, "Session terminated...")
            
            # Last resort: kill the session leader
            # This is aggressive but works
            return (False, "Could not logout gracefully. Please logout manually.")
            
        except Exception as e:
            return (False, f"Generic logout failed: {e}")
    
    def _refresh_xfce(self) -> Tuple[bool, str]:
        """Refresh XFCE desktop."""
        try:
            # Restart xfce4-panel
            subprocess.run(['xfce4-panel', '-r'], capture_output=True, timeout=10)
            
            # Restart xfdesktop
            subprocess.Popen(['xfdesktop', '--reload'], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            return (True, "XFCE desktop refreshed")
        except Exception as e:
            return (False, f"XFCE refresh failed: {e}")
    
    def _refresh_kde(self) -> Tuple[bool, str]:
        """Refresh KDE Plasma desktop."""
        try:
            # Reload plasma shell
            subprocess.run(['kquitapp5', 'plasmashell'], capture_output=True, timeout=10)
            time.sleep(1)
            subprocess.Popen(['kstart5', 'plasmashell'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            return (True, "KDE Plasma shell restarted")
        except Exception as e:
            return (False, f"KDE refresh failed: {e}")
    
    def _refresh_gnome(self) -> Tuple[bool, str]:
        """Refresh GNOME desktop."""
        try:
            # Restart GNOME Shell (only works on X11)
            if os.environ.get('XDG_SESSION_TYPE') == 'x11':
                subprocess.run(['busctl', '--user', 'call', 
                              'org.gnome.Shell', '/org/gnome/Shell',
                              'org.gnome.Shell', 'Eval', 's',
                              'global.reexec_self()'],
                             capture_output=True, timeout=10)
                return (True, "GNOME Shell restarted")
            else:
                return (False, "GNOME Shell restart not supported on Wayland")
        except Exception as e:
            return (False, f"GNOME refresh failed: {e}")
    
    def schedule_restart_after_app_close(self, delay_seconds: int = 1) -> bool:
        """
        Schedule a session restart after the application closes.
        
        Args:
            delay_seconds: Delay before restarting
            
        Returns:
            True if scheduled successfully
        """
        try:
            # Create a script that will logout after delay
            script_content = f"""#!/bin/bash
sleep {delay_seconds}
"""
            if self.desktop == DesktopEnvironment.XFCE:
                script_content += "xfce4-session-logout --logout --fast\n"
            elif self.desktop == DesktopEnvironment.KDE:
                script_content += "qdbus org.kde.ksmserver /KSMServer logout 0 0 0\n"
            elif self.desktop == DesktopEnvironment.GNOME:
                script_content += "gnome-session-quit --logout --no-prompt\n"
            
            # Write and execute the script in background
            script_path = Path("/tmp/soplos-welcome-live-restart.sh")
            with open(script_path, 'w') as f:
                f.write(script_content)
            os.chmod(script_path, 0o755)
            
            subprocess.Popen(['bash', str(script_path)],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL,
                           start_new_session=True)
            
            return True
        except Exception as e:
            print(f"Failed to schedule restart: {e}")
            return False


# Global singleton
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get or create the global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
