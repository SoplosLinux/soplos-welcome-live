#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Soplos Welcome Live 2.0 - Live ISO Welcome Application

Main entry point for the application.
Provides a welcoming experience for users testing Soplos Linux from a Live ISO,
with support for XFCE (Tyron), KDE Plasma (Tyson), and GNOME (Boro).
"""

import sys
import os
import warnings
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Suppress accessibility warnings for cleaner output
warnings.filterwarnings('ignore', '.*Couldn\'t connect to accessibility bus.*', Warning)
warnings.filterwarnings('ignore', '.*Failed to connect to socket.*', Warning)

# Disable accessibility bridge if not explicitly enabled
if not os.environ.get('ENABLE_ACCESSIBILITY'):
    os.environ['NO_AT_BRIDGE'] = '1'
    os.environ['AT_SPI_BUS'] = '0'


def main():
    """Main entry point for Soplos Welcome Live."""
    try:
        # Some GTK warnings are emitted by the underlying C library directly
        # to the process stderr file descriptor. To suppress the known noisy
        # theme parsing warning that originates from the system theme, we
        # temporarily redirect the OS stderr (fd 2) to /dev/null while the
        # GTK modules initialize. We restore stderr afterwards so other
        # runtime errors continue to appear.
        import os
        devnull_fd = None
        saved_stderr_fd = None
        try:
            devnull_fd = os.open(os.devnull, os.O_RDWR)
            saved_stderr_fd = os.dup(2)
            os.dup2(devnull_fd, 2)
            # Import and run the application while stderr is suppressed
            from core import run_application
            return run_application()
        finally:
            # restore stderr
            try:
                if saved_stderr_fd is not None:
                    os.dup2(saved_stderr_fd, 2)
            except Exception:
                pass
            try:
                if saved_stderr_fd is not None:
                    os.close(saved_stderr_fd)
            except Exception:
                pass
            try:
                if devnull_fd is not None:
                    os.close(devnull_fd)
            except Exception:
                pass
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please ensure all dependencies are installed:")
        print("  sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0")
        return 1
        
    except Exception as e:
        print(f"Application error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
