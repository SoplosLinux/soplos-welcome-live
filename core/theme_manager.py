"""
Theme management system for Soplos Welcome Live.
Handles CSS theme loading, application, and dynamic theme switching.
"""

import os
from pathlib import Path
from typing import Dict, Optional, List
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

from .environment import get_environment_detector, DesktopEnvironment, ThemeType


class ThemeManager:
    """
    Manages CSS themes for the application with automatic detection
    and desktop environment integration.
    """
    
    def __init__(self, assets_path: str):
        """
        Initialize the theme manager.
        
        Args:
            assets_path: Path to the assets directory containing themes
        """
        self.assets_path = Path(assets_path)
        self.themes_path = self.assets_path / 'themes'
        self.css_provider = None
        self.current_theme = None
        self.environment_detector = get_environment_detector()
        
        # Ensure themes directory exists
        self.themes_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize CSS provider
        self._init_css_provider()
    
    def _init_css_provider(self):
        """Initialize the GTK CSS provider."""
        self.css_provider = Gtk.CssProvider()
        
        # Add to default screen
        screen = Gdk.Screen.get_default()
        if screen:
            Gtk.StyleContext.add_provider_for_screen(
                screen, 
                self.css_provider, 
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
    
    def get_available_themes(self) -> List[str]:
        """
        Get list of available theme names.
        
        Returns:
            List of theme names (without .css extension)
        """
        if not self.themes_path.exists():
            return []
        
        themes = []
        for theme_file in self.themes_path.glob('*.css'):
            themes.append(theme_file.stem)
        
        return sorted(themes)
    
    def detect_optimal_theme(self) -> str:
        """
        Detects the optimal theme based on the current environment.
        
        Returns:
            Theme name that best matches the current environment
        """
        env_info = self.environment_detector.detect_all()
        desktop_env = env_info['desktop_environment']
        theme_type = env_info['theme_type']
        
        # Priority order for theme selection
        theme_candidates = []
        
        # 1. Desktop-specific theme with light/dark variant
        if desktop_env != 'unknown':
            theme_candidates.append(f"{desktop_env}-{theme_type}")
            theme_candidates.append(f"{desktop_env}")
        
        # 2. Generic light/dark theme
        theme_candidates.append(theme_type)
        
        # 3. Base theme
        theme_candidates.append('base')
        
        # 4. Fallback themes
        theme_candidates.extend(['light', 'dark', 'default'])
        
        # Find the first available theme
        available_themes = self.get_available_themes()
        
        for theme in theme_candidates:
            if theme in available_themes:
                return theme
        
        # Return base if nothing found
        return 'base'
    
    def load_theme(self, theme_name: str) -> bool:
        """
        Load and apply a theme by name.
        
        Args:
            theme_name: Name of the theme to load
            
        Returns:
            True if theme loaded successfully, False otherwise
        """
        theme_path = self.themes_path / f"{theme_name}.css"
        
        if not theme_path.exists():
            print(f"Theme file not found: {theme_path}")
            return False
        
        try:
            # Load CSS file
            self.css_provider.load_from_path(str(theme_path))
            self.current_theme = theme_name
            print(f"Theme '{theme_name}' loaded successfully")
            return True
            
        except Exception as e:
            print(f"Error loading theme '{theme_name}': {e}")
            return False
    
    def load_theme_from_string(self, css_string: str) -> bool:
        """
        Load theme from a CSS string.
        
        Args:
            css_string: CSS content as string
            
        Returns:
            True if loaded successfully
        """
        try:
            self.css_provider.load_from_data(css_string.encode())
            return True
        except Exception as e:
            print(f"Error loading CSS from string: {e}")
            return False
    
    def get_current_theme(self) -> Optional[str]:
        """Get the name of the currently loaded theme."""
        return self.current_theme
    
    def reload_theme(self) -> bool:
        """Reload the current theme."""
        if self.current_theme:
            return self.load_theme(self.current_theme)
        return False
    
    def toggle_dark_mode(self) -> str:
        """
        Toggle between light and dark themes.
        
        Returns:
            Name of the newly applied theme
        """
        current = self.current_theme or 'light'
        
        if 'dark' in current:
            new_theme = current.replace('dark', 'light')
        else:
            new_theme = current.replace('light', 'dark')
        
        # Check if the new theme exists
        if new_theme not in self.get_available_themes():
            new_theme = 'dark' if 'light' in current else 'light'
        
        self.load_theme(new_theme)
        return new_theme


# Global singleton instance
_theme_manager = None


def get_theme_manager() -> Optional[ThemeManager]:
    """Get the global theme manager instance."""
    return _theme_manager


def initialize_theming(assets_path: str) -> ThemeManager:
    """
    Initialize the global theme manager.
    
    Args:
        assets_path: Path to assets directory
        
    Returns:
        The initialized ThemeManager instance
    """
    global _theme_manager
    _theme_manager = ThemeManager(assets_path)
    return _theme_manager
