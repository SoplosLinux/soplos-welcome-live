"""
Internationalization (i18n) manager for Soplos Welcome Live.
Handles GNU Gettext translation loading, language detection, and string management.
"""

import os
import locale
import gettext
from pathlib import Path
from typing import Dict, List, Optional, Callable


class I18nManager:
    """
    Manages internationalization using GNU Gettext.
    Provides automatic language detection and translation services.
    """
    
    # Supported languages with their locale codes and native names
    SUPPORTED_LANGUAGES = {
        'es': {'name': 'Spanish', 'native': 'Español', 'locale': 'es_ES.UTF-8'},
        'en': {'name': 'English', 'native': 'English', 'locale': 'en_US.UTF-8'},
        'fr': {'name': 'French', 'native': 'Français', 'locale': 'fr_FR.UTF-8'},
        'de': {'name': 'German', 'native': 'Deutsch', 'locale': 'de_DE.UTF-8'},
        'pt': {'name': 'Portuguese', 'native': 'Português', 'locale': 'pt_PT.UTF-8'},
        'it': {'name': 'Italian', 'native': 'Italiano', 'locale': 'it_IT.UTF-8'},
        'ro': {'name': 'Romanian', 'native': 'Română', 'locale': 'ro_RO.UTF-8'},
        'ru': {'name': 'Russian', 'native': 'Русский', 'locale': 'ru_RU.UTF-8'}
    }
    
    # Language fallback chain
    FALLBACK_CHAIN = ['en', 'es']
    
    def __init__(self, locale_dir: str, domain: str = 'soplos-welcome-live'):
        """
        Initialize the i18n manager.
        
        Args:
            locale_dir: Path to locale directory containing .mo files
            domain: Translation domain name
        """
        self.locale_dir = Path(locale_dir)
        self.domain = domain
        self.current_language = None
        self.translations: Dict[str, gettext.GNUTranslations] = {}
        self.fallback_translation = None
        self._current_translation = None
        
        # Ensure locale directory exists
        self.locale_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize translations
        self._load_translations()
        
        # Detect and set system language
        detected_lang = self.detect_system_language()
        self.set_language(detected_lang)
    
    def _load_translations(self):
        """Load all available translations."""
        for lang_code in self.SUPPORTED_LANGUAGES.keys():
            mo_file = self.locale_dir / lang_code / 'LC_MESSAGES' / f'{self.domain}.mo'
            
            if mo_file.exists():
                try:
                    with open(mo_file, 'rb') as f:
                        translation = gettext.GNUTranslations(f)
                        self.translations[lang_code] = translation
                        print(f"  Loaded translation for {lang_code}")
                except Exception as e:
                    print(f"  Warning: Error loading translation for {lang_code}: {e}")
        
        # Set fallback translation (English)
        if 'en' in self.translations:
            self.fallback_translation = self.translations['en']
        else:
            # Create a null translation if English is not available
            self.fallback_translation = gettext.NullTranslations()
    
    def detect_system_language(self) -> str:
        """
        Detect system language with multiple fallback methods.
        
        Returns:
            Detected language code
        """
        # Method 1: Environment variables (in order of preference)
        env_vars = ['SOPLOS_WELCOME_LANG', 'LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG']
        
        for env_var in env_vars:
            env_value = os.environ.get(env_var)
            if env_value:
                # Extract language code from locale string (e.g., 'es_ES.UTF-8' -> 'es')
                lang_code = env_value.split('_')[0].split('.')[0].split('@')[0].lower()
                if lang_code in self.SUPPORTED_LANGUAGES:
                    return lang_code
        
        # Method 2: Python locale module
        try:
            system_locale = locale.getdefaultlocale()[0]
            if system_locale:
                lang_code = system_locale.split('_')[0].lower()
                if lang_code in self.SUPPORTED_LANGUAGES:
                    return lang_code
        except Exception:
            pass
        
        # Method 3: Check /etc/locale.conf (for systemd-based systems)
        try:
            locale_conf = Path('/etc/locale.conf')
            if locale_conf.exists():
                with open(locale_conf, 'r') as f:
                    for line in f:
                        if line.startswith('LANG='):
                            lang_value = line.split('=')[1].strip().strip('"')
                            lang_code = lang_value.split('_')[0].lower()
                            if lang_code in self.SUPPORTED_LANGUAGES:
                                return lang_code
        except Exception:
            pass
        
        # Default to English
        return 'en'
    
    def set_language(self, lang_code: str) -> bool:
        """
        Set the active language.
        
        Args:
            lang_code: Language code (e.g., 'es', 'en', 'fr')
            
        Returns:
            True if language was set successfully
        """
        if lang_code not in self.SUPPORTED_LANGUAGES:
            print(f"Unsupported language: {lang_code}")
            return False
        
        self.current_language = lang_code
        
        # Set the translation
        if lang_code in self.translations:
            self._current_translation = self.translations[lang_code]
        else:
            # Fall back through chain
            self._current_translation = self.fallback_translation
            for fallback_lang in self.FALLBACK_CHAIN:
                if fallback_lang in self.translations:
                    self._current_translation = self.translations[fallback_lang]
                    break
        
        # Install the translation globally
        if self._current_translation:
            self._current_translation.install()
        
        return True
    
    def gettext(self, message: str) -> str:
        """
        Translate a string.
        
        Args:
            message: The string to translate
            
        Returns:
            Translated string or original if no translation found
        """
        if self._current_translation:
            return self._current_translation.gettext(message)
        return message
    
    def ngettext(self, singular: str, plural: str, n: int) -> str:
        """
        Translate a string with plural forms.
        
        Args:
            singular: Singular form
            plural: Plural form
            n: Count
            
        Returns:
            Appropriate translated form
        """
        if self._current_translation:
            return self._current_translation.ngettext(singular, plural, n)
        return singular if n == 1 else plural
    
    def get_available_languages(self) -> List[str]:
        """Get list of available language codes."""
        return list(self.SUPPORTED_LANGUAGES.keys())
    
    def get_language_name(self, lang_code: str, native: bool = True) -> str:
        """
        Get the display name for a language.
        
        Args:
            lang_code: Language code
            native: If True, return native name; otherwise English name
            
        Returns:
            Language display name
        """
        lang_info = self.SUPPORTED_LANGUAGES.get(lang_code, {})
        if native:
            return lang_info.get('native', lang_code)
        return lang_info.get('name', lang_code)
    
    def get_locale_code(self, lang_code: str) -> str:
        """
        Get the full locale code for a language.
        
        Args:
            lang_code: Short language code (e.g., 'es')
            
        Returns:
            Full locale code (e.g., 'es_ES.UTF-8')
        """
        lang_info = self.SUPPORTED_LANGUAGES.get(lang_code, {})
        return lang_info.get('locale', f'{lang_code}.UTF-8')


# Global singleton instance
_i18n_manager: Optional[I18nManager] = None


def get_i18n_manager() -> Optional[I18nManager]:
    """Get the global i18n manager instance."""
    return _i18n_manager


def initialize_i18n(locale_dir: str, domain: str = 'soplos-welcome-live') -> I18nManager:
    """
    Initialize the global i18n manager.
    
    Args:
        locale_dir: Path to locale directory
        domain: Translation domain name
        
    Returns:
        The initialized I18nManager instance
    """
    global _i18n_manager
    _i18n_manager = I18nManager(locale_dir, domain)
    return _i18n_manager


def _(message: str) -> str:
    """
    Convenience function for translating strings.
    
    Args:
        message: The string to translate
        
    Returns:
        Translated string
    """
    if _i18n_manager:
        return _i18n_manager.gettext(message)
    return message


def ngettext(singular: str, plural: str, n: int) -> str:
    """
    Convenience function for plural translations.
    
    Args:
        singular: Singular form
        plural: Plural form
        n: Count
        
    Returns:
        Appropriate translated form
    """
    if _i18n_manager:
        return _i18n_manager.ngettext(singular, plural, n)
    return singular if n == 1 else plural
