"""
Main window for Soplos Welcome Live.
Simple single-view interface for Live ISO environment.
Uses same visual style as Soplos Welcome 2.0 - centered layout.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf

import os
import subprocess
import webbrowser
import time
import threading
import socket


from pathlib import Path



from core.i18n_manager import _
from core import __version__
from config.paths import LOGO_PATH, SLIDE_PATH, ASSETS_DIR
from ui import CSS_CLASSES
from utils.autostart import AutostartManager
from utils.numlockx_manager import NumlockxManager
from utils.display_manager import DisplayManager


class MainWindow(Gtk.ApplicationWindow):
    """
    Main application window for Soplos Welcome Live.
    Simple centered interface without tabs, similar to Welcome 2.0 style.
    """
    
    # Language configurations
    LANGUAGES = {
        'Español': {'code': 'es', 'locale': 'es_ES.UTF-8', 'layout': 'es'},
        'English': {'code': 'en', 'locale': 'en_US.UTF-8', 'layout': 'us'},
        'Português': {'code': 'pt', 'locale': 'pt_PT.UTF-8', 'layout': 'pt'},
        'Français': {'code': 'fr', 'locale': 'fr_FR.UTF-8', 'layout': 'fr'},
        'Deutsch': {'code': 'de', 'locale': 'de_DE.UTF-8', 'layout': 'de'},
        'Italiano': {'code': 'it', 'locale': 'it_IT.UTF-8', 'layout': 'it'},
        'Română': {'code': 'ro', 'locale': 'ro_RO.UTF-8', 'layout': 'ro'},
        'Русский': {'code': 'ru', 'locale': 'ru_RU.UTF-8', 'layout': 'ru'}
    }
    
    def __init__(self, application, environment_detector, theme_manager, i18n_manager):
        """Initialize the main window."""
        super().__init__(application=application)
        
        # Store references to managers
        self.application = application
        self.environment_detector = environment_detector
        self.theme_manager = theme_manager
        self.i18n_manager = i18n_manager
        
        # Get current language
        self.current_lang = i18n_manager.current_language
        
        # Get edition info
        self.edition_name = environment_detector.get_edition_name()
        self.desktop = environment_detector.desktop_environment
        
        # Autostart manager
        self.autostart_manager = AutostartManager()
        
        # Display manager
        self.display_manager = DisplayManager()
        
        # Window properties
        self.set_title(_("Soplos Welcome Live"))
        self.set_default_size(850, 600)  # Taller to fit all content
        self.set_size_request(800, 550)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(True)

        # Create HeaderBar (CSD) to match Welcome 2.0 visual style
        self._create_header_bar()
        
        # Apply CSS class and ID for specificity
        self.get_style_context().add_class(CSS_CLASSES['window'])
        # Also add legacy class used by Soplos Welcome themes so CSS from
        # the original Welcome (2.0) applies without requiring CSS edits.
        self.get_style_context().add_class('soplos-welcome-window')
        self.set_name("main-window")

        # Note: previously we added a USER-priority CSS provider here
        # to normalize switches. Removed to let the system theme fully
        # control switch appearance (per user request).
        
        # Window icon
        self._set_window_icon()

        # Key press handler (all desktops)
        self.connect('key-press-event', self._on_key_press)

        # Create UI
        self._create_ui()

        # Fade-in animation on startup
        self.set_opacity(0.0)
        self._fade_step = 0
        GLib.timeout_add(30, self._fade_in)

        # Internet connectivity indicator
        self._start_connectivity_check()
    
    def _fade_in(self):
        """Animate window fade-in on startup."""
        self._fade_step += 1
        self.set_opacity(min(self._fade_step / 8.0, 1.0))
        if self._fade_step < 8:
            return True  # Continue
        return False  # Stop

    def _start_connectivity_check(self):
        """Start background internet connectivity checks, repeated every 15 s."""
        self._check_connectivity_async()
        GLib.timeout_add_seconds(15, self._schedule_connectivity_check)

    def _schedule_connectivity_check(self):
        """Called by GLib timer to trigger a new connectivity check."""
        self._check_connectivity_async()
        return True  # Keep repeating

    def _check_connectivity_async(self):
        """Launch a daemon thread to test connectivity without blocking the UI."""
        def check():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(3)
                s.connect(("8.8.8.8", 53))
                s.close()
                connected = True
            except Exception:
                connected = False
            GLib.idle_add(self._update_net_indicator, connected)
        threading.Thread(target=check, daemon=True).start()

    def _update_net_indicator(self, connected):
        """Update the network indicator label in the UI thread."""
        if connected:
            self.net_indicator.set_markup('<span foreground="#4CAF50">●</span>')
            self.net_indicator.set_tooltip_text(_("Internet connection available"))
        else:
            self.net_indicator.set_markup('<span foreground="#F44336">●</span>')
            self.net_indicator.set_tooltip_text(_("No internet connection"))
        return False  # Remove from GLib.idle_add queue

    def _create_header_bar(self):
        """
        Create HeaderBar (CSD) for GNOME, but use native decorations (SSD) 
        for XFCE and KDE to avoid double headers or missing controls.
        """
        # Detect environment safely
        desktop_env = 'unknown'
        try:
             if self.desktop:
                desktop_env = getattr(self.desktop, 'value', str(self.desktop)).lower()
        except:
            pass
            
        # XFCE and KDE/Plasma work best with native window decorations (SSD)
        if desktop_env in ['xfce', 'kde', 'plasma']:
            return

        # For GNOME and others, use Client-Side Decorations (CSD)
        header = Gtk.HeaderBar()
        header.set_show_close_button(True)
        header.set_title(_("Soplos Welcome Live"))
        
        # Explicit decoration layout to ensure controls are visible
        header.set_decoration_layout("menu:minimize,maximize,close")

        # Apply strict styling class
        header.get_style_context().add_class('titlebar')
        
        # CRITICAL: Show the header bar to ensure it renders
        header.show_all()

        self.set_titlebar(header)
        self.header = header

        # Connect signals
        self.connect('delete-event', self._on_delete_event)

        # Ensure window can take focus immediately
        self.set_can_focus(True)
        self.set_focus_visible(False)
    
    def _set_window_icon(self):
        """Set the window icon."""
        try:
            if LOGO_PATH.exists():
                self.set_icon_from_file(str(LOGO_PATH))
            else:
                self.set_icon_name('system-software-install')
        except Exception as e:
            print(f"Error setting window icon: {e}")
    


    def _create_ui(self):
        """Create the main user interface - centered layout like Welcome 2.0."""
        # Ensure progress bar style is loaded

        
        # Main vertical container - store reference for progress bar
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.main_box.get_style_context().add_class(CSS_CLASSES['content'])
        self.add(self.main_box)
        
        # Main body frame to separate content from footer (like Welcome 2.0 Notebook)
        body_frame = Gtk.Frame()
        self.main_box.pack_start(body_frame, True, True, 0)
        
        # Content box - centered (no scroll, tighter spacing)
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        content_box.set_valign(Gtk.Align.CENTER)
        content_box.set_halign(Gtk.Align.CENTER)
        content_box.set_margin_top(15)
        content_box.set_margin_bottom(10)
        content_box.set_margin_start(30)
        content_box.set_margin_end(30)
        
        body_frame.add(content_box)
        
        # Logo - centered and large
        self._create_logo(content_box)
        
        # Title (use markup to match Welcome 2.0 sizing)
        title_label = Gtk.Label()
        title_label.set_markup(f'<span size="20000" weight="bold">{_("Welcome to Soplos Linux")}</span>')
        title_label.get_style_context().add_class(CSS_CLASSES['welcome_title'])
        title_label.set_justify(Gtk.Justification.CENTER)
        title_label.set_halign(Gtk.Align.CENTER)
        content_box.pack_start(title_label, False, False, 0)
        
        # Subtitle (match Welcome 2.0 markup sizing)
        subtitle_label = Gtk.Label()
        subtitle_label.set_markup(f'<span size="12000">{_('Live Session')} - {self.edition_name}</span>')
        subtitle_label.get_style_context().add_class(CSS_CLASSES['welcome_subtitle'])
        subtitle_label.set_justify(Gtk.Justification.CENTER)
        subtitle_label.set_halign(Gtk.Align.CENTER)
        content_box.pack_start(subtitle_label, False, False, 0)
        
        # Description
        desc_label = Gtk.Label()
        desc_label.set_text(_("Explore the system, install Soplos Linux, or rescue an existing installation."))
        desc_label.set_line_wrap(True)
        desc_label.set_max_width_chars(70)
        desc_label.set_justify(Gtk.Justification.CENTER)
        desc_label.set_halign(Gtk.Align.CENTER)
        desc_label.set_margin_top(10)
        content_box.pack_start(desc_label, False, False, 0)
        
        # Features list with icons (like Welcome 2.0)
        self._create_features_list(content_box)
        
        # Main action buttons
        self._create_action_buttons(content_box)
        
        # Link buttons row
        self._create_link_buttons(content_box)
        
        # Settings row (language, autostart, numlock)
        self._create_settings_row(content_box)
        
        # Progress area with Revealer (Welcome 2.0 style)
        self.progress_revealer = Gtk.Revealer()
        self.progress_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)
        
        progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        progress_box.set_margin_start(60)
        progress_box.set_margin_end(60)
        progress_box.set_margin_bottom(15)
        
        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.get_style_context().add_class('soplos-progress-bar')
        self.progress_bar.set_show_text(True)
        progress_box.pack_start(self.progress_bar, False, False, 0)
        
        # Progress label
        self.progress_label = Gtk.Label()
        self.progress_label.set_text(_("Ready"))
        self.progress_label.get_style_context().add_class(CSS_CLASSES['status_label'])
        progress_box.pack_start(self.progress_label, False, False, 0)
        
        self.progress_revealer.add(progress_box)
        self.progress_revealer.set_reveal_child(False)
        self.main_box.pack_end(self.progress_revealer, False, True, 0)
        
        # Status bar at bottom
        self._create_status_bar(self.main_box)
        
        # CRITICAL: Show all widgets
        self.main_box.show_all()
    
    def _create_logo(self, parent):
        """Create centered logo."""
        # Try to load main Soplos logo
        logo_paths = [
            ASSETS_DIR / 'icons' / 'soplos-logo.png',
            ASSETS_DIR / 'icons' / 'org.soplos.welcomelive.png',
            LOGO_PATH,
            Path('/usr/share/icons/hicolor/128x128/apps/soplos-welcome-live.png')
        ]
        
        for logo_path in logo_paths:
            if logo_path.exists():
                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                        filename=str(logo_path),
                        width=128,
                        height=128,
                        preserve_aspect_ratio=True
                    )
                    logo_image = Gtk.Image.new_from_pixbuf(pixbuf)
                    logo_image.set_margin_bottom(10)
                    parent.pack_start(logo_image, False, False, 0)
                    return
                except Exception as e:
                    print(f"Error loading logo from {logo_path}: {e}")
        
        # Fallback to icon
        logo_image = Gtk.Image.new_from_icon_name('system-software-install', Gtk.IconSize.DIALOG)
        logo_image.set_pixel_size(128)
        parent.pack_start(logo_image, False, False, 0)
    
    def _create_features_list(self, parent):
        """Create features list with icons like Welcome 2.0."""
        # Frame for features
        features_frame = Gtk.Frame()
        features_frame.set_label(_("Available options:"))
        features_frame.set_label_align(0.5, 0.5)
        features_frame.set_margin_top(15)
        features_frame.set_margin_bottom(10)
        # Using flat style if available or relying on theme
        parent.pack_start(features_frame, False, False, 0)
        
        # Features Grid
        grid = Gtk.Grid()
        grid.set_column_spacing(15)
        grid.set_row_spacing(10)
        grid.set_margin_top(10)
        grid.set_margin_bottom(10)
        grid.set_margin_start(20)
        grid.set_margin_end(20)
        grid.set_halign(Gtk.Align.CENTER)
        features_frame.add(grid)
        
        # Features
        features = [
            ("system-software-install", _("Install Soplos Linux on your computer"),
             _("Launch the Calamares installer to install Soplos Linux on your hard drive.")),
            ("drive-harddisk", _("Rescue an existing installation via CHROOT"),
             _("Mount and chroot into an existing Linux installation to repair it, reset passwords or fix the bootloader.")),
            ("preferences-desktop-locale", _("Change system language on the fly"),
             _("Change the system language and keyboard layout. The session will restart automatically to apply the changes.")),
        ]

        # Add NumLock feature for Tyron
        if self._is_tyron():
            features.append(("input-keyboard", _("Toggle NumLock for keyboards"),
                             _("Enable or disable NumLock activation on the installed system. Recommended to disable on laptops without a numeric keypad.")))

        for i, (icon_name, text, tooltip) in enumerate(features):
            # Icon
            icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.LARGE_TOOLBAR)
            icon.set_halign(Gtk.Align.CENTER)
            icon.set_valign(Gtk.Align.CENTER)
            icon.set_tooltip_text(tooltip)
            grid.attach(icon, 0, i, 1, 1)

            # Label
            label = Gtk.Label(label=f"• {text}")
            label.set_halign(Gtk.Align.START)
            label.set_valign(Gtk.Align.CENTER)
            label.set_tooltip_text(tooltip)
            grid.attach(label, 1, i, 1, 1)
    
    def _create_action_buttons(self, parent):
        """Create main action buttons."""
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.set_margin_top(15)
        parent.pack_start(button_box, False, False, 0)
        
        # Install button (primary action)
        install_btn = Gtk.Button()
        install_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        install_icon = Gtk.Image.new_from_icon_name('system-software-install', Gtk.IconSize.BUTTON)
        install_label = Gtk.Label(label=_("Install Soplos Linux"))
        install_box.pack_start(install_icon, False, False, 0)
        install_box.pack_start(install_label, False, False, 0)
        install_btn.add(install_box)
        install_btn.get_style_context().add_class(CSS_CLASSES['button_install'])
        install_btn.get_style_context().add_class('suggested-action')
        install_btn.set_tooltip_text(_("Launch the Calamares installer to install Soplos Linux on your hard drive."))
        install_btn.connect("clicked", self._on_install_clicked)
        install_btn.set_size_request(180, 45)
        button_box.pack_start(install_btn, False, False, 0)
        self.install_btn = install_btn
        
        # System Rescue button
        rescue_btn = Gtk.Button()
        rescue_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        rescue_icon = Gtk.Image.new_from_icon_name('drive-harddisk', Gtk.IconSize.BUTTON)
        rescue_label = Gtk.Label(label=_("System Rescue"))
        rescue_box.pack_start(rescue_icon, False, False, 0)
        rescue_box.pack_start(rescue_label, False, False, 0)
        rescue_btn.add(rescue_box)
        rescue_btn.get_style_context().add_class(CSS_CLASSES['button_secondary'])
        rescue_btn.set_tooltip_text(_("Mount and repair an existing installation"))
        rescue_btn.connect("clicked", self._on_chroot_clicked)
        rescue_btn.set_size_request(180, 45)
        button_box.pack_start(rescue_btn, False, False, 0)

        # GParted button
        gparted_btn = Gtk.Button()
        gparted_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        gparted_icon = Gtk.Image.new_from_icon_name('drive-harddisk-ieee1394', Gtk.IconSize.BUTTON)
        gparted_label = Gtk.Label(label=_("GParted"))
        gparted_box.pack_start(gparted_icon, False, False, 0)
        gparted_box.pack_start(gparted_label, False, False, 0)
        gparted_btn.add(gparted_box)
        gparted_btn.get_style_context().add_class(CSS_CLASSES['button_secondary'])
        gparted_btn.set_tooltip_text(_("Open GParted to manage disk partitions before installing."))
        gparted_btn.connect("clicked", self._on_gparted_clicked)
        gparted_btn.set_size_request(180, 45)
        button_box.pack_start(gparted_btn, False, False, 0)

        # Hardware info button
        hwinfo_btn = Gtk.Button()
        hwinfo_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        hwinfo_icon = Gtk.Image.new_from_icon_name('computer', Gtk.IconSize.BUTTON)
        hwinfo_label = Gtk.Label(label=_("Hardware Info"))
        hwinfo_box.pack_start(hwinfo_icon, False, False, 0)
        hwinfo_box.pack_start(hwinfo_label, False, False, 0)
        hwinfo_btn.add(hwinfo_box)
        hwinfo_btn.get_style_context().add_class(CSS_CLASSES['button_secondary'])
        hwinfo_btn.set_tooltip_text(_("Show information about this system's hardware."))
        hwinfo_btn.connect("clicked", self._on_hwinfo_clicked)
        hwinfo_btn.set_size_request(180, 45)
        button_box.pack_start(hwinfo_btn, False, False, 0)

    def _create_link_buttons(self, parent):
        """Create link buttons row with icons like Welcome 2.0."""
        links_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        links_box.set_halign(Gtk.Align.CENTER)
        links_box.set_margin_top(15)
        parent.pack_start(links_box, False, False, 0)
        
        links = [
            ("web-browser", _("Web"), "https://soplos.org",
             _("Visit the official Soplos Linux website.")),
            ("internet-group-chat", _("Forums"), "https://soplos.org/forums/",
             _("Get help and connect with the Soplos community on the forums.")),
            ("help-browser", _("Wiki"), "https://soplos.org/wiki/",
             _("Browse the Soplos Linux documentation and guides.")),
            ("emblem-favorite", _("Donate"), "https://www.paypal.com/paypalme/isubdes",
             _("Support the development of Soplos Linux with a donation."))
        ]

        for icon_name, label, url, tooltip in links:
            btn = Gtk.Button()
            btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            btn_box.set_halign(Gtk.Align.CENTER)
            icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
            text = Gtk.Label(label=label)
            btn_box.pack_start(icon, False, False, 0)
            btn_box.pack_start(text, False, False, 0)
            btn.add(btn_box)
            btn.get_style_context().add_class(CSS_CLASSES['link_button'])
            btn.set_tooltip_text(tooltip)
            btn.connect("clicked", lambda x, u=url: webbrowser.open(u))
            btn.set_size_request(95, 40)  # Uniform width
            links_box.pack_start(btn, True, True, 0)  # Expand to fill
    
    def _create_settings_row(self, parent):
        """Create settings row (language, autostart, numlock)."""
        settings_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        settings_box.set_halign(Gtk.Align.CENTER)
        settings_box.set_margin_top(20)
        parent.pack_start(settings_box, False, False, 0)
        
        # Language selector
        lang_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        lang_icon = Gtk.Image.new_from_icon_name('preferences-desktop-locale', Gtk.IconSize.BUTTON)
        lang_icon.set_tooltip_text(_("Select the system language and keyboard layout."))
        lang_box.pack_start(lang_icon, False, False, 0)

        self.lang_combo = Gtk.ComboBoxText()
        current_index = 0
        for i, (lang_name, config) in enumerate(self.LANGUAGES.items()):
            self.lang_combo.append_text(lang_name)
            if config['code'] == self.current_lang:
                current_index = i
        self.lang_combo.set_active(current_index)
        self.lang_combo.set_tooltip_text(_("Select the system language and keyboard layout."))
        self.lang_combo.connect("changed", self._on_language_changed)
        lang_box.pack_start(self.lang_combo, False, False, 0)
        settings_box.pack_start(lang_box, False, False, 0)
        
        # Separator
        sep1 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        settings_box.pack_start(sep1, False, False, 0)

        # Resolution selector
        res_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        res_icon = Gtk.Image.new_from_icon_name('video-display', Gtk.IconSize.BUTTON)
        res_icon.set_tooltip_text(_("Change the screen resolution for this live session."))
        res_box.pack_start(res_icon, False, False, 0)

        self.res_combo = Gtk.ComboBoxText()
        resolutions = self.display_manager.get_resolutions()
        for res in resolutions:
            self.res_combo.append_text(res)
        
        if resolutions:
            # Try to select current resolution
            default_index = 0
            current_res = self.display_manager.get_current_resolution()
            
            if current_res and current_res in resolutions:
                 for i, res in enumerate(resolutions):
                     if res == current_res:
                         default_index = i
                         break
            
            self.res_combo.set_active(default_index)
            
        self.res_combo.set_tooltip_text(_("Change the screen resolution for this live session."))
        self.res_combo.connect("changed", self._on_resolution_changed)
        res_box.pack_start(self.res_combo, False, False, 0)
        settings_box.pack_start(res_box, False, False, 0)

        # Separator 2
        sep2 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        settings_box.pack_start(sep2, False, False, 0)
        
        # Autostart switch
        autostart_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        autostart_label = Gtk.Label(label=_("Show at startup"))
        autostart_label.set_tooltip_text(_("Show this welcome screen automatically when the live session starts."))
        autostart_box.pack_start(autostart_label, False, False, 0)

        self.autostart_switch = Gtk.Switch()
        self.autostart_switch.set_active(self.autostart_manager.is_enabled())
        self.autostart_switch.set_tooltip_text(_("Show this welcome screen automatically when the live session starts."))
        self.autostart_switch.connect("notify::active", self._on_autostart_toggled)
        # Force a compact size and center alignment to avoid vertical stretching
        try:
            self.autostart_switch.set_size_request(36, 22)
            self.autostart_switch.set_valign(Gtk.Align.CENTER)
        except Exception:
            pass
        autostart_box.pack_start(self.autostart_switch, False, False, 0)
        settings_box.pack_start(autostart_box, False, False, 0)
        
        # NumLock switch - ONLY for Tyron (XFCE)
        if self._is_tyron():
            sep3 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
            settings_box.pack_start(sep3, False, False, 0)
            
            numlock_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            numlock_label = Gtk.Label(label=_("NumLock on install"))
            numlock_box.pack_start(numlock_label, False, False, 0)
            
            # Initialize NumLock manager
            self.numlock_manager = NumlockxManager()
            self.numlock_switch = Gtk.Switch()
            self.numlock_switch.set_active(self.numlock_manager.is_enabled())
            self.numlock_switch.set_tooltip_text(_("Enable/disable NumLock activation in installed system"))
            self.numlock_switch.connect("notify::active", self._on_numlock_toggled)
            try:
                self.numlock_switch.set_size_request(36, 22)
                self.numlock_switch.set_valign(Gtk.Align.CENTER)
            except Exception:
                pass
            numlock_box.pack_start(self.numlock_switch, False, False, 0)
            settings_box.pack_start(numlock_box, False, False, 0)
    
    def _create_status_bar(self, parent):
        """Create status bar at the bottom."""
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        status_box.set_margin_start(15)
        status_box.set_margin_end(15)
        status_box.set_margin_top(8)
        status_box.set_margin_bottom(8)
        
        # Left: System info
        env_info = self.environment_detector.detect_all()
        desktop_name = env_info['desktop_environment'].upper()
        protocol_name = env_info['display_protocol'].upper()
        
        status_text = f"{desktop_name}  ·  {protocol_name}"
        status_label = Gtk.Label(label=status_text)
        status_label.set_halign(Gtk.Align.START)
        status_label.get_style_context().add_class(CSS_CLASSES['status_label'])
        status_box.pack_start(status_label, False, False, 0)
        
        # Right: Version
        version_label = Gtk.Label(label=f"v{__version__}")
        version_label.set_halign(Gtk.Align.END)
        version_label.get_style_context().add_class('dim-label')
        status_box.pack_end(version_label, False, False, 0)

        # Right: Internet indicator (left of version)
        self.net_indicator = Gtk.Label()
        self.net_indicator.set_markup('<span foreground="#888888">●</span>')
        self.net_indicator.set_tooltip_text(_("Checking internet connection..."))
        status_box.pack_end(self.net_indicator, False, False, 0)

        parent.pack_end(status_box, False, False, 0)

    # ==================== Helper Methods ====================
    
    def _is_tyron(self) -> bool:
        """Check if running on Tyron (XFCE) edition."""
        from core.environment import SoplosEdition, DesktopEnvironment
        return (self.environment_detector.edition == SoplosEdition.TYRON or 
                self.environment_detector.desktop_environment == DesktopEnvironment.XFCE)
    
    # ==================== Event Handlers ====================
    
    def _on_autostart_toggled(self, switch, gparam):
        """Handle autostart switch toggle."""
        if switch.get_active():
            self.autostart_manager.enable()
        else:
            self.autostart_manager.disable()
    
    def _on_numlock_toggled(self, switch, gparam):
        """Handle NumLock switch toggle - configures Calamares for installation."""
        try:
            if switch.get_active():
                self.numlock_manager.enable_numlockx()
                self._show_message(
                    _("NumLock Enabled"),
                    _("NumLock will be activated automatically in the installed system."),
                    Gtk.MessageType.INFO
                )
            else:
                self.numlock_manager.disable_numlockx()
                self._show_message(
                    _("NumLock Disabled"),
                    _("NumLock will NOT be activated in the installed system.\n"
                      "Recommended for laptops without numeric keypad."),
                    Gtk.MessageType.INFO
                )
        except Exception as e:
            self._show_message(_("Error"), str(e), Gtk.MessageType.ERROR)

    def _on_resolution_changed(self, combo):
        """Handle resolution change."""
        resolution = combo.get_active_text()
        if not resolution:
            return
            
        try:
            success = self.display_manager.set_resolution(resolution)
            if not success:
                # show warning but don't block
                print(f"Failed to set resolution {resolution}")
        except Exception as e:
             print(f"Error changing resolution: {e}")
    
    def _on_language_changed(self, combo):
        """Handle language change synchronously with event pumping (Tyson Logic)."""
        lang_name = combo.get_active_text()
        if lang_name not in self.LANGUAGES:
            return
        
        lang_config = self.LANGUAGES[lang_name]
        lang_code = lang_config['code']
        
        # Check current language
        # Use I18nManager's detected language, ensuring sync with UI state
        current_code = self.i18n_manager.current_language
        if current_code == lang_code:
            return
        
        # Show progress area (Revealer) - Force visibility for XFCE
        self.progress_revealer.set_visible(True)
        self.progress_revealer.set_reveal_child(True)
        self.progress_bar.set_fraction(0.0)
        self.progress_label.set_text(_("Configuring language..."))
        
        # Disable inputs
        self.lang_combo.set_sensitive(False)
        if hasattr(self, 'install_btn'):
            self.install_btn.set_sensitive(False)
            
        # Process events immediately to update UI
        # Process events to allow animation to start and complete (approx 350ms)
        start_time = time.time()
        while time.time() - start_time < 0.35:
            while Gtk.events_pending():
                Gtk.main_iteration()

        try:
            from utils.language_changer import get_language_changer
            changer = get_language_changer()
            
            locale = changer.LOCALE_CODES[lang_code]
            layout = changer.KEYBOARD_LAYOUTS.get(lang_code, 'us')
            
            # Helper for synchronous UI updates
            def update_ui(fraction, text):
                self.progress_bar.set_fraction(fraction)
                self.progress_label.set_text(text)
                self.progress_bar.set_text(f"{int(fraction * 100)}%")
                # Pump events to keep UI responsive (Tyson logic)
                while Gtk.events_pending():
                    Gtk.main_iteration()

            # Step 1: System locale
            update_ui(0.2, _("Configuring system locale..."))
            changer._configure_system_locale(locale, layout, os.environ.get('USER', 'liveuser'))
            
            # Step 2: User settings
            update_ui(0.4, _("Applying user settings..."))
            changer._apply_user_settings(lang_code, locale, layout)
            
            # Step 3: XDG directories
            update_ui(0.6, _("Migrating directories..."))
            changer._migrate_xdg_directories(locale)
            # Step 4: GTK/XFCE bookmarks
            # Now supports both Nautilus (GNOME) and Thunar (XFCE)
            if changer.desktop.value in ['gnome', 'xfce']:
                changer._update_gtk_bookmarks()
            
            # Step 5: Restart session IMMEDIATELY
            update_ui(1.0, _("Restarting session..."))
            
            # Force all pending UI updates to complete NOW
            while Gtk.events_pending():
                Gtk.main_iteration()
            
            # CRITICAL: Call restart directly, NO GLib.timeout_add
            # The timeout keeps GTK alive during DM restart, causing deadlock
            from utils.language_changer import get_language_changer
            get_language_changer()._restart_display_manager()
            
        except Exception as e:
            print(f"Error changing language: {e}")
            self.progress_revealer.set_reveal_child(False)
            self.lang_combo.set_sensitive(True)
            if hasattr(self, 'install_btn'):
                self.install_btn.set_sensitive(True)
            self._show_message(_("Error"), str(e), Gtk.MessageType.ERROR)

    
    def _on_gparted_clicked(self, button):
        """Handle GParted button click - launch GParted partition editor."""
        try:
            subprocess.Popen(['pkexec', '/usr/sbin/gparted'],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
        except Exception as e:
            self._show_message(
                _("Error"),
                _("Could not open GParted: {error}").format(error=str(e)),
                Gtk.MessageType.ERROR
            )

    def _on_hwinfo_clicked(self, button):
        """Show a dialog with basic hardware information."""
        cpu = _("Unknown")
        ram = _("Unknown")
        disk = _("Unknown")

        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.startswith('model name'):
                        cpu = line.split(':', 1)[1].strip()
                        break
        except Exception:
            pass

        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemTotal'):
                        kb = int(line.split()[1])
                        ram = f"{kb / (1024 * 1024):.1f} GB"
                        break
        except Exception:
            pass

        try:
            result = subprocess.run(
                ['lsblk', '-d', '-o', 'NAME,SIZE,MODEL', '--noheadings'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                lines = [l.strip() for l in result.stdout.strip().splitlines()
                         if l and not any(x in l for x in ['loop', 'sr', 'rom'])]
                disk = '\n'.join(lines) if lines else _("Unknown")
        except Exception:
            pass

        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.CLOSE,
            text=_("Hardware Information")
        )
        dialog.format_secondary_markup(
            f"<b>{_('CPU')}:</b> {cpu}\n"
            f"<b>{_('RAM')}:</b> {ram}\n\n"
            f"<b>{_('Storage')}:</b>\n{disk}"
        )
        dialog.run()
        dialog.destroy()

    def _on_install_clicked(self, button):
        """Handle install button click - launch Calamares (like legacy: sudo, then close window)."""
        try:
            calamares_paths = [
                '/usr/bin/calamares',
                '/usr/local/bin/calamares',
                '/usr/bin/calamares-qt5'
            ]
            
            calamares_cmd = None
            for path in calamares_paths:
                if os.path.exists(path):
                    calamares_cmd = path
                    break
            
            if calamares_cmd:
                # Use sudo (not pkexec) like legacy - no authentication dialog needed
                subprocess.Popen(['sudo', 'env', 'QT_STYLE_OVERRIDE=fusion', calamares_cmd],
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
                print("Calamares installer launched")
                # Close window after 1 second (like legacy behavior)
                GLib.timeout_add(1000, lambda: self.destroy())
            else:
                self._show_message(
                    _("Installer Not Found"),
                    _("The Calamares installer could not be found.\n"
                      "Please install it or run the installation manually."),
                    Gtk.MessageType.ERROR
                )
        except Exception as e:
            self._show_message(_("Error"), str(e), Gtk.MessageType.ERROR)
    
    def _on_chroot_clicked(self, button):
        """Handle chroot button click - open system rescue window."""
        try:
            from ui.chroot_window import ChRootWindow
            chroot_window = ChRootWindow(self)
            chroot_window.show_all()
        except Exception as e:
            self._show_message(
                _("Error"),
                _("Could not open System Rescue: {error}").format(error=str(e)),
                Gtk.MessageType.ERROR
            )
    
    def _on_delete_event(self, widget, event):
        """Handle window close."""
        return False  # Allow close
    
    def show_about_dialog(self, *args):
        """Show About dialog."""
        from core import __version__
        dialog = Gtk.AboutDialog()
        dialog.set_transient_for(self)
        dialog.set_modal(True)
        dialog.set_program_name(_("Soplos Welcome Live"))
        dialog.set_version(__version__)
        dialog.set_comments(_("Welcome screen for Soplos Linux live sessions."))
        dialog.set_website("https://soplos.org")
        dialog.set_website_label("soplos.org")
        dialog.set_authors(["Sergi Perich <info@soploslinux.com>"])
        dialog.set_license_type(Gtk.License.GPL_3_0)
        icon_path = Path(__file__).parent.parent / 'assets' / 'icons' / '64x64' / 'org.soplos.welcomelive.png'
        if icon_path.exists():
            dialog.set_logo(GdkPixbuf.Pixbuf.new_from_file_at_scale(str(icon_path), 48, 48, True))
        _about_css = Gtk.CssProvider()
        _about_css.load_from_data(b"""
            dialog, messagedialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            dialog .background, messagedialog .background {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            dialog > box, messagedialog > box {
                background-color: #2b2b2b;
            }
            dialog label, messagedialog label {
                color: #ffffff;
            }
            dialog button, messagedialog button {
                background-image: none;
                background-color: #333333;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 6px 14px;
                min-height: 0;
                box-shadow: none;
            }
            dialog button:hover, messagedialog button:hover {
                background-color: #444444;
                border-color: #ff8800;
            }
            dialog stackswitcher button {
                border-radius: 100px;
                background-color: #2b2b2b;
                background-image: none;
                border: 1px solid #3c3c3c;
                font-weight: normal;
                padding: 4px 16px;
                min-height: 0;
                box-shadow: none;
                color: #ffffff;
            }
            dialog stackswitcher button:hover {
                background-color: #444444;
                border-color: #ff8800;
            }
            dialog stackswitcher button:checked {
                background-color: #444444;
                color: #ffffff;
            }
            dialog scrolledwindow,
            dialog scrolledwindow viewport {
                background-color: #2b2b2b;
                border-radius: 0;
            }
            dialog scrolledwindow textview,
            dialog scrolledwindow textview text {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            dialog headerbar, dialog .titlebar {
                background-color: #2b2b2b;
                border-bottom: 1px solid #3c3c3c;
                box-shadow: none;
            }
            dialog .dialog-action-area {
                background-color: #2b2b2b;
                border-top: 1px solid #3c3c3c;
            }
        """)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), _about_css,
            Gtk.STYLE_PROVIDER_PRIORITY_USER
        )
        dialog.run()
        dialog.destroy()

    def _on_key_press(self, widget, event):
        """Handle key press events."""
        keyval = event.keyval
        state = event.state

        # F1 - About dialog
        if keyval == Gdk.KEY_F1:
            self.show_about_dialog()
            return True

        # Check for Ctrl+Q to quit
        if state & Gdk.ModifierType.CONTROL_MASK:
            if keyval == Gdk.KEY_q or keyval == Gdk.KEY_Q:
                self.close()
                return True

        # Escape to close
        if keyval == Gdk.KEY_Escape:
            self.close()
            return True

        return False
    
    def _show_message(self, title: str, message: str, msg_type=Gtk.MessageType.INFO):
        """Show a message dialog."""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=msg_type,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
