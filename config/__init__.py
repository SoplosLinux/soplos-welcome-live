"""
Configuration module for Soplos Welcome Live.
Contains path configuration and application settings.
"""

from .paths import *

__all__ = [
    'BASE_DIR',
    'ASSETS_DIR',
    'ICONS_DIR',
    'THEMES_DIR',
    'SLIDES_DIR',
    'LOCALE_DIR',
    'CONFIG_DIR',
    'UI_DIR',
    'UTILS_DIR',
    'CORE_DIR',
    'get_icon_path',
    'get_slide_path',
    'get_theme_path'
]
