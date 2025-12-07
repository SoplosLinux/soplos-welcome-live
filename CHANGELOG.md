# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

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
