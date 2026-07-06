# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [2.0.2-5] - 2026-07-06

### Fixed
- Calamares is now launched with `QT_STYLE_OVERRIDE=fusion` on KDE Plasma to ensure correct rendering.

## [2.0.2-4] - 2026-06-24

### Fixed
- Language changer now detects the active display manager with `systemctl is-active` before restarting it, instead of always using the generic `display-manager.service` alias. On Tyson RC1 it restarts `plasmalogin` directly; on beta ISOs still on SDDM it restarts `sddm`; the generic alias is only used as a last resort. This resolves a bug on VirtualBox where the hot restart after language change caused plasmalogin to show the Breeze wallpaper instead of the Soplos one and triggered a ksplashqml crash cascade on login.

## [2.0.2-3] - 2026-06-23

### Fixed
- Ghostty is now the first-priority terminal in the CHROOT recovery terminal launcher for all three desktop environments (XFCE/Tyron, KDE/Tyson, GNOME/Boro), reflecting its role as the default terminal across all three distros.
- All 8 locale files updated to reflect the new terminal hint in the "no terminal found" error message.

## [2.0.2-2] - 2026-06-22

### Fixed
- Display manager restart fallback in language changer now tries `plasmalogin` before `sddm` on KDE, ensuring compatibility with both Tyson RC1 (PLM) and beta users still on SDDM.

## [2.0.2] - 2026-03-31

### ✨ Added
- **Fade-in animation**: Smooth window opacity transition on startup.
- **Tooltips**: Descriptive tooltips on all interactive elements (feature switches, action buttons, links, settings).
- **Internet connectivity indicator**: Live green/red dot in the status bar, checked every 15 seconds in a background thread.
- **Hardware Info button**: New button in the action bar opens a dialog showing CPU model, total RAM and connected storage devices.
- **GParted button**: Direct access to GParted from the main window action bar.
- **Guided Rescue Operations window**: After mounting the system in CHROOT, a new window provides guided operations:
  - Reset user password (via `chpasswd`).
  - Repair GRUB (auto-detects UEFI/BIOS, runs `grub-install` + `update-grub`).
  - Update GRUB (`update-grub`).
  - Regenerate initramfs (`dracut --regenerate-all --force`).
  - Terminal button to open an interactive shell (disables all other operations once clicked).
  - Output panel showing operation results in real time.

### 🔧 Fixed
- Removed incorrect positional partition auto-assignment fallback in the CHROOT partition detector; unidentified partitions now show "Select option" instead of a wrong automatic assignment.
- Fixed dark strip at the bottom of the partition selection dialog by replacing `action_area` buttons with a manual button box inside `content_area`.
- Removed misleading column headers from the partition assignment grid.

### 🌍 Translations
- All 8 languages (ES, EN, FR, DE, PT, IT, RO, RU) updated with new strings for all the above features.
- All `.po` files compiled to `.mo`.

## [2.0.1-1] - 2026-03-21

### ✨ Added
- **About dialog**: Press F1 or use the GNOME application menu to open the About dialog with version, author, license and website.

### 🔧 Fixed
- Duplicate `_initialize_theming()` call on startup eliminated.
- Inline imports moved to module level: `shutil`, `gettext`, `sys`, `traceback` in `application.py`.
- Duplicate `import os` inside `main()` function removed.
- Duplicate accessibility environment variable setup removed from `core/environment.py`.
- CSS theme priority changed from `PRIORITY_USER` to `PRIORITY_APPLICATION` so the About dialog CSS correctly overrides the application theme.
- About dialog now correctly styled: uniform dark background across headerbar, content and action area.

### 🧹 Cleanup
- Removed all `[DEBUG]` and `[DIAG]` print statements from `ui/main_window.py`.
- Removed `_debug_print_switches` diagnostic method from `ui/main_window.py`.
- Removed `DEBUG:` print statement from `core/chroot_operations.py`.
- Removed HeaderBar setup diagnostic prints.

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

## [1.1.6] - 2025-11-29 _(Tyson only)_

### ✨ Changed
- Removed restrictive `lsblk` filter so all disk types are detected (MMC, NVMe, USB, loop, etc.).
- Partition parsing switched to JSON (`lsblk -J`) with a robust text fallback for older systems.
- Improved BTRFS subvolume detection and added debug output for troubleshooting.
- Ported fixes from the Tyron tree and cleaned up indentation and error handling.

## [1.1.5] - 2025-09-08 _(Tyson only)_

### ✨ Changed
- Welcome tab URLs updated to soplos.org.

## [1.1.4] - 2025-08-02 _(Tyson only)_

### 🔧 Fixed
- Dictionary issues fixed and full i18n completed across all 8 languages.
- CHROOT function improved for systems with BTRFS subvolumes.

## [1.1.3] - 2025-08-02 _(Tyson only)_

### ✨ Changed
- Program icon updated to new design.
- Maintainer changed to Sergi Perich.

## [1.1.2] - 2025-11-29 _(Tyron only)_

### ✨ Changed
- Universal disk detection in CHROOT: removed restrictive `lsblk` filter; now detects all disk types on any hardware and VM (MMC, NVMe, USB, loop, etc.).
- Fixed indentation errors in `core/chroot_operations.py`.
- Added debug message showing detected disks for troubleshooting.

