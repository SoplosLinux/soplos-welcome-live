"""
Environment detection module for Soplos Welcome Live.
Handles desktop environment detection, display protocol identification,
edition detection (Tyron/Tyson/Boro), and system environment configuration.
"""

import os
import subprocess
import configparser
from pathlib import Path
from typing import Dict, Optional, Tuple
from enum import Enum


class DesktopEnvironment(Enum):
    """Supported desktop environments."""
    GNOME = "gnome"
    KDE = "kde"
    XFCE = "xfce"
    UNKNOWN = "unknown"


class DisplayProtocol(Enum):
    """Display server protocols."""
    X11 = "x11"
    WAYLAND = "wayland"
    UNKNOWN = "unknown"


class ThemeType(Enum):
    """System theme types."""
    LIGHT = "light"
    DARK = "dark"
    UNKNOWN = "unknown"


class SoplosEdition(Enum):
    """Soplos Linux editions."""
    TYRON = "tyron"       # XFCE edition
    TYSON = "tyson"       # KDE Plasma edition
    BORO = "boro"         # GNOME edition
    UNKNOWN = "unknown"


class EnvironmentDetector:
    """
    Detects and analyzes the current desktop environment, display protocol,
    Soplos edition, and system theme preferences.
    """
    
    # Edition to Desktop Environment mapping
    EDITION_DESKTOP_MAP = {
        SoplosEdition.TYRON: DesktopEnvironment.XFCE,
        SoplosEdition.TYSON: DesktopEnvironment.KDE,
        SoplosEdition.BORO: DesktopEnvironment.GNOME,
    }
    
    def __init__(self):
        self._desktop_env = None
        self._display_protocol = None
        self._theme_type = None
        self._edition = None
        self._environment_info = {}
        
    def detect_all(self) -> Dict[str, str]:
        """
        Performs complete environment detection.
        
        Returns:
            Dictionary with all detected environment information
        """
        self._detect_edition()
        self._detect_desktop_environment()
        self._detect_display_protocol()
        self._detect_theme_type()
        self._detect_additional_info()
        
        return {
            'edition': self._edition.value,
            'desktop_environment': self._desktop_env.value,
            'display_protocol': self._display_protocol.value,
            'theme_type': self._theme_type.value,
            'environment_info': self._environment_info
        }
    
    def _detect_edition(self) -> SoplosEdition:
        """Detects the Soplos Linux edition."""
        # Check for edition files
        edition_file = Path('/etc/soplos-edition')
        if edition_file.exists():
            try:
                content = edition_file.read_text().strip().lower()
                if 'tyron' in content:
                    self._edition = SoplosEdition.TYRON
                elif 'tyson' in content:
                    self._edition = SoplosEdition.TYSON
                elif 'boro' in content:
                    self._edition = SoplosEdition.BORO
                else:
                    self._edition = SoplosEdition.UNKNOWN
                return self._edition
            except Exception:
                pass
        
        # Fallback: detect from desktop environment
        desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
        
        if 'xfce' in desktop:
            self._edition = SoplosEdition.TYRON
        elif 'kde' in desktop or 'plasma' in desktop:
            self._edition = SoplosEdition.TYSON
        elif 'gnome' in desktop:
            self._edition = SoplosEdition.BORO
        else:
            # Check for specific processes
            self._edition = self._detect_edition_from_processes()
        
        return self._edition
    
    def _detect_edition_from_processes(self) -> SoplosEdition:
        """Detect edition by checking running processes."""
        try:
            # Check for XFCE
            result = subprocess.run(['pgrep', '-x', 'xfce4-session'], 
                                   capture_output=True, timeout=2)
            if result.returncode == 0:
                return SoplosEdition.TYRON
            
            # Check for KDE
            result = subprocess.run(['pgrep', '-x', 'plasmashell'], 
                                   capture_output=True, timeout=2)
            if result.returncode == 0:
                return SoplosEdition.TYSON
            
            # Check for GNOME
            result = subprocess.run(['pgrep', '-x', 'gnome-shell'], 
                                   capture_output=True, timeout=2)
            if result.returncode == 0:
                return SoplosEdition.BORO
                
        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            pass
        
        return SoplosEdition.UNKNOWN
    
    def _detect_desktop_environment(self) -> DesktopEnvironment:
        """Detects the current desktop environment."""
        # If edition is known, use the mapping
        if self._edition and self._edition != SoplosEdition.UNKNOWN:
            self._desktop_env = self.EDITION_DESKTOP_MAP.get(
                self._edition, DesktopEnvironment.UNKNOWN
            )
            return self._desktop_env
        
        # Check XDG_CURRENT_DESKTOP first (most reliable)
        current_desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
        
        if 'gnome' in current_desktop:
            self._desktop_env = DesktopEnvironment.GNOME
        elif 'kde' in current_desktop or 'plasma' in current_desktop:
            self._desktop_env = DesktopEnvironment.KDE
        elif 'xfce' in current_desktop:
            self._desktop_env = DesktopEnvironment.XFCE
        else:
            # Fallback detection methods
            self._desktop_env = self._fallback_desktop_detection()
        
        return self._desktop_env
    
    def _fallback_desktop_detection(self) -> DesktopEnvironment:
        """Fallback method for desktop environment detection."""
        # Check for environment variables
        if os.environ.get('GNOME_DESKTOP_SESSION_ID'):
            return DesktopEnvironment.GNOME
        elif os.environ.get('KDE_SESSION_VERSION'):
            return DesktopEnvironment.KDE
        elif os.environ.get('XFCE_PANEL_MIGRATE_DEFAULT'):
            return DesktopEnvironment.XFCE
        
        return DesktopEnvironment.UNKNOWN
    
    def _detect_display_protocol(self) -> DisplayProtocol:
        """Detects the display server protocol (X11 or Wayland)."""
        session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
        
        if session_type == 'wayland':
            self._display_protocol = DisplayProtocol.WAYLAND
        elif session_type == 'x11' or os.environ.get('DISPLAY'):
            self._display_protocol = DisplayProtocol.X11
        else:
            self._display_protocol = DisplayProtocol.UNKNOWN
            
        return self._display_protocol
    
    def _detect_theme_type(self) -> ThemeType:
        """Detects system theme preference (dark/light)."""
        try:
            if self._desktop_env == DesktopEnvironment.GNOME:
                self._theme_type = self._detect_gnome_theme()
            elif self._desktop_env == DesktopEnvironment.KDE:
                self._theme_type = self._detect_kde_theme()
            elif self._desktop_env == DesktopEnvironment.XFCE:
                self._theme_type = self._detect_xfce_theme()
            else:
                self._theme_type = ThemeType.UNKNOWN
        except Exception:
            self._theme_type = ThemeType.UNKNOWN
            
        return self._theme_type
    
    def _detect_gnome_theme(self) -> ThemeType:
        """Detects GNOME theme preference."""
        try:
            result = subprocess.run([
                'gsettings', 'get', 'org.gnome.desktop.interface', 'color-scheme'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                if 'dark' in result.stdout.lower():
                    return ThemeType.DARK
                elif 'light' in result.stdout.lower():
                    return ThemeType.LIGHT
        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            pass
        
        # Fallback: check GTK theme
        try:
            result = subprocess.run([
                'gsettings', 'get', 'org.gnome.desktop.interface', 'gtk-theme'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and 'dark' in result.stdout.lower():
                return ThemeType.DARK
        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            pass
            
        return ThemeType.LIGHT  # Default to light
    
    def _detect_kde_theme(self) -> ThemeType:
        """Detects KDE theme preference."""
        try:
            kde_config = Path.home() / '.config' / 'kdeglobals'
            if kde_config.exists():
                config = configparser.ConfigParser()
                config.read(kde_config)
                
                if 'General' in config:
                    color_scheme = config['General'].get('ColorScheme', '').lower()
                    if 'dark' in color_scheme or 'black' in color_scheme:
                        return ThemeType.DARK
        except Exception:
            pass
        
        # Check GTK3 settings
        try:
            gtk_config = Path.home() / '.config' / 'gtk-3.0' / 'settings.ini'
            if gtk_config.exists():
                config = configparser.ConfigParser()
                config.read(gtk_config)
                if 'Settings' in config:
                    prefer_dark = config['Settings'].get('gtk-application-prefer-dark-theme', '').lower()
                    if prefer_dark in ['1', 'true', 'yes']:
                        return ThemeType.DARK
        except Exception:
            pass
            
        return ThemeType.LIGHT  # Default to light
    
    def _detect_xfce_theme(self) -> ThemeType:
        """Detects XFCE theme preference."""
        try:
            result = subprocess.run([
                'xfconf-query', '-c', 'xsettings', '-p', '/Net/ThemeName'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and 'dark' in result.stdout.lower():
                return ThemeType.DARK
                
        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            pass
        
        return ThemeType.LIGHT  # Default to light
    
    def _detect_additional_info(self):
        """Collects additional environment information."""
        self._environment_info = {
            'desktop_session': os.environ.get('DESKTOP_SESSION', ''),
            'gdm_session': os.environ.get('GDMSESSION', ''),
            'window_manager': self._detect_window_manager(),
            'gtk_version': self._detect_gtk_version(),
            'is_live_session': self._detect_live_session(),
        }
    
    def _detect_window_manager(self) -> str:
        """Detects the current window manager."""
        try:
            result = subprocess.run(['wmctrl', '-m'], 
                                   capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('Name:'):
                        return line.split(':', 1)[1].strip()
        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            pass
        
        # Fallback based on desktop environment
        wm_map = {
            DesktopEnvironment.XFCE: 'xfwm4',
            DesktopEnvironment.KDE: 'kwin',
            DesktopEnvironment.GNOME: 'mutter',
        }
        return wm_map.get(self._desktop_env, 'unknown')
    
    def _detect_gtk_version(self) -> str:
        """Detects GTK version."""
        try:
            import gi
            gi.require_version('Gtk', '3.0')
            from gi.repository import Gtk
            return f"{Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}"
        except ImportError:
            return 'unknown'
    
    def _detect_live_session(self) -> bool:
        """Detects if running in a live session."""
        # Check for common live session indicators
        indicators = [
            Path('/run/live/medium'),
            Path('/run/live'),
            Path('/lib/live'),
            Path('/cdrom'),
        ]
        
        for indicator in indicators:
            if indicator.exists():
                return True
        
        # Check for live user
        if os.environ.get('USER') == 'live':
            return True
        
        # Check /etc/os-release for live indicator
        try:
            os_release = Path('/etc/os-release')
            if os_release.exists():
                content = os_release.read_text().lower()
                if 'live' in content:
                    return True
        except Exception:
            pass
        
        return False
    
    # Public properties for easy access
    @property
    def edition(self) -> SoplosEdition:
        """Current Soplos edition."""
        if self._edition is None:
            self._detect_edition()
        return self._edition
    
    @property
    def desktop_environment(self) -> DesktopEnvironment:
        """Current desktop environment."""
        if self._desktop_env is None:
            self._detect_desktop_environment()
        return self._desktop_env
    
    @property
    def display_protocol(self) -> DisplayProtocol:
        """Current display protocol."""
        if self._display_protocol is None:
            self._detect_display_protocol()
        return self._display_protocol
    
    @property
    def theme_type(self) -> ThemeType:
        """Current theme type."""
        if self._theme_type is None:
            self._detect_theme_type()
        return self._theme_type
    
    @property
    def is_wayland(self) -> bool:
        """True if running on Wayland."""
        return self.display_protocol == DisplayProtocol.WAYLAND
    
    @property
    def is_dark_theme(self) -> bool:
        """True if using dark theme."""
        return self.theme_type == ThemeType.DARK
    
    @property
    def is_live(self) -> bool:
        """True if running in live session."""
        if 'is_live_session' not in self._environment_info:
            self._environment_info['is_live_session'] = self._detect_live_session()
        return self._environment_info.get('is_live_session', True)
    
    def get_edition_name(self) -> str:
        """Returns the human-readable edition name."""
        edition_names = {
            SoplosEdition.TYRON: "Tyron (XFCE)",
            SoplosEdition.TYSON: "Tyson (KDE Plasma)",
            SoplosEdition.BORO: "Boro (GNOME)",
            SoplosEdition.UNKNOWN: "Unknown Edition",
        }
        return edition_names.get(self.edition, "Unknown")
    
    def configure_environment_variables(self):
        """
        Configures environment variables for optimal GTK integration
        based on the detected environment.
        """
        if self.is_wayland:
            os.environ['GTK_USE_PORTAL'] = '1'
            os.environ['GDK_BACKEND'] = 'wayland'
            
        if self.desktop_environment == DesktopEnvironment.KDE:
            if 'GTK_THEME' not in os.environ:
                theme_name = 'Breeze-Dark' if self.is_dark_theme else 'Breeze'
                os.environ['GTK_THEME'] = theme_name
        
        # Disable accessibility bus if not needed
        if not os.environ.get('ENABLE_ACCESSIBILITY'):
            os.environ['NO_AT_BRIDGE'] = '1'
            os.environ['AT_SPI_BUS'] = '0'


# Global instance for easy access
_environment_detector = None

def get_environment_detector() -> EnvironmentDetector:
    """
    Returns the global environment detector instance.
    Creates it if it doesn't exist.
    """
    global _environment_detector
    if _environment_detector is None:
        _environment_detector = EnvironmentDetector()
    return _environment_detector

def detect_environment() -> Dict[str, str]:
    """
    Convenience function to detect all environment information.
    
    Returns:
        Dictionary with complete environment detection results
    """
    detector = get_environment_detector()
    return detector.detect_all()
