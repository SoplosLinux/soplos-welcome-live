"""
Main window for Soplos Welcome Live.
Central GUI component that manages the welcome interface.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf

import os
import sys
import subprocess
import webbrowser
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.i18n_manager import _
from core import __version__
from config.paths import LOGO_PATH, SLIDE_PATH, ICONS_DIR
from ui import (DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT, 
                MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT, CSS_CLASSES)
from utils.autostart import AutostartManager
from utils.language_changer import get_language_changer, LanguageChangeResult
from utils.session_manager import get_session_manager


class MainWindow(Gtk.ApplicationWindow):
    """
    Main application window for Soplos Welcome Live.
    Provides the live ISO welcome experience with install, chroot, and configuration options.
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
        """
        Initialize the main window.
        
        Args:
            application: The parent GTK application
            environment_detector: Environment detection instance
            theme_manager: Theme management instance
            i18n_manager: Internationalization manager instance
        """
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
        
        # Language changer
        self.language_changer = get_language_changer()
        
        # Session manager
        self.session_manager = get_session_manager()
        
        # Window properties
        self.set_title(_("Soplos Welcome Live"))
        self.set_default_size(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self.set_size_request(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(True)
        
        # Set WM_CLASS
        self.set_wmclass("org.soplos.welcomelive", "org.soplos.welcomelive")
        
        # Apply CSS class
        self.get_style_context().add_class(CSS_CLASSES['window'])
        
        # Set border width
        self.set_border_width(10)
        
        # Window icon
        self._set_window_icon()
        
        # Create UI
        self._create_ui()
        
        # Connect signals
        self.connect('delete-event', self._on_delete_event)
        self.connect('key-press-event', self._on_key_press)
        
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
        """Create the main user interface."""
        # Main vertical container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(main_box)
        
        # Horizontal content area (logo left, content right)
        content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        main_box.pack_start(content_box, True, True, 0)
        
        # Left panel (logo and controls)
        self._create_left_panel(content_box)
        
        # Right panel (main content)
        self._create_right_panel(content_box)
        
        # Progress bar at bottom
        self._create_progress_bar(main_box)
    
    def _create_left_panel(self, parent):
        """Create the left panel with logo and controls."""
        left_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        left_panel.set_size_request(200, -1)
        parent.pack_start(left_panel, False, False, 5)
        
        # Logo
        try:
            if LOGO_PATH.exists():
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    filename=str(LOGO_PATH),
                    width=150,
                    height=150,
                    preserve_aspect_ratio=True
                )
                logo_image = Gtk.Image.new_from_pixbuf(pixbuf)
                left_panel.pack_start(logo_image, False, False, 10)
        except Exception as e:
            print(f"Error loading logo: {e}")
        
        # Welcome text
        welcome_label = Gtk.Label()
        welcome_label.set_markup(
            f"<span size='large' weight='bold'>{_('Welcome to Soplos Linux')}</span>\n"
            f"<span size='small'>{_('Live Session')} - {self.edition_name}</span>"
        )
        welcome_label.set_justify(Gtk.Justification.CENTER)
        welcome_label.set_line_wrap(True)
        left_panel.pack_start(welcome_label, False, False, 5)
        
        # Flexible space
        left_panel.pack_start(Gtk.Box(), True, True, 0)
        
        # Controls area
        controls_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        left_panel.pack_end(controls_box, False, False, 0)
        
        # Autostart switch
        autostart_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        autostart_label = Gtk.Label(label=_("Show at startup"))
        autostart_box.pack_start(autostart_label, False, False, 0)
        
        self.autostart_switch = Gtk.Switch()
        self.autostart_switch.set_active(self.autostart_manager.is_enabled())
        self.autostart_switch.connect("notify::active", self._on_autostart_toggled)
        autostart_box.pack_end(self.autostart_switch, False, False, 0)
        
        controls_box.pack_start(autostart_box, False, False, 5)
        
        # Language selector
        lang_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        lang_box.set_margin_bottom(5)
        
        lang_label = Gtk.Label(label=_("Language"))
        lang_box.pack_start(lang_label, False, False, 0)
        
        self.lang_combo = Gtk.ComboBoxText()
        current_index = 0
        
        for i, (lang_name, config) in enumerate(self.LANGUAGES.items()):
            self.lang_combo.append_text(lang_name)
            if config['code'] == self.current_lang:
                current_index = i
        
        self.lang_combo.set_active(current_index)
        self.lang_combo.connect("changed", self._on_language_changed)
        lang_box.pack_start(self.lang_combo, True, True, 5)
        
        controls_box.pack_start(lang_box, False, False, 0)
    
    def _create_right_panel(self, parent):
        """Create the right panel with main content."""
        right_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        parent.pack_start(right_panel, True, True, 0)
        
        # Slide image
        try:
            if SLIDE_PATH.exists():
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    filename=str(SLIDE_PATH),
                    width=580,
                    height=160,
                    preserve_aspect_ratio=True
                )
                slide_image = Gtk.Image.new_from_pixbuf(pixbuf)
                slide_image.get_style_context().add_class(CSS_CLASSES['slide_image'])
                right_panel.pack_start(slide_image, False, False, 0)
        except Exception as e:
            print(f"Error loading slide: {e}")
        
        # Welcome message
        welcome_msg = Gtk.Label()
        welcome_msg.set_markup(
            f"<span size='xx-large' weight='bold'>{_('Try Soplos Linux')}</span>\n"
            f"<span size='large'>{_('Explore the system before installing')}</span>"
        )
        welcome_msg.set_line_wrap(True)
        welcome_msg.set_justify(Gtk.Justification.CENTER)
        welcome_msg.set_margin_top(10)
        welcome_msg.set_margin_bottom(10)
        right_panel.pack_start(welcome_msg, False, False, 0)
        
        # Link buttons row
        links_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        links_box.set_margin_top(10)
        links_box.set_homogeneous(True)
        right_panel.pack_start(links_box, False, True, 0)
        
        # Website button
        website_btn = Gtk.Button(label=_("Website"))
        website_btn.connect("clicked", lambda x: webbrowser.open("https://soplos.org"))
        website_btn.get_style_context().add_class(CSS_CLASSES['link_button'])
        links_box.pack_start(website_btn, True, True, 10)
        
        # Forums button
        forum_btn = Gtk.Button(label=_("Forums"))
        forum_btn.connect("clicked", lambda x: webbrowser.open("https://soplos.org/forums/"))
        forum_btn.get_style_context().add_class(CSS_CLASSES['link_button'])
        links_box.pack_start(forum_btn, True, True, 10)
        
        # Wiki button
        wiki_btn = Gtk.Button(label=_("Wiki"))
        wiki_btn.connect("clicked", lambda x: webbrowser.open("https://soplos.org/wiki/"))
        wiki_btn.get_style_context().add_class(CSS_CLASSES['link_button'])
        links_box.pack_start(wiki_btn, True, True, 10)
        
        # Donate button
        donate_btn = Gtk.Button(label=_("Donate"))
        donate_btn.connect("clicked", lambda x: webbrowser.open("https://paypal.me/isubdes"))
        donate_btn.get_style_context().add_class(CSS_CLASSES['link_button'])
        links_box.pack_start(donate_btn, True, True, 10)
        
        # Spacer
        right_panel.pack_start(Gtk.Box(), True, True, 0)
        
        # Action buttons row
        button_panel = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        right_panel.pack_end(button_panel, False, False, 5)
        
        # Exit button
        exit_btn = Gtk.Button(label=_("Exit"))
        exit_btn.connect("clicked", self._on_exit_clicked)
        button_panel.pack_end(exit_btn, False, False, 0)
        
        # ChRoot button
        chroot_btn = Gtk.Button(label=_("System Rescue"))
        chroot_btn.connect("clicked", self._on_chroot_clicked)
        chroot_btn.set_tooltip_text(_("Mount and repair an existing installation"))
        button_panel.pack_end(chroot_btn, False, False, 5)
        
        # Install button (prominent)
        install_btn = Gtk.Button(label=_("Install Soplos Linux"))
        install_btn.connect("clicked", self._on_install_clicked)
        install_btn.get_style_context().add_class(CSS_CLASSES['button_install'])
        install_btn.get_style_context().add_class('suggested-action')
        button_panel.pack_end(install_btn, False, False, 5)
    
    def _create_progress_bar(self, parent):
        """Create the progress bar at the bottom."""
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(False)
        self.progress_bar.set_no_show_all(True)  # Hidden by default
        parent.pack_end(self.progress_bar, False, False, 0)
    
    def _on_autostart_toggled(self, switch, gparam):
        """Handle autostart switch toggle."""
        if switch.get_active():
            self.autostart_manager.enable()
        else:
            self.autostart_manager.disable()
    
    def _on_language_changed(self, combo):
        """Handle language change."""
        lang_name = combo.get_active_text()
        if lang_name not in self.LANGUAGES:
            return
        
        lang_config = self.LANGUAGES[lang_name]
        lang_code = lang_config['code']
        
        # Show confirmation dialog
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=_("Change Language")
        )
        dialog.format_secondary_text(
            _("Do you want to change the system language to {language}?\n\n"
              "This will require a session restart to take full effect.").format(
                  language=lang_name
              )
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            self._apply_language_change(lang_code)
    
    def _apply_language_change(self, lang_code: str):
        """Apply the language change."""
        # Show progress
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_text(_("Changing language..."))
        self.progress_bar.show()
        self.progress_bar.pulse()
        
        def do_change():
            result, message = self.language_changer.change_language(lang_code)
            GLib.idle_add(self._on_language_change_complete, result, message)
        
        # Run in background
        import threading
        thread = threading.Thread(target=do_change)
        thread.daemon = True
        thread.start()
    
    def _on_language_change_complete(self, result: LanguageChangeResult, message: str):
        """Handle language change completion."""
        self.progress_bar.hide()
        
        if result == LanguageChangeResult.RESTART_REQUIRED:
            # Ask to restart session
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.YES_NO,
                text=_("Restart Required")
            )
            dialog.format_secondary_text(
                _("Language settings have been updated.\n\n"
                  "Do you want to restart your session now to apply all changes?")
            )
            
            response = dialog.run()
            dialog.destroy()
            
            if response == Gtk.ResponseType.YES:
                # Schedule restart and close app
                self.session_manager.schedule_restart_after_app_close(2)
                self.application.quit()
        
        elif result == LanguageChangeResult.PARTIAL:
            self._show_message(_("Partial Success"), message, Gtk.MessageType.WARNING)
        
        elif result == LanguageChangeResult.FAILED:
            self._show_message(_("Error"), message, Gtk.MessageType.ERROR)
        
        return False
    
    def _on_install_clicked(self, button):
        """Handle install button click - launch Calamares."""
        try:
            # Try to find Calamares
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
                # Launch Calamares with pkexec for root privileges
                subprocess.Popen(['pkexec', calamares_cmd],
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
                print("Calamares installer launched")
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
    
    def _on_exit_clicked(self, button):
        """Handle exit button click."""
        self.application.quit()
    
    def _on_delete_event(self, widget, event):
        """Handle window close."""
        return False  # Allow close
    
    def _on_key_press(self, widget, event):
        """Handle key press events."""
        # Escape to close
        if event.keyval == Gdk.KEY_Escape:
            self.application.quit()
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
    
    def show_progress(self, text: str = "", fraction: float = -1):
        """
        Show progress bar with optional text and fraction.
        
        Args:
            text: Progress text to display
            fraction: Progress fraction (0-1), or -1 for pulse mode
        """
        self.progress_bar.show()
        
        if text:
            self.progress_bar.set_show_text(True)
            self.progress_bar.set_text(text)
        
        if fraction < 0:
            self.progress_bar.pulse()
        else:
            self.progress_bar.set_fraction(fraction)
    
    def hide_progress(self):
        """Hide the progress bar."""
        self.progress_bar.hide()
        self.progress_bar.set_fraction(0)
        self.progress_bar.set_show_text(False)