## [1.1.2] - 2025-07-27 _(Tyson only)_

### ✨ Added
- Advanced partition and BTRFS subvolume detection in the CHROOT environment.
- Full `/home` mounting support as a partition or BTRFS subvolume.
- Improved recovery flow robustness and compatibility with multiple terminals.

## [1.1.1] - 2025-09-08 _(Tyron only)_

### ✨ Changed
- Welcome tab URLs updated to soplos.org.

## [1.1.1] - 2025-07-18 _(Tyson only)_

### 🔧 Fixed
- Language detection and startup robustness improvements. Minor translation fixes.

## [1.1.0] - 2025-08-03 _(Tyron only)_

### ✨ Changed
- Complete i18n refactor: translation dictionaries split into 8 separate files for easier maintenance and language addition.
- BTRFS partition mounting and subvolume selection in CHROOT: all known issues and errors fixed.

## [1.1.0] - 2025-07-18 _(Tyson only)_

### ✨ Added
- Metainfo finalized to AppStream/DEP-11 standard.
- Program icons added in 48×48, 64×64 and 128×128 px.

## [1.0.9] - 2025-08-02 _(Tyron only)_

### ✨ Changed
- Program icon updated to new design for better Soplos Linux branding integration.

## [1.0.9] - 2025-07-15 _(Tyson only)_

### 🔧 Fixed
- Metainfo corrections for proper appearance in software centers (AppStream/Discover).

## [1.0.8] - 2025-05-08 _(Tyron only)_

### ✨ Added
- Advanced partition and BTRFS subvolume detection in the CHROOT environment.
- Full `/home` mounting support as a partition or BTRFS subvolume.
- Improved recovery flow robustness and compatibility with multiple terminals.
- Maintainer updated to Sergi Perich.

## [1.0.8] - 2025-07-13 _(Tyson only)_

### 🔧 Fixed
- Metainfo file fixed for proper visualization in Discover/AppStream.

## [1.0.7] - 2025-05-08 _(Tyron only)_

### ✨ Added
- Advanced partition and BTRFS subvolume detection in the CHROOT environment.
- Full `/home` mounting support as a partition or BTRFS subvolume.

_(Version bump on same day as 1.0.8 — content identical, immediately superseded.)_

## [1.0.7] - 2025-07-13 _(Tyson only)_

### ✨ Added
- Full BTRFS subvolume support in CHROOT recovery.
- Dictionary string corrections and review across all languages.
- NumLockX completely removed (not applicable to KDE Plasma).

## [1.0.6] - 2025-05-08 _(Tyron only)_

### 🛠️ Improved
- Metainfo updated for AppStream/DEP-11 compliance. Full validation for software centers. No functional changes.

## [1.0.6] - 2025-06-24 _(Tyson only)_

### ✨ Added
- AppStream integration: Application now visible in KDE Discover.

## [1.0.5] - 2025-05-07 _(Tyron only)_

### ✨ Added
- Full BTRFS subvolume support in CHROOT recovery.
- Complete i18n in 8 languages with keyboard mnemonics.
- Dictionary string corrections and review across all languages.

## [1.0.5] - 2025-06-20 _(Tyson only)_

### 🌍 Added
- Complete program internationalization. Label refinement to English for consistency.
- Minor bug fixes and general stability improvements.
- User interface optimizations and performance improvements.

## [1.0.4] - 2025-05-07 _(Tyron only)_

### ✨ Added
- Intelligent partition detection in CHROOT environment.
- NumLock management integration and automatic XDG folder migration on language change.
- Real-time Python cache cleanup and memory optimization.
- GParted integration and robust filesystem validation.
- Complete i18n in 8 languages.

## [1.0.3] - 2025-05-06 _(Tyron only)_

### 🛠️ Improved
- Locale configuration fixes and interface optimizations.

## [1.0.3] - 2025-06-14 _(Tyson only)_

### 🎉 Initial Release (Tyson)
- Basic welcome interface with Calamares integration, locale/keyboard configuration.
- CHROOT recovery tools and GParted integration.
- Multi-language support (8 languages) and hardware detection.
- NumLock activation toggle.

## [1.0.2] - 2025-05-05 _(Tyron only)_

### 🔧 Fixed
- CHROOT operation fixes and general stability improvements.
- Hardware detection improvements.

## [1.0.2] - 2025-06-09 _(Tyson only)_

### 🔧 Fixed
- Minor bug fixes and stability improvements.

## [1.0.1] - 2025-05-16 _(Tyron only)_

### 🔧 Fixed
- User interface improvements and configuration optimizations.

## [1.0.1] - 2025-05-28 _(Tyson only)_

### 🔧 Fixed
- Minor interface fixes and stability improvements.

## [1.0.0] - 2025-05-09 _(Tyron only)_

### 🎉 Initial Release (Tyron)
- Basic welcome interface for Soplos Linux Live.
- Basic CHROOT functionality for system recovery.
- Initial multi-language support.

## [1.0.0] - 2025-05-16 _(Tyson only)_

### 🎉 Initial Release (Tyson)
- Basic welcome interface with Calamares integration, locale/keyboard configuration.
- CHROOT recovery tools and GParted integration.
- Multi-language support (8 languages) and hardware detection.
- NumLock activation toggle.

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
