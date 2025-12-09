"""
Language changer for Soplos Welcome Live.
Based on the WORKING legacy implementations from Tyson/Tyron.

Flow:
1. Create ONE bash script with ALL system changes
2. Execute it with ONE sudo call
3. Apply user-level settings (no sudo)
4. Migrate XDG directories
5. Restart display manager
"""

import os
import subprocess
import shutil
import time
from pathlib import Path
from typing import Optional, Tuple, Callable
from enum import Enum

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.environment import get_environment_detector, DesktopEnvironment, DisplayProtocol


class LanguageChangeResult(Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class LanguageChanger:
    """Language changer based on working legacy implementations."""
    
    KEYBOARD_LAYOUTS = {
        'es': 'es', 'en': 'us', 'fr': 'fr', 'de': 'de',
        'pt': 'pt', 'it': 'it', 'ro': 'ro', 'ru': 'ru'
    }
    
    LOCALE_CODES = {
        'es': 'es_ES.UTF-8', 'en': 'en_US.UTF-8', 'fr': 'fr_FR.UTF-8',
        'de': 'de_DE.UTF-8', 'pt': 'pt_PT.UTF-8', 'it': 'it_IT.UTF-8',
        'ro': 'ro_RO.UTF-8', 'ru': 'ru_RU.UTF-8'
    }
    
    def __init__(self):
        self.env_detector = get_environment_detector()
        self.env_detector.detect_all()
        self.desktop = self.env_detector.desktop_environment
        self.display = self.env_detector.display_protocol
        self.edition = self.env_detector.get_edition_name()
    
    def change_language(self, lang_code: str) -> Tuple[LanguageChangeResult, str]:
        """Change language - NO confirmations, just do it and restart."""
        if lang_code not in self.LOCALE_CODES:
            return (LanguageChangeResult.FAILED, f"Unsupported language: {lang_code}")
        
        locale = self.LOCALE_CODES[lang_code]
        layout = self.KEYBOARD_LAYOUTS.get(lang_code, 'us')
        username = os.environ.get('USER', 'liveuser')
        
        try:
            # 1. Configure system locale (ONE sudo call)
            self._configure_system_locale(locale, layout, username)
            
            # 2. Apply user-level settings (no sudo)
            self._apply_user_settings(lang_code, locale, layout)
            
            # 3. Migrate XDG directories
            self._migrate_xdg_directories(locale)
            
            # 4. GTK bookmarks for GNOME
            if self.desktop == DesktopEnvironment.GNOME:
                self._update_gtk_bookmarks()
            
            # 5. Restart display manager immediately
            self._restart_display_manager()
            
            return (LanguageChangeResult.SUCCESS, "")
            
        except Exception as e:
            return (LanguageChangeResult.FAILED, str(e))
    
    def _configure_system_locale(self, locale: str, layout: str, username: str):
        """Configure system locale with ONE sudo call - copied from Tyson legacy."""
        
        # Determine DM-specific config
        dm_config = ""
        if self.desktop == DesktopEnvironment.KDE:
            dm_config = f'''
# SDDM configuration
if [ -d "/etc/sddm.conf.d" ]; then
    echo "[X11]" > /etc/sddm.conf.d/keyboard.conf
    echo "ServerArguments=-layout {layout}" >> /etc/sddm.conf.d/keyboard.conf
    echo "[General]" > /etc/sddm.conf.d/locale.conf
    echo "Language={locale}" >> /etc/sddm.conf.d/locale.conf
fi
'''
        elif self.desktop == DesktopEnvironment.GNOME:
            dm_config = f'''
# GDM/AccountsService configuration
if [ -f /var/lib/AccountsService/users/{username} ]; then
    if grep -q "^Language=" /var/lib/AccountsService/users/{username}; then
        sed -i "s/^Language=.*/Language={locale}/" /var/lib/AccountsService/users/{username}
    else
        echo "Language={locale}" >> /var/lib/AccountsService/users/{username}
    fi
fi
'''
        elif self.desktop == DesktopEnvironment.XFCE:
            dm_config = f'''
# LightDM configuration
if [ -f /etc/lightdm/lightdm.conf ]; then
    sed -i "s/^#*greeter-locale=.*/greeter-locale={locale}/" /etc/lightdm/lightdm.conf 2>/dev/null || true
fi
'''
        
        script = f'''#!/bin/bash
# System locale configuration - ALL in one script

# 1. /etc/locale.conf
cat > /etc/locale.conf << EOF
LANG={locale}
LC_ADDRESS={locale}
LC_IDENTIFICATION={locale}
LC_MEASUREMENT={locale}
LC_MONETARY={locale}
LC_NAME={locale}
LC_NUMERIC={locale}
LC_PAPER={locale}
LC_TELEPHONE={locale}
LC_TIME={locale}
EOF

# 2. /etc/default/locale
cat > /etc/default/locale << EOF
LANG={locale}
LANGUAGE={locale.split('_')[0]}
LC_ALL={locale}
EOF

# 3. /etc/environment
cat > /etc/environment << EOF
LANG={locale}
LANGUAGE={locale.split('_')[0]}
EOF

# 4. Generate locale
locale-gen {locale} 2>/dev/null || true

# 5. localectl
localectl set-locale LANG={locale} 2>/dev/null || true
localectl set-x11-keymap {layout} 2>/dev/null || true

# 6. Wayland keyboard config
mkdir -p /etc/xdg
echo "XKBLAYOUT={layout}" > /etc/xdg/keyboard

# 7. Console keyboard
echo "KEYMAP={layout}" > /etc/vconsole.conf 2>/dev/null || true

# 8. X11 keyboard config
mkdir -p /etc/X11/xorg.conf.d
cat > /etc/X11/xorg.conf.d/00-keyboard.conf << EOF
Section "InputClass"
    Identifier "system-keyboard"
    MatchIsKeyboard "on"
    Option "XkbLayout" "{layout}"
EndSection
EOF

{dm_config}

echo "System locale configured"
'''
        
        script_path = '/tmp/configure_system_locale.sh'
        with open(script_path, 'w') as f:
            f.write(script)
        os.chmod(script_path, 0o755)
        
        # ONE sudo call
        subprocess.run(['sudo', '/bin/bash', script_path], check=True, timeout=60)
    
    def _apply_user_settings(self, lang_code: str, locale: str, layout: str):
        """Apply user-level settings (no sudo needed)."""
        
        # Update environment
        os.environ['LANG'] = locale
        os.environ['LC_ALL'] = locale
        os.environ['LANGUAGE'] = lang_code
        
        if self.desktop == DesktopEnvironment.KDE:
            # KDE user settings
            kwrite = 'kwriteconfig6' if shutil.which('kwriteconfig6') else 'kwriteconfig5'
            subprocess.run([kwrite, '--file', 'plasma-localerc', '--group', 'Translations',
                          '--key', 'LANGUAGE', lang_code], check=False)
            subprocess.run([kwrite, '--file', 'plasma-localerc', '--group', 'Formats',
                          '--key', 'LANG', locale], check=False)
            subprocess.run([kwrite, '--file', 'kxkbrc', '--group', 'Layout',
                          '--key', 'LayoutList', layout], check=False)
            subprocess.run([kwrite, '--file', 'kxkbrc', '--group', 'Layout',
                          '--key', 'Use', 'true'], check=False)
            subprocess.run(['qdbus', 'org.kde.keyboard', '/Layouts', 'reset'], check=False)
            
        elif self.desktop == DesktopEnvironment.GNOME:
            # GNOME user settings
            subprocess.run(['gsettings', 'set', 'org.gnome.system.locale', 'region', locale], check=False)
            subprocess.run(['gsettings', 'set', 'org.gnome.desktop.input-sources', 'sources',
                          f"[('xkb', '{layout}')]"], check=False)
            
        elif self.desktop == DesktopEnvironment.XFCE:
            # XFCE user settings
            subprocess.run(['xfconf-query', '-c', 'keyboard-layout', '-p', '/Default/XkbLayout',
                          '-s', layout], check=False)
        
        # Try setxkbmap (works on X11)
        subprocess.run(['setxkbmap', layout], check=False, timeout=5)
    
    def _migrate_xdg_directories(self, locale: str):
        """Migrate XDG user directories."""
        home = Path.home()
        user_dirs_file = home / '.config' / 'user-dirs.dirs'
        
        def parse_dirs(file_path):
            dirs = {}
            if file_path.exists():
                with open(file_path, 'r') as f:
                    for line in f:
                        if line.startswith('XDG_') and '=' in line:
                            key, value = line.strip().split('=', 1)
                            # Handle both "$HOME/Path" and "/home/user/Path" formats
                            clean_value = value.strip('"')
                            if clean_value.startswith('$HOME/'):
                                path = clean_value.replace('$HOME/', '')
                                dirs[key] = home / path
                            elif clean_value.startswith('/'):
                                dirs[key] = Path(clean_value)
                            else:
                                # Relative path fallback
                                dirs[key] = home / clean_value
            return dirs

        # Get old dirs BEFORE update
        old_dirs = parse_dirs(user_dirs_file)
        
        # Save explicit reference to old Desktop for Calamares icon fallback
        old_desktop = old_dirs.get('XDG_DESKTOP_DIR', home / 'Desktop')
        
        # Force update with new locale
        env = os.environ.copy()
        env['LANG'] = locale
        env['LC_ALL'] = locale
        # Ensure xdg-user-dirs-update uses the intended language
        env['LANGUAGE'] = locale.split('_')[0]
        try:
            subprocess.run(['xdg-user-dirs-update', '--force'], env=env, check=False, timeout=30)
        except Exception as e:
            print(f"XDG update error: {e}")
        
        # Get new dirs AFTER update
        new_dirs = parse_dirs(user_dirs_file)
        
        # Migrate content
        for key, old_path in old_dirs.items():
            # Find corresponding new path
            new_path = new_dirs.get(key)
            
            if not new_path or old_path == new_path or not old_path.exists():
                continue
            
            # Create new directory if needed
            if not new_path.exists():
                try:
                    new_path.mkdir(parents=True, exist_ok=True)
                except: pass
            
            # Move content
            if new_path.exists():
                for item in old_path.iterdir():
                    dest = new_path / item.name
                    if not dest.exists():
                        try:
                            shutil.move(str(item), str(dest))
                            print(f"Moved {item.name} to {dest}")
                        except Exception as e:
                            print(f"Failed to move {item}: {e}")
                
                # Setup specific symlink/files for Desktop
                if key == 'XDG_DESKTOP_DIR':
                    # List of desktop files to explicitly move if generic move failed or they are special
                    desktop_files = [
                        'calamares-install-soplos.desktop',
                        'home.desktop',
                        'trash.desktop'
                    ]
                    
                    for desktop_filename in desktop_files:
                        old_file = old_path / desktop_filename
                        new_file = new_path / desktop_filename
                        
                        if old_file.exists() and not new_file.exists():
                             try:
                                 shutil.move(str(old_file), str(new_file))
                                 print(f"Moved {desktop_filename} to {new_path}")
                             except Exception as e:
                                 print(f"Failed to move {desktop_filename}: {e}")

                # Try to remove old dir if empty
                try:
                    if not any(old_path.iterdir()):
                        old_path.rmdir()
                except:
                    pass
        
        # Update KDE/Plasma configuration if detected
        if self.desktop == DesktopEnvironment.KDE:
            try:
                # Update Dolphin HomeUrl
                kwrite = 'kwriteconfig6' if shutil.which('kwriteconfig6') else 'kwriteconfig5'
                subprocess.run([
                    kwrite, '--file', 'dolphinrc',
                    '--group', 'General', '--key', 'HomeUrl',
                    f'file://{home}'
                ], check=False)
                
                # Update Plasma Desktop view URL
                # Use XDG_DESKTOP_DIR from new_dirs or fallback to 'Desktop' in user's home
                desktop_path = new_dirs.get('XDG_DESKTOP_DIR', home / 'Desktop')
                
                subprocess.run([
                    kwrite, '--file', 'plasma-org.kde.plasma.desktop-appletsrc',
                    '--group', 'Containments', '--group', '1', '--group', 'General',
                    '--key', 'url', f'file://{desktop_path}'
                ], check=False)
                
                # Remove Dolphin bookmarks file so KDE/Dolphin will regenerate it
                # on next session start. For a live system we remove it outright
                # (do NOT move to Trash) to ensure the regenerated file matches
                # the new XDG directories.
                try:
                    xbel_path = home / '.local' / 'share' / 'user-places.xbel'
                    if xbel_path.exists():
                        xbel_path.unlink()
                except Exception:
                    pass

                # Also remove any stray copy in the Trash files (if present)
                try:
                    trash_copy = home / '.local' / 'share' / 'Trash' / 'files' / 'user-places.xbel'
                    if trash_copy.exists():
                        trash_copy.unlink()
                except Exception:
                    pass
                
                # Force refresh of Plasma Shell
                subprocess.run(['qdbus', 'org.kde.plasmashell', '/PlasmaShell', 
                               'org.kde.PlasmaShell.evaluateScript', 
                               'refreshCurrentShell()'], check=False)
            except Exception as e:
                print(f"Error updating KDE references: {e}")
    
    # KDE bookmark remapping code removed: we rely on deleting
    # `~/.local/share/user-places.xbel` so KDE/Dolphin regenerates it.
    
    def _update_gtk_bookmarks(self):
        """Update GTK bookmarks for GNOME."""
        try:
            from utils.update_gtk_bookmarks import update_gtk_bookmarks
            update_gtk_bookmarks()
        except:
            pass
    
    def _restart_display_manager(self):
        """Restart the display manager safely."""
        # Force sync to disk to prevent config read errors
        subprocess.run(['sync'], check=False)
        time.sleep(1)
        
        # Try generic alias first (Works on most systemd distros)
        dm_service = 'display-manager.service'
        
        # If specific override needed (though display-manager should handle it)
        # We can fallback to detected names if the alias fails?
        # But for now, let's try the alias as primary.
        
        print(f"Restarting {dm_service}...")
        try:
            subprocess.run(['sudo', 'systemctl', 'restart', dm_service], check=True, timeout=30)
        except subprocess.CalledProcessError:
            # Fallback to hardcoded names if alias fails
            dm_map = {
                DesktopEnvironment.XFCE: 'lightdm',
                DesktopEnvironment.KDE: 'sddm',
                DesktopEnvironment.GNOME: 'gdm3', # Try gdm3 first
            }
            dm = dm_map.get(self.desktop, 'gdm3')
            
            # Double check for GNOME: gdm vs gdm3
            if self.desktop == DesktopEnvironment.GNOME:
                # Check if gdm exists
                try:
                    subprocess.run(['systemctl', 'status', 'gdm'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    dm = 'gdm'
                except:
                    dm = 'gdm3'
            
            print(f"Fallback restart: {dm}...")
            subprocess.run(['sudo', 'systemctl', 'restart', dm], check=True, timeout=30)
    
    def get_current_language_code(self) -> str:
        locale = os.environ.get('LANG', 'en_US.UTF-8')
        return locale.split('_')[0] if '_' in locale else 'en'


# Singleton
_language_changer: Optional[LanguageChanger] = None

def get_language_changer() -> LanguageChanger:
    global _language_changer
    if _language_changer is None:
        _language_changer = LanguageChanger()
    return _language_changer
