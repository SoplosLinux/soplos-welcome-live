# Soplos Welcome Live

[![License: GPL-3.0+](https://img.shields.io/badge/License-GPL--3.0%2B-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Version](https://img.shields.io/badge/version-2.0.2--4-green.svg)]()

Welcome application for Soplos Linux Live Environment with advanced system recovery tools.

## 📝 Description

Soplos Welcome Live 2.0 is the welcome application for the Soplos Linux Live environment. It provides an intuitive interface for system installation via Calamares and professional-grade system recovery tools with full BTRFS support.

Built with the same modular architecture as Soplos Welcome 2.0, it offers universal desktop compatibility (XFCE, KDE Plasma, GNOME) and complete X11/Wayland support.

## ✨ Features

### 🎯 Installation
- **Calamares Integration**: Direct system installation with privilege management
- **Language Configuration**: Automatic locale detection and keyboard setup
- **XDG Folder Migration**: Intelligent folder renaming when changing language

### 🛠️ System Recovery (CHROOT)
- **Advanced CHROOT System**: Complete system recovery environment
- **Intelligent Partition Detection**: Automatic mount suggestions
- **Full BTRFS Support**: Subvolume detection and mounting
- **GParted Integration**: Professional disk management
- **Universal Compatibility**: Works with any Linux distribution

### 🌐 Internationalization
- **8 Languages**: ES, EN, FR, DE, PT, IT, RO, RU (100% complete)
- **Keyboard Mnemonics**: Full accessibility support
- **GNU Gettext**: Professional translation system

### 🖥️ Desktop Support
- **XFCE (Tyron)**: Full support with NumLock management
- **KDE Plasma (Tyson)**: Native integration
- **GNOME (Boro)**: Complete compatibility
- **X11 & Wayland**: Universal display protocol support

## 📸 Screenshots

### Main Window
![Main Window](https://raw.githubusercontent.com/SoplosLinux/soplos-welcome-live/main/assets/screenshots/screenshot1.png)

### Disk Selection
![Disk Selection](https://raw.githubusercontent.com/SoplosLinux/soplos-welcome-live/main/assets/screenshots/screenshot2.png)

### Partition Mount Point Assignment
![Partition Assignment](https://raw.githubusercontent.com/SoplosLinux/soplos-welcome-live/main/assets/screenshots/screenshot3.png)

### Guided Rescue Operations
![Rescue Operations](https://raw.githubusercontent.com/SoplosLinux/soplos-welcome-live/main/assets/screenshots/screenshot4.png)

### Interactive CHROOT Terminal
![CHROOT Terminal](https://raw.githubusercontent.com/SoplosLinux/soplos-welcome-live/main/assets/screenshots/screenshot5.png)

## 🔧 Installation

```bash
sudo apt install soplos-welcome-live
```

### Dependencies
- `python3` (≥3.8)
- `python3-gi`, `gir1.2-gtk-3.0`
- `python3-psutil`
- `calamares` (recommended)
- `gparted` (recommended)

## 🌐 Supported Languages

| Language   | Code | Status      |
|------------|------|-------------|
| Spanish    | `es` | ✅ Complete |
| English    | `en` | ✅ Complete |
| French     | `fr` | ✅ Complete |
| Portuguese | `pt` | ✅ Complete |
| German     | `de` | ✅ Complete |
| Italian    | `it` | ✅ Complete |
| Romanian   | `ro` | ✅ Complete |
| Russian    | `ru` | ✅ Complete |

## 📄 License

[GPL-3.0+](https://www.gnu.org/licenses/gpl-3.0.html) - GNU General Public License v3 or later.

## 👤 Developer

Developed by **Sergi Perich**  
Website: https://soplos.org  
Contact: info@soploslinux.com

## 🔗 Links

- [Website](https://soplos.org)
- [Report Issues](https://github.com/SoplosLinux/soplos-welcome-live/issues)
- [Community Forums](https://soplos.org/forums/)
- [Donate](https://www.paypal.com/paypalme/isubdes)

## 📦 Version History

### v2.0.2-4 (2026-06-24)
- **Fix**: Language changer now detects the active display manager with `systemctl is-active` and restarts it directly (`plasmalogin` on Tyson RC1, `sddm` on beta ISOs). Resolves Breeze wallpaper on plasmalogin and ksplashqml crash cascade on VirtualBox after language change.

### v2.0.2-3 (2026-06-23)
- **Fix**: Ghostty is now the first-priority terminal in the CHROOT recovery terminal launcher for all three desktop environments (XFCE/Tyron, KDE/Tyson, GNOME/Boro), reflecting its role as the new default terminal across all three distros.

### v2.0.2-2 (2026-06-22)
- **Fix**: Language changer on KDE now tries `plasmalogin` first, then `sddm` as fallback, supporting both Tyson RC1 and beta users.

### v2.0.2 (2026-03-31)
- **Fade-in animation**: Smooth opacity transition on startup.
- **Tooltips**: All interactive elements now have descriptive tooltips.
- **Internet indicator**: Live green/red dot in the status bar, refreshed every 15 seconds in background.
- **Hardware Info button**: Opens a dialog with CPU, RAM and storage details.
- **GParted button**: Direct access to GParted from the main window.
- **Guided Rescue Operations**: After mounting in CHROOT, a new dedicated window provides: Reset Password, Repair GRUB (UEFI/BIOS auto-detect), Update GRUB, Regenerate initramfs, and interactive terminal access.
- **Fixes**: Removed wrong positional partition auto-assignment, fixed dark strip in partition dialog, removed misleading column headers from partition grid.
- **Translations**: All 8 languages updated and compiled.

### v2.0.1-1 (2026-03-21)
- **About dialog**: F1 shortcut and GNOME menu action open the About dialog.
- **Code cleanup**: Removed all debug/diagnostic print statements from production code.
- **Bug fixes**: Eliminated duplicate `_initialize_theming()` call, duplicate imports and duplicate accessibility env setup.
- **CSS fix**: About dialog now renders with uniform dark background across all sections.

### v2.0.1 (2026-01-09)
- **Documentation**: Added manual page and copyright file.

### v2.0.0 (2025-12-07)
- **Architecture Rewrite**: Modular design matching Soplos Welcome 2.0
- **Universal Desktop**: Single codebase for XFCE, Plasma, and GNOME
- **X11/Wayland**: Complete display protocol support
- **GNU Gettext**: Professional internationalization (8 languages)
- **Improved CHROOT**: Enhanced partition detection and BTRFS support

#### Patch - 2025-12-08
- Fixed: normalized `Gtk.Switch` styling in Live so switches render consistently across desktop themes (removed oval/stretch issue)
- Added focused CSS overrides and set application CSS priority to ensure theme rules apply correctly
- Updated screenshots prepared for the welcome flow (replace legacy captures before packaging)

#### Patch - 2025-12-09
- GNOME / Wayland display improvements:
	- Improved detection and setting of resolutions on GNOME Wayland (GDK-first detection with a robust D-Bus fallback).
	- Avoids incorrect virtual/guest modes at startup, chooses best available refresh rate, and applies temporary monitor changes suitable for Live ISO usage.

#### Patch - 2025-12-10
- Restored legacy functionality for robust Chroot operations (safe unmount, exact mount sequence).
- Added cross-DE terminal support (XFCE, Plasma, GNOME) with environment-aware launching.
- Implemented **Resolution Persistence**: Resolution changes now persist across language-switch restarts in GNOME (Wayland) and XFCE (X11).
- Restored original UI progress dialogs and buttons.
- **Translation Overhaul**: Complete quality review and refinement of all 8 languages (ES, EN, DE, FR, PT, IT, RO, RU) ensuring 100% string coverage and UI-conciseness.


### v1.1.6 (2025-11-29) _(Tyson only)_
- Universal disk detection in CHROOT: removed restrictive `lsblk` filter; detects all types (MMC, NVMe, USB, loop, etc.).
- Partition parsing switched to JSON (`lsblk -J`) with text fallback.
- Improved BTRFS subvolume detection.

### v1.1.2 (2025-11-29) _(Tyron only)_
- Universal disk detection in CHROOT: removed restrictive `lsblk` filter; detects all types on any hardware and VM.
- Fixed indentation errors in `core/chroot_operations.py`.

### v1.1.5 (2025-09-08) _(Tyson only)_
- Welcome tab URLs updated to soplos.org.

### v1.1.1 (2025-09-08) _(Tyron only)_
- Welcome tab URLs updated to soplos.org.

### v1.1.4 (2025-08-02) _(Tyson only)_
- Dictionary issues fixed and full i18n completed across all 8 languages.
- CHROOT function improved for systems with BTRFS subvolumes.

### v1.1.3 (2025-08-02) _(Tyson only)_
- Program icon updated to new design.
- Maintainer changed to Sergi Perich.

### v1.1.0 (2025-08-03) _(Tyron only)_
- Complete i18n refactor: translation dictionaries split into 8 separate files.
- Fixed all known BTRFS subvolume mounting issues in CHROOT.

### v1.1.2 (2025-07-27) _(Tyson only)_
- Advanced partition and BTRFS subvolume detection in CHROOT.
- Full `/home` mounting support as partition or BTRFS subvolume.

### v1.1.1 (2025-07-18) _(Tyson only)_
- Language detection and startup robustness improvements. Minor translation fixes.

### v1.1.0 (2025-07-18) _(Tyson only)_
- Metainfo finalized to AppStream/DEP-11 standard.
- Program icons added in 48×48, 64×64 and 128×128 px.

### v1.0.9 (2025-08-02) _(Tyron only)_
- Program icon updated to new design.

### v1.0.9 (2025-07-15) _(Tyson only)_
- Metainfo corrections for proper appearance in software centers (AppStream/Discover).

### v1.0.8 (2025-05-08) _(Tyron only)_
- Advanced partition and BTRFS subvolume detection in CHROOT.
- Full `/home` mounting support as partition or BTRFS subvolume.
- GParted integration and robust filesystem validation.
- Maintainer updated to Sergi Perich.

### v1.0.8 (2025-07-13) _(Tyson only)_
- Metainfo file fixed for proper visualization in Discover/AppStream.

### v1.0.7 (2025-05-08) _(Tyron only)_
- Advanced partition and BTRFS subvolume detection in CHROOT.
- Full `/home` mounting support as partition or BTRFS subvolume.

### v1.0.7 (2025-07-13) _(Tyson only)_
- Full BTRFS subvolume support in CHROOT recovery.
- Dictionary string corrections across all languages.
- NumLockX completely removed (not applicable to KDE Plasma).

### v1.0.6 (2025-05-08) _(Tyron only)_
- Metainfo updated for AppStream/DEP-11 compliance.

### v1.0.6 (2025-06-24) _(Tyson only)_
- AppStream integration: application now visible in KDE Discover.

### v1.0.5 (2025-05-07) _(Tyron only)_
- Full BTRFS subvolume support in CHROOT recovery.
- Complete i18n in 8 languages with keyboard mnemonics.

### v1.0.5 (2025-06-20) _(Tyson only)_
- Complete program internationalization in 8 languages.
- Minor bug fixes and stability improvements.

### v1.0.4 (2025-05-07) _(Tyron only)_
- Intelligent partition detection in CHROOT.
- NumLock management integration and automatic XDG folder migration on language change.
- GParted integration and robust filesystem validation.
- Complete i18n in 8 languages.

### v1.0.3 (2025-05-06) _(Tyron only)_
- Locale configuration fixes and interface optimizations.

### v1.0.3 (2025-06-14) _(Tyson only)_
- **Initial Release (Tyson)**: Basic welcome interface with Calamares integration.
- CHROOT recovery tools and GParted integration.
- Multi-language support (8 languages) and hardware detection.

### v1.0.2 (2025-05-05) _(Tyron only)_
- CHROOT operation fixes and general stability improvements.
- Hardware detection improvements.

### v1.0.2 (2025-06-09) _(Tyson only)_
- Minor bug fixes and stability improvements.

### v1.0.1 (2025-05-16) _(Tyron only)_
- User interface improvements and configuration optimizations.

### v1.0.1 (2025-05-28) _(Tyson only)_
- Minor interface fixes and stability improvements.

### v1.0.0 (2025-05-09) _(Tyron only)_
- **Initial Release (Tyron)**: Basic welcome interface for Soplos Linux Live.
- Basic CHROOT functionality for system recovery.
- Initial multi-language support.

### v1.0.0 (2025-05-16) _(Tyson only)_
- **Initial Release (Tyson)**: Basic welcome interface with Calamares integration.
- CHROOT recovery tools and GParted integration.
- Multi-language support (8 languages) and hardware detection.

---

**Soplos Welcome Live 2.0** - The professional tool for Soplos Linux Live environment
