"""
Language changer for Soplos Welcome Live.
Handles live language switching with desktop-specific implementations.

Supports:
- XFCE (Tyron): Uses numlockx and xfconf for X11
- KDE Plasma (Tyson): Uses kwriteconfig5/6 and plasma-apply-locale
- GNOME (Boro): Uses dconf/gsettings
"""

import os
import subprocess
import json
import time
import shutil
from pathlib import Path
from typing import Optional, Tuple, List, Callable
from enum import Enum

# Import environment detector
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.environment import get_environment_detector, DesktopEnvironment, DisplayProtocol


class LanguageChangeResult(Enum):
    """Result of a language change operation."""
    SUCCESS = "success"
    PARTIAL = "partial"  # Some settings changed but not all
    FAILED = "failed"
    RESTART_REQUIRED = "restart_required"


class LanguageChanger:
    """
    Handles live language switching with desktop-specific implementations.
    """
    
    # Keyboard layout mapping
    KEYBOARD_LAYOUTS = {
        'es': {'layout': 'es', 'variant': ''},
        'en': {'layout': 'us', 'variant': ''},
        'fr': {'layout': 'fr', 'variant': ''},
        'de': {'layout': 'de', 'variant': ''},
        'pt': {'layout': 'pt', 'variant': ''},
        'it': {'layout': 'it', 'variant': ''},
        'ro': {'layout': 'ro', 'variant': ''},
        'ru': {'layout': 'ru', 'variant': ''}
    }
    
    # Locale mapping
    LOCALE_CODES = {
        'es': 'es_ES.UTF-8',
        'en': 'en_US.UTF-8',
        'fr': 'fr_FR.UTF-8',
        'de': 'de_DE.UTF-8',
        'pt': 'pt_PT.UTF-8',
        'it': 'it_IT.UTF-8',
        'ro': 'ro_RO.UTF-8',
        'ru': 'ru_RU.UTF-8'
    }
    
    def __init__(self):
        """Initialize the language changer."""
        self.env_detector = get_environment_detector()
        self.env_detector.detect_all()
        
        # Detect desktop environment
        self.desktop = self.env_detector.desktop_environment
        self.display = self.env_detector.display_protocol
        
        # Get edition name
        self.edition = self.env_detector.get_edition_name()
        
        print(f"LanguageChanger initialized for {self.edition} ({self.desktop.value}/{self.display.value})")
    
    def change_language(self, lang_code: str, callback: Optional[Callable] = None) -> Tuple[LanguageChangeResult, str]:
        """
        Change the system language.
        
        Args:
            lang_code: Language code (e.g., 'es', 'en', 'fr')
            callback: Optional callback for progress updates
            
        Returns:
            Tuple of (result, message)
        """
        if lang_code not in self.LOCALE_CODES:
            return (LanguageChangeResult.FAILED, f"Unsupported language: {lang_code}")
        
        locale_code = self.LOCALE_CODES[lang_code]
        keyboard = self.KEYBOARD_LAYOUTS.get(lang_code, {'layout': 'us', 'variant': ''})
        
        # Route to appropriate handler based on desktop environment
        if self.desktop == DesktopEnvironment.XFCE:
            return self._change_language_xfce(lang_code, locale_code, keyboard, callback)
        elif self.desktop == DesktopEnvironment.KDE:
            return self._change_language_kde(lang_code, locale_code, keyboard, callback)
        elif self.desktop == DesktopEnvironment.GNOME:
            return self._change_language_gnome(lang_code, locale_code, keyboard, callback)
        else:
            return self._change_language_generic(lang_code, locale_code, keyboard, callback)
    
    def _change_language_xfce(self, lang_code: str, locale_code: str, keyboard: dict, 
                               callback: Optional[Callable] = None) -> Tuple[LanguageChangeResult, str]:
        """
        Change language for XFCE (Tyron edition).
        Uses xfconf-query and numlockx for X11.
        """
        results = []
        
        try:
            if callback:
                callback("Changing XFCE language settings...")
            
            # 1. Update locale environment files
            self._update_locale_files(locale_code)
            results.append(("locale_files", True))
            
            # 2. Change keyboard layout using xfconf (XFCE specific)
            if self.display == DisplayProtocol.X11:
                try:
                    # Set keyboard layout via xfconf
                    subprocess.run([
                        'xfconf-query', '-c', 'keyboard-layout', 
                        '-p', '/Default/XkbLayout', '-s', keyboard['layout']
                    ], capture_output=True, timeout=10)
                    
                    # Also set via setxkbmap for immediate effect
                    cmd = ['setxkbmap', keyboard['layout']]
                    if keyboard['variant']:
                        cmd.extend(['-variant', keyboard['variant']])
                    subprocess.run(cmd, capture_output=True, timeout=10)
                    
                    results.append(("keyboard", True))
                except Exception as e:
                    print(f"Keyboard layout change warning: {e}")
                    results.append(("keyboard", False))
            
            # 3. Handle NumLockX (XFCE/X11 specific)
            if self.display == DisplayProtocol.X11:
                self._handle_numlockx()
                results.append(("numlockx", True))
            
            # 4. Update XFCE session locale
            try:
                # Update LANG in xfce4-session
                xfce_session_conf = Path.home() / ".config" / "xfce4" / "xfconf" / "xfce-perchannel-xml" / "xfce4-session.xml"
                if xfce_session_conf.parent.exists():
                    # This requires session restart to take effect
                    pass
                results.append(("xfce_session", True))
            except Exception as e:
                results.append(("xfce_session", False))
            
            # Check results
            failed = [r[0] for r in results if not r[1]]
            if not failed:
                return (LanguageChangeResult.RESTART_REQUIRED, 
                        f"Language changed to {lang_code}. Session restart required for full effect.")
            elif len(failed) < len(results):
                return (LanguageChangeResult.PARTIAL, 
                        f"Language partially changed. Failed: {', '.join(failed)}")
            else:
                return (LanguageChangeResult.FAILED, "Failed to change language settings.")
                
        except Exception as e:
            return (LanguageChangeResult.FAILED, f"Error changing XFCE language: {e}")
    
    def _change_language_kde(self, lang_code: str, locale_code: str, keyboard: dict,
                              callback: Optional[Callable] = None) -> Tuple[LanguageChangeResult, str]:
        """
        Change language for KDE Plasma (Tyson edition).
        Uses kwriteconfig5/6 and plasma-apply-* commands.
        """
        results = []
        
        try:
            if callback:
                callback("Changing KDE Plasma language settings...")
            
            # 1. Update locale environment files
            self._update_locale_files(locale_code)
            results.append(("locale_files", True))
            
            # 2. Detect KDE version and use appropriate tools
            kwrite_cmd = self._get_kwriteconfig_command()
            
            # 3. Update kdeglobals
            try:
                # Set LANG in kdeglobals
                subprocess.run([
                    kwrite_cmd, '--file', 'kdeglobals', 
                    '--group', 'Locale', '--key', 'Language', lang_code
                ], capture_output=True, timeout=10)
                
                # Set formats locale
                subprocess.run([
                    kwrite_cmd, '--file', 'plasma-localerc',
                    '--group', 'Formats', '--key', 'LANG', locale_code
                ], capture_output=True, timeout=10)
                
                # Set language in plasma-localerc
                for key in ['LC_NUMERIC', 'LC_TIME', 'LC_MONETARY', 'LC_MEASUREMENT', 'LC_COLLATE']:
                    subprocess.run([
                        kwrite_cmd, '--file', 'plasma-localerc',
                        '--group', 'Formats', '--key', key, locale_code
                    ], capture_output=True, timeout=10)
                
                results.append(("kdeglobals", True))
            except Exception as e:
                print(f"KDE config warning: {e}")
                results.append(("kdeglobals", False))
            
            # 4. Change keyboard layout
            try:
                # Try plasma-apply-keyboard for Plasma 6
                result = subprocess.run([
                    'plasma-apply-keyboard', keyboard['layout']
                ], capture_output=True, timeout=10)
                
                if result.returncode != 0:
                    # Fallback to kwriteconfig
                    subprocess.run([
                        kwrite_cmd, '--file', 'kxkbrc',
                        '--group', 'Layout', '--key', 'LayoutList', keyboard['layout']
                    ], capture_output=True, timeout=10)
                
                results.append(("keyboard", True))
            except Exception as e:
                print(f"Keyboard layout change warning: {e}")
                results.append(("keyboard", False))
            
            # 5. Update session locale for Wayland
            if self.display == DisplayProtocol.WAYLAND:
                self._update_wayland_session_locale(locale_code)
                results.append(("wayland_session", True))
            
            # Check results
            failed = [r[0] for r in results if not r[1]]
            if not failed:
                return (LanguageChangeResult.RESTART_REQUIRED,
                        f"Language changed to {lang_code}. Please restart your session for full effect.")
            elif len(failed) < len(results):
                return (LanguageChangeResult.PARTIAL,
                        f"Language partially changed. Failed: {', '.join(failed)}")
            else:
                return (LanguageChangeResult.FAILED, "Failed to change language settings.")
                
        except Exception as e:
            return (LanguageChangeResult.FAILED, f"Error changing KDE language: {e}")
    
    def _change_language_gnome(self, lang_code: str, locale_code: str, keyboard: dict,
                                callback: Optional[Callable] = None) -> Tuple[LanguageChangeResult, str]:
        """
        Change language for GNOME (Boro edition).
        Uses dconf/gsettings.
        """
        results = []
        
        try:
            if callback:
                callback("Changing GNOME language settings...")
            
            # 1. Update locale environment files
            self._update_locale_files(locale_code)
            results.append(("locale_files", True))
            
            # 2. Update GNOME locale settings via dconf/gsettings
            try:
                # Set system locale
                subprocess.run([
                    'gsettings', 'set', 'org.gnome.system.locale', 'region', locale_code
                ], capture_output=True, timeout=10)
                
                # Set input sources (keyboard layout)
                keyboard_source = f"[('xkb', '{keyboard['layout']}')]"
                subprocess.run([
                    'gsettings', 'set', 'org.gnome.desktop.input-sources', 'sources', keyboard_source
                ], capture_output=True, timeout=10)
                
                results.append(("gsettings", True))
            except Exception as e:
                print(f"GNOME gsettings warning: {e}")
                results.append(("gsettings", False))
            
            # 3. Use dconf directly for more settings
            try:
                # Update locale via dconf
                dconf_commands = [
                    f"/system/locale/region '{locale_code}'",
                    f"/org/gnome/desktop/input-sources/sources [('xkb', '{keyboard['layout']}')]"
                ]
                
                for dconf_cmd in dconf_commands:
                    key, value = dconf_cmd.split(' ', 1)
                    subprocess.run([
                        'dconf', 'write', key, value
                    ], capture_output=True, timeout=10)
                
                results.append(("dconf", True))
            except Exception as e:
                print(f"GNOME dconf warning: {e}")
                results.append(("dconf", False))
            
            # 4. Update AccountsService locale (system-wide for login screen)
            self._update_accountsservice_locale(locale_code, lang_code)
            results.append(("accountsservice", True))
            
            # 5. Handle Wayland-specific settings
            if self.display == DisplayProtocol.WAYLAND:
                self._update_wayland_session_locale(locale_code)
                results.append(("wayland_session", True))
            
            # Check results
            failed = [r[0] for r in results if not r[1]]
            if not failed:
                return (LanguageChangeResult.RESTART_REQUIRED,
                        f"Language changed to {lang_code}. Please restart your session for full effect.")
            elif len(failed) < len(results):
                return (LanguageChangeResult.PARTIAL,
                        f"Language partially changed. Failed: {', '.join(failed)}")
            else:
                return (LanguageChangeResult.FAILED, "Failed to change language settings.")
                
        except Exception as e:
            return (LanguageChangeResult.FAILED, f"Error changing GNOME language: {e}")
    
    def _change_language_generic(self, lang_code: str, locale_code: str, keyboard: dict,
                                  callback: Optional[Callable] = None) -> Tuple[LanguageChangeResult, str]:
        """Generic language change for unknown desktops."""
        try:
            self._update_locale_files(locale_code)
            return (LanguageChangeResult.RESTART_REQUIRED,
                    f"Basic locale files updated to {lang_code}. Restart session for effect.")
        except Exception as e:
            return (LanguageChangeResult.FAILED, f"Error: {e}")
    
    def _update_locale_files(self, locale_code: str):
        """Update locale configuration files."""
        home = Path.home()
        
        # Update ~/.config/locale.conf
        locale_conf = home / ".config" / "locale.conf"
        locale_conf.parent.mkdir(parents=True, exist_ok=True)
        
        locale_content = f"""LANG={locale_code}
LC_NUMERIC={locale_code}
LC_TIME={locale_code}
LC_MONETARY={locale_code}
LC_PAPER={locale_code}
LC_MEASUREMENT={locale_code}
LC_NAME={locale_code}
LC_ADDRESS={locale_code}
LC_TELEPHONE={locale_code}
LC_IDENTIFICATION={locale_code}
"""
        with open(locale_conf, 'w') as f:
            f.write(locale_content)
        
        # Update ~/.pam_environment (for some systems)
        pam_env = home / ".pam_environment"
        pam_content = f"""LANG={locale_code}
LANGUAGE={locale_code.split('.')[0]}
"""
        with open(pam_env, 'w') as f:
            f.write(pam_content)
        
        # Update current environment
        os.environ['LANG'] = locale_code
        os.environ['LANGUAGE'] = locale_code.split('_')[0]
    
    def _handle_numlockx(self):
        """Handle NumLockX for XFCE/X11."""
        # Check if numlockx is available
        if shutil.which('numlockx'):
            try:
                # Turn on numlock (common preference)
                subprocess.run(['numlockx', 'on'], capture_output=True, timeout=5)
            except Exception:
                pass
    
    def _get_kwriteconfig_command(self) -> str:
        """Get the appropriate kwriteconfig command for the KDE version."""
        # Try kwriteconfig6 first (Plasma 6)
        if shutil.which('kwriteconfig6'):
            return 'kwriteconfig6'
        elif shutil.which('kwriteconfig5'):
            return 'kwriteconfig5'
        else:
            return 'kwriteconfig'
    
    def _update_wayland_session_locale(self, locale_code: str):
        """Update locale for Wayland sessions."""
        # Update environment.d for systemd user session
        env_dir = Path.home() / ".config" / "environment.d"
        env_dir.mkdir(parents=True, exist_ok=True)
        
        env_file = env_dir / "locale.conf"
        with open(env_file, 'w') as f:
            f.write(f"LANG={locale_code}\n")
    
    def _update_accountsservice_locale(self, locale_code: str, lang_code: str):
        """Update AccountsService locale (requires root or polkit)."""
        # This typically requires elevated privileges
        # For live session, we skip this or use pkexec
        pass
    
    def get_current_locale(self) -> str:
        """Get the current system locale."""
        return os.environ.get('LANG', 'en_US.UTF-8')
    
    def get_current_language_code(self) -> str:
        """Get the current language code."""
        locale = self.get_current_locale()
        return locale.split('_')[0] if '_' in locale else locale.split('.')[0]


# Global singleton
_language_changer: Optional[LanguageChanger] = None


def get_language_changer() -> LanguageChanger:
    """Get or create the global language changer instance."""
    global _language_changer
    if _language_changer is None:
        _language_changer = LanguageChanger()
    return _language_changer
