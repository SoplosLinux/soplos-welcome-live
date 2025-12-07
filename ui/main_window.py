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
        self.set_name("main-window")
        
        # Window icon
        self._set_window_icon()
        
        # Create UI
        self._create_ui()
    
    def _create_header_bar(self):
        """
        Create custom HeaderBar to match Welcome 2.0 style.
        Only used on GNOME to allow CSD integration.
        On XFCE/KDE, we rely on native Server-Side Decorations (SSD).
        """
        # Check environment - only use CSD on GNOME
        is_gnome = False
        # Only create HeaderBar if we are on GNOME
        # Debug detection
        print(f"HeaderBar check: Detected Desktop = {self.desktop.value}")
        
        if self.desktop.value != 'gnome':
            print("Using native window decorations (SSD)")
            return

        print("Creating Client-Side Decorations (CSD) for GNOME")
        header = Gtk.HeaderBar()
        header.set_show_close_button(True)
        # Force decoration layout on GNOME to ensure buttons appear
        header.set_decoration_layout("menu:minimize,maximize,close")
        header.set_title(_("Soplos Welcome Live"))
        
        # Apply strict styling class
        header.get_style_context().add_class('titlebar')
        
        self.set_titlebar(header)
        self.header = header
        
        # Connect signals
        # Connect signals
        self.connect('delete-event', self._on_delete_event)
        self.connect('key-press-event', self._on_key_press)
        
        # Ensure window can take focus immediately
        self.set_can_focus(True)
        self.set_focus_visible(False)
        
        print("Main window created successfully")
    
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
        
        # Content box - centered (no scroll, tighter spacing)
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        content_box.set_valign(Gtk.Align.CENTER)
        content_box.set_halign(Gtk.Align.CENTER)
        content_box.set_margin_top(15)
        content_box.set_margin_bottom(10)
        content_box.set_margin_start(30)
        content_box.set_margin_end(30)
        self.main_box.pack_start(content_box, True, True, 0)
        
        # Logo - centered and large
        self._create_logo(content_box)
        
        # Title
        title_label = Gtk.Label()
        title_label.set_text(_('Welcome to Soplos Linux'))
        title_label.get_style_context().add_class(CSS_CLASSES['welcome_title'])
        title_label.set_justify(Gtk.Justification.CENTER)
        content_box.pack_start(title_label, False, False, 0)
        
        # Subtitle
        subtitle_label = Gtk.Label()
        subtitle_label.set_text(f"{_('Live Session')} - {self.edition_name}")
        subtitle_label.get_style_context().add_class(CSS_CLASSES['welcome_subtitle'])
        subtitle_label.set_justify(Gtk.Justification.CENTER)
        content_box.pack_start(subtitle_label, False, False, 0)
        
        # Description
        desc_label = Gtk.Label()
        desc_label.set_text(_("Explore the system, install Soplos Linux, or rescue an existing installation."))
        desc_label.set_line_wrap(True)
        desc_label.set_max_width_chars(70)
        desc_label.set_justify(Gtk.Justification.CENTER)
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
        features_frame.set_margin_top(15)
        features_frame.set_margin_bottom(10)
        features_frame.set_margin_bottom(10)
        # features_frame.get_style_context().add_class(CSS_CLASSES['card']) # Removed to match Welcome 2.0 style
        parent.pack_start(features_frame, False, False, 0)
        
        features_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        features_box.set_margin_top(15)
        features_box.set_margin_bottom(15)
        features_box.set_margin_start(20)
        features_box.set_margin_end(20)
        features_frame.add(features_box)
        
        # Header
        header_label = Gtk.Label()
        header_label.set_text(_('Available options:'))
        header_label.get_style_context().add_class(CSS_CLASSES['features_header'])
        header_label.set_halign(Gtk.Align.START)
        features_box.pack_start(header_label, False, False, 0)
        
        # Features
        features = [
            ("system-software-install", _("Install Soplos Linux on your computer")),
            ("drive-harddisk", _("Rescue an existing installation via CHROOT")),
            ("preferences-desktop-locale", _("Change system language on the fly")),
        ]
        
        # Add NumLock feature for Tyron
        if self._is_tyron():
            features.append(("input-keyboard", _("Toggle NumLock for keyboards")))
        
        for icon_name, text in features:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            row.set_margin_start(10)
            
            icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.LARGE_TOOLBAR)
            row.pack_start(icon, False, False, 0)
            
            label = Gtk.Label(label=f"• {text}")
            label.set_halign(Gtk.Align.START)
            row.pack_start(label, False, False, 0)
            
            features_box.pack_start(row, False, False, 0)
    
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
        install_btn.connect("clicked", self._on_install_clicked)
        install_btn.set_size_request(200, 45)
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
    
    def _create_link_buttons(self, parent):
        """Create link buttons row with icons like Welcome 2.0."""
        links_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        links_box.set_halign(Gtk.Align.CENTER)
        links_box.set_margin_top(15)
        parent.pack_start(links_box, False, False, 0)
        
        links = [
            ("web-browser", _("Web"), "https://soplos.org"),
            ("internet-group-chat", _("Forums"), "https://soplos.org/forums/"),
            ("help-browser", _("Wiki"), "https://soplos.org/wiki/"),
            ("emblem-favorite", _("Donate"), "https://www.paypal.com/paypalme/isubdes")
        ]
        
        for icon_name, label, url in links:
            btn = Gtk.Button()
            btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            btn_box.set_halign(Gtk.Align.CENTER)
            icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
            text = Gtk.Label(label=label)
            btn_box.pack_start(icon, False, False, 0)
            btn_box.pack_start(text, False, False, 0)
            btn.add(btn_box)
            btn.get_style_context().add_class(CSS_CLASSES['link_button'])
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
        lang_box.pack_start(lang_icon, False, False, 0)
        
        self.lang_combo = Gtk.ComboBoxText()
        current_index = 0
        for i, (lang_name, config) in enumerate(self.LANGUAGES.items()):
            self.lang_combo.append_text(lang_name)
            if config['code'] == self.current_lang:
                current_index = i
        self.lang_combo.set_active(current_index)
        self.lang_combo.connect("changed", self._on_language_changed)
        lang_box.pack_start(self.lang_combo, False, False, 0)
        settings_box.pack_start(lang_box, False, False, 0)
        
        # Separator
        sep1 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        settings_box.pack_start(sep1, False, False, 0)

        # Resolution selector
        res_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        res_icon = Gtk.Image.new_from_icon_name('video-display', Gtk.IconSize.BUTTON)
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
            
        self.res_combo.connect("changed", self._on_resolution_changed)
        res_box.pack_start(self.res_combo, False, False, 0)
        settings_box.pack_start(res_box, False, False, 0)

        # Separator 2
        sep2 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        settings_box.pack_start(sep2, False, False, 0)
        
        # Autostart switch
        autostart_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        autostart_label = Gtk.Label(label=_("Show at startup"))
        autostart_box.pack_start(autostart_label, False, False, 0)
        
        self.autostart_switch = Gtk.Switch()
        self.autostart_switch.set_active(self.autostart_manager.is_enabled())
        self.autostart_switch.connect("notify::active", self._on_autostart_toggled)
        autostart_box.pack_start(self.autostart_switch, False, False, 0)
        settings_box.pack_start(autostart_box, False, False, 0)
        
        # NumLock switch - ONLY for Tyron (XFCE)
        if self._is_tyron():
            sep2 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
            settings_box.pack_start(sep2, False, False, 0)
            
            numlock_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            numlock_label = Gtk.Label(label=_("NumLock on install"))
            numlock_box.pack_start(numlock_label, False, False, 0)
            
            # Initialize NumLock manager
            self.numlock_manager = NumlockxManager()
            self.numlock_switch = Gtk.Switch()
            self.numlock_switch.set_active(self.numlock_manager.is_enabled())
            self.numlock_switch.set_tooltip_text(_("Enable/disable NumLock activation in installed system"))
            self.numlock_switch.connect("notify::active", self._on_numlock_toggled)
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
        
        status_text = _("Ready - {desktop} on {protocol}").format(
            desktop=desktop_name,
            protocol=protocol_name
        )
        status_label = Gtk.Label(label=status_text)
        status_label.set_halign(Gtk.Align.START)
        status_label.get_style_context().add_class(CSS_CLASSES['status_label'])
        status_box.pack_start(status_label, False, False, 0)
        
        # Right: Version
        version_label = Gtk.Label(label=f"Soplos Welcome Live v{__version__}")
        version_label.set_halign(Gtk.Align.END)
        version_label.get_style_context().add_class('dim-label')
        status_box.pack_end(version_label, False, False, 0)
        
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
            
            # Step 5: Prepare Restart (Delayed)
            update_ui(1.0, _("Restarting session..."))
            
            # Use GLib.timeout_add to separate restart from current stack (Tyson logic)
            GLib.timeout_add(1500, self._do_restart_session)
            
        except Exception as e:
            print(f"Error changing language: {e}")
            self.progress_revealer.set_reveal_child(False)
            self.lang_combo.set_sensitive(True)
            if hasattr(self, 'install_btn'):
                self.install_btn.set_sensitive(True)
            self._show_message(_("Error"), str(e), Gtk.MessageType.ERROR)

    def _do_restart_session(self):
        """Execute the restart command."""
        try:
            from utils.language_changer import get_language_changer
            get_language_changer()._restart_display_manager()
        except:
            pass
        return False
    
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
                subprocess.Popen(['sudo', calamares_cmd],
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
    
    def _on_key_press(self, widget, event):
        """Handle key press events."""
        keyval = event.keyval
        state = event.state
        
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
