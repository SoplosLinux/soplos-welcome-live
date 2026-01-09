# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [2.0.1] - 2026-01-09

### 📚 Documentation
- **Man Page**: Added complete manual page (`docs/soplos-welcome-live.1`) with standard sections (NAME, SYNOPSIS, DESCRIPTION, OPTIONS, FILES, AUTHOR, COPYRIGHT, SEE ALSO).
- **Debian Copyright**: Added machine-readable copyright file (`debian/copyright`) following Debian 1.0 format with full GPL-3.0+ license block.

## [2.0.0] - 2025-12-07

### 🏗️ Architecture Rewrite
- Complete rewrite with modular architecture matching Soplos Welcome 2.0
- Professional project structure: Core, UI, Config, Utils layers
- Separation of concerns for maintainability

### 🖥️ Universal Desktop Support
- Single unified codebase for all desktop environments
- **XFCE (Tyron)**: Full support with NumLock integration
- **KDE Plasma (Tyson)**: Native Plasma integration
- **GNOME (Boro)**: Complete GNOME compatibility
- Smart desktop environment detection

### 🔧 Display Protocol Compatibility
- Complete X11 support
- Full Wayland compatibility
- Automatic protocol detection

### 🌍 Internationalization Overhaul
- Migrated to GNU Gettext standard (.po/.mo files)
- 8 languages at 100%: ES, EN, FR, DE, PT, IT, RO, RU
- Keyboard mnemonics in all languages
- Automatic locale detection

### 🛠️ Enhanced CHROOT Recovery
- Improved partition detection (universal hardware/VM support)
- Full BTRFS subvolume support with hierarchical selection
- GParted integration for disk management
- Robust filesystem validation

### 🩹 Patch - 2025-12-08
- Normalized application switch styling across desktop themes (fixed oval/stretch issue in Live images)
- Applied focused CSS overrides and ensured application CSS has USER priority so widgets render consistently
- Prepared updated screenshots for the welcome flow (replace legacy images before packaging)

### 🩹 Patch - 2025-12-09
- Removed KDE bookmark remapping logic from the language changer; the language switcher now deletes `~/.local/share/user-places.xbel` before restarting the session so KDE/Dolphin regenerates localized bookmarks. This simplifies behavior in live images and avoids incorrect localized paths. (No backups; intended for live environments, documented as 2.0 preproduction.)
 - GNOME/Wayland display fixes:
	 - Robust GNOME Wayland resolution handling: improved D-Bus parsing of `GetCurrentState` with defensive unpacking and selection of logical monitors.
	 - Added GDK-first fallback to reliably detect the actual screen geometry at startup (avoids incorrect VM/guest mode detection such as `RHT`).
	 - Safer `ApplyMonitorsConfig` usage: pass empty property maps for monitor props to satisfy D-Bus signatures, increased D-Bus timeout to 5s, and prefer temporary apply method in Live ISOs.
	 - Selects best refresh rate when multiple modes match the requested resolution; improved error handling and debug logging.
	 - Selects best refresh rate when multiple modes match the requested resolution; improved error handling and debug logging.

### Patch - 2025-12-10
- **Legacy Chroot Restoration**: Re-implemented the robust 2.0-style chroot logic with `safe_umount`, strict mounting sequence, and validation.
- **Cross-DE Terminal Support**: Implemented smart terminal detection for Chroot (Kitty/Xfce4-terminal for XFCE, Konsole for Plasma, Gnome-terminal/Ptyxis for GNOME).
- **Resolution Persistence**: Implemented session persistence for resolution changes.
  - **GNOME Wayland**: Switched to persistent `ApplyMonitorsConfig` method.
  - **XFCE X11**: Added autostart script generation (`soplos-resolution.desktop`).
- **UI Improvements**: Restored the progress dialog detailed view and window footer buttons to match the legacy experience.
- **System Validation**: Re-enabled strict system validation checks to ensure only valid Linux systems are chrooted.
- **Translation Overhaul**: Complete quality review and refinement of all 8 languages (ES, EN, DE, FR, PT, IT, RO, RU) ensuring 100% string coverage, "natural" phrasing, and UI-conciseness.

---

## [1.1.2] - 2025-11-29

### ✨ Changed
- Universal disk detection in CHROOT: removed restrictive lsblk filter
- Now detects all disk types on any hardware and VM
- Fixed indentation errors in core/chroot_operations.py
- Added debug message showing detected disks

## [1.1.1] - 2025-09-08

### ✨ Changed
- Updated links in the welcome tab buttons

## [1.1.0] - 2025-08-02

### ✨ Changed
- Complete internationalization refactor: dictionaries split into 8 files
- Fixed all BTRFS partition mounting and subvolume selection issues

## [1.0.9] - 2025-07-27

### ✨ Changed
- New program icon for better Soplos Linux branding integration

## [1.0.8] - 2025-07-27

### ✨ Added
- Advanced partition and BTRFS subvolume detection
- Full /home mounting support (partition or subvolume)
- Improved recovery flow robustness
- Multiple terminal compatibility

## [1.0.6] - 2025-07-18

### 🛠️ Improved
- Metainfo update for AppStream/DEP-11 compliance

## [1.0.5] - 2025-07-10

### 🌍 Added
- Full BTRFS subvolume support in CHROOT recovery
- Complete internationalization in 8 languages with mnemonics

## [1.0.4] - 2024-01-28

### ✨ New
- Advanced CHROOT functionality with intelligent partition detection
- NumLock management integration
- Automatic XDG folder migration
- Real-time Python cache cleanup
- GParted integration

## [1.0.0] - 2024-01-27

### 🎉 Initial Release
- Basic welcome interface
- CHROOT functionality
- Multi-language support

---

## Author

Developed by **Sergi Perich**  
Website: https://soplos.org  
Contact: info@soploslinux.com

## Contributing

- **Issues**: https://github.com/SoplosLinux/soplos-welcome-live/issues
- **Email**: info@soploslinux.com

## Support

- **Documentation**: https://soplos.org
- **Community**: https://soplos.org/forums/
