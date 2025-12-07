"""
Path configuration for Soplos Welcome Live.
Centralized path management for all application resources.
"""

import os
from pathlib import Path

# Base directory is the directory containing this file's parent
BASE_DIR = Path(__file__).parent.parent

# Main directories
ASSETS_DIR = BASE_DIR / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
THEMES_DIR = ASSETS_DIR / "themes"
SLIDES_DIR = ASSETS_DIR / "slides"
SCREENSHOTS_DIR = ASSETS_DIR / "screenshots"

LOCALE_DIR = BASE_DIR / "locale"
CONFIG_DIR = BASE_DIR / "config"
UI_DIR = BASE_DIR / "ui"
UTILS_DIR = BASE_DIR / "utils"
CORE_DIR = BASE_DIR / "core"
SCRIPTS_DIR = BASE_DIR / "scripts"

# Icon paths
LOGO_PATH = ICONS_DIR / "org.soplos.welcomelive.png"
ICON_PATH = ICONS_DIR / "org.soplos.welcomelive.png"

# Icon size directories
ICONS_48 = ICONS_DIR / "48x48"
ICONS_64 = ICONS_DIR / "64x64"
ICONS_128 = ICONS_DIR / "128x128"

# Slide path for welcome screen
SLIDE_PATH = SLIDES_DIR / "slide1.png"

# Desktop file path
DESKTOP_FILE = ASSETS_DIR / "org.soplos.welcomelive.desktop"


def get_icon_path(icon_name: str, size: int = 64) -> Path:
    """
    Get the path to an icon file.
    
    Args:
        icon_name: Name of the icon (without extension)
        size: Icon size (48, 64, or 128)
        
    Returns:
        Path to the icon file
    """
    size_dirs = {48: ICONS_48, 64: ICONS_64, 128: ICONS_128}
    icon_dir = size_dirs.get(size, ICONS_64)
    
    # Try PNG first, then SVG
    for ext in ['.png', '.svg']:
        icon_path = icon_dir / f"{icon_name}{ext}"
        if icon_path.exists():
            return icon_path
    
    # Fallback to main icons directory
    for ext in ['.png', '.svg']:
        icon_path = ICONS_DIR / f"{icon_name}{ext}"
        if icon_path.exists():
            return icon_path
    
    return ICONS_DIR / f"{icon_name}.png"


def get_slide_path(slide_number: int = 1) -> Path:
    """
    Get the path to a slide image.
    
    Args:
        slide_number: Slide number (1-based)
        
    Returns:
        Path to the slide image
    """
    return SLIDES_DIR / f"slide{slide_number}.png"


def get_theme_path(theme_name: str) -> Path:
    """
    Get the path to a theme CSS file.
    
    Args:
        theme_name: Name of the theme (without extension)
        
    Returns:
        Path to the theme CSS file
    """
    return THEMES_DIR / f"{theme_name}.css"


def ensure_directories():
    """Create all necessary directories if they don't exist."""
    directories = [
        ASSETS_DIR,
        ICONS_DIR,
        ICONS_48,
        ICONS_64,
        ICONS_128,
        THEMES_DIR,
        SLIDES_DIR,
        SCREENSHOTS_DIR,
        LOCALE_DIR,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


# Ensure directories exist on import
ensure_directories()
