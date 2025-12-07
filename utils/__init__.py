"""
Utilities module for Soplos Welcome Live.
Contains helper functions for autostart, language management, and desktop integration.
"""

from .autostart import AutostartManager
from .language_changer import LanguageChanger, get_language_changer
from .session_manager import SessionManager, get_session_manager

__all__ = [
    'AutostartManager',
    'LanguageChanger',
    'get_language_changer',
    'SessionManager',
    'get_session_manager'
]
