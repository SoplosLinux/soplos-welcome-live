"""
User interface module for Soplos Welcome Live.
Contains all GTK-based UI components, windows, and dialogs.
"""

# UI module information
__version__ = "2.0.0"
__author__ = "Sergi Perich"

# Re-export main components when available
try:
    from .main_window import MainWindow
    __all__ = ['MainWindow']
except ImportError:
    __all__ = []

# UI Constants (matching soplos-welcome 2.0)
DEFAULT_WINDOW_WIDTH = 850
DEFAULT_WINDOW_HEIGHT = 500
MIN_WINDOW_WIDTH = 750
MIN_WINDOW_HEIGHT = 400

# CSS Classes
CSS_CLASSES = {
    'window': 'soplos-welcome-live-window',
    'content': 'soplos-content',
    'card': 'soplos-card',
    'button_install': 'soplos-button-install',
    'button_primary': 'soplos-button-primary',
    'button_secondary': 'soplos-button-secondary',
    'button_danger': 'soplos-button-danger',
    'status_label': 'soplos-status-label',
    'progress_bar': 'soplos-progress-bar',
    'icon_large': 'soplos-icon-large',
    'icon_medium': 'soplos-icon-medium',
    'separator': 'soplos-separator',
    'welcome_title': 'soplos-welcome-title',
    'welcome_subtitle': 'soplos-welcome-subtitle',
    'slide_image': 'soplos-slide-image',
    'link_button': 'soplos-link-button',
    'features_header': 'features-header',
    'dialog_title': 'dialog-title'
}
