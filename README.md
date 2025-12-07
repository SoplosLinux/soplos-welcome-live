# Soplos Welcome Live

[![License: GPL-3.0+](https://img.shields.io/badge/License-GPL--3.0%2B-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Version](https://img.shields.io/badge/version-2.0.0-green.svg)]()

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

### Welcome Screen
![Welcome Screen](https://raw.githubusercontent.com/SoplosLinux/soplos-welcome-live/main/assets/screenshots/screenshot1.png)

### CHROOT Recovery System
![CHROOT Recovery](https://raw.githubusercontent.com/SoplosLinux/soplos-welcome-live/main/assets/screenshots/screenshot2.png)

### BTRFS Subvolume Selection
![BTRFS Support](https://raw.githubusercontent.com/SoplosLinux/soplos-welcome-live/main/assets/screenshots/screenshot3.png)

### Terminal Session
![Terminal](https://raw.githubusercontent.com/SoplosLinux/soplos-welcome-live/main/assets/screenshots/screenshot4.png)

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

### v2.0.0 (2025-12-07)
- **Architecture Rewrite**: Modular design matching Soplos Welcome 2.0
- **Universal Desktop**: Single codebase for XFCE, Plasma, and GNOME
- **X11/Wayland**: Complete display protocol support
- **GNU Gettext**: Professional internationalization (8 languages)
- **Improved CHROOT**: Enhanced partition detection and BTRFS support

### v1.1.2 (2025-11-29)
- Universal disk detection in CHROOT (all hardware/VM types)
- Fixed indentation errors in core modules

### v1.1.1 (2025-09-08)
- Updated welcome tab links

### v1.1.0 (2025-08-02)
- Internationalization refactor (8 language files)
- Fixed BTRFS subvolume mounting issues

---

**Soplos Welcome Live 2.0** - The professional tool for Soplos Linux Live environment
