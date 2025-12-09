"""
Display Manager for Soplos Welcome Live.
Handles resolution detection and changing for X11 (XFCE), Wayland (KDE), and Wayland (GNOME).
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gio, GLib

import os
import subprocess
import re
import json
from typing import List, Tuple, Optional, Dict
from pathlib import Path
import sys

# Add parent dir to path if needed (standard in this project)
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.environment import get_environment_detector, DesktopEnvironment, DisplayProtocol

class DisplayManager:
    def __init__(self):
        self.env = get_environment_detector()
        self.env.detect_all()
        self.desktop = self.env.desktop_environment
        self.protocol = self.env.display_protocol
        
    def get_resolutions(self) -> List[str]:
        """Get list of available resolutions (e.g. ['1920x1080', '1366x768'])."""
        resolutions = []
        try:
            if self.protocol == DisplayProtocol.X11:
                resolutions = self._get_x11_resolutions()
            elif self.desktop == DesktopEnvironment.KDE:
                resolutions = self._get_kde_resolutions()
            elif self.desktop == DesktopEnvironment.GNOME:
                resolutions = self._get_gnome_resolutions()
        except Exception as e:
            print(f"Error checking resolutions: {e}")
            
        # Fallback if empty - provide safe defaults
        if not resolutions:
            return ["1920x1080", "1600x900", "1366x768", "1280x720", "1024x768", "800x600"]
            
        # Deduplicate and sort (descending area)
        unique_res = sorted(list(set(resolutions)), 
                          key=lambda r: int(r.split('x')[0]) * int(r.split('x')[1]) if 'x' in r else 0,
                          reverse=True)
        return unique_res

    def set_resolution(self, resolution: str) -> bool:
        """Set screen resolution."""
        try:
            print(f"Setting resolution to {resolution}...")
            if self.protocol == DisplayProtocol.X11:
                return self._set_x11_resolution(resolution)
            elif self.desktop == DesktopEnvironment.KDE:
                return self._set_kde_resolution(resolution)
            elif self.desktop == DesktopEnvironment.GNOME:
                return self._set_gnome_resolution(resolution)
        except Exception as e:
            return False
        return False

    def get_current_resolution(self) -> Optional[str]:
        """Get the current screen resolution."""
        try:
            if self.protocol == DisplayProtocol.X11:
                return self._get_x11_current_resolution()
            elif self.desktop == DesktopEnvironment.KDE:
                return self._get_kde_current_resolution()
            elif self.desktop == DesktopEnvironment.GNOME:
                return self._get_gnome_current_resolution()
        except Exception as e:
            print(f"Error checking current resolution: {e}")
        return None

    # ==================== X11 Implementation ====================
    
    def _get_x11_resolutions(self) -> List[str]:
        # Parse xrandr output
        res_list = []
        try:
            output = subprocess.check_output(['xrandr', '-q'], universal_newlines=True)
            for line in output.splitlines():
                if 'connected' in line and 'disconnected' not in line:
                    continue  # output header
                # Lines with resolution: "   1920x1080     60.00*+  50.00  "
                match = re.search(r'\s+(\d+x\d+)', line)
                if match:
                    res_list.append(match.group(1))
        except Exception as e:
            print(f"X11 detection failed: {e}")
        return res_list

    def _set_x11_resolution(self, resolution: str) -> bool:
        # Need to find the connected output first
        try:
            output_info = subprocess.check_output(['xrandr', '-q'], universal_newlines=True)
            connected_output = None
            for line in output_info.splitlines():
                if ' connected' in line:
                    connected_output = line.split()[0]
                    break
            
            if connected_output:
                subprocess.run(['xrandr', '--output', connected_output, '--mode', resolution], check=True)
                return True
        except Exception as e:
            print(f"X11 switch failed: {e}")
        return False

    def _get_x11_current_resolution(self) -> Optional[str]:
        try:
            output = subprocess.check_output(['xrandr', '-q'], universal_newlines=True)
            for line in output.splitlines():
                # Look for line with asterisk: "   1920x1080     60.00*+  50.00  "
                if '*' in line:
                    match = re.search(r'\s+(\d+x\d+)', line)
                    if match:
                        return match.group(1)
        except Exception:
            pass
        return None

    # ==================== KDE Wayland Implementation ====================

    def _get_kde_resolutions(self) -> List[str]:
        # kscreen-doctor -j returns JSON
        res_list = []
        try:
            # Check availability first
            try:
                subprocess.run(['kscreen-doctor', '-h'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except FileNotFoundError:
                return []

            output = subprocess.check_output(['kscreen-doctor', '-j'], universal_newlines=True)
            data = json.loads(output)
            
            for output in data.get('outputs', []):
                if output.get('connected'):
                    for mode in output.get('modes', []):
                        # Format "1920x1080"
                        size = mode.get('size')
                        if size:
                            res_list.append(f"{size['width']}x{size['height']}")
        except Exception as e:
            print(f"KDE detection failed: {e}")
            # Fallback text parsing if JSON fails (older versions)
            pass
        return res_list

    def _set_kde_resolution(self, resolution: str) -> bool:
        try:
            # Need strict format for kscreen-doctor: output.<id>.mode.<mode_id>
            # 1. Get current config to map resolution to mode ID
            output_json = subprocess.check_output(['kscreen-doctor', '-j'], universal_newlines=True)
            data = json.loads(output_json)
            
            cmd_args = []
            
            for out in data.get('outputs', []):
                if out.get('connected'):
                    out_id = out.get('id')
                    target_mode_id = None
                    
                    # Find model mode ID matching requested resolution
                    w, h = map(int, resolution.split('x'))
                    
                    best_mode = None
                    # Prefer higher refresh rate? Default to first found
                    for mode in out.get('modes', []):
                        size = mode.get('size')
                        if size['width'] == w and size['height'] == h:
                            target_mode_id = mode.get('id')
                            break # Found match
                    
                    if target_mode_id:
                        cmd_args.extend([f"output.{out_id}.mode.{target_mode_id}"])
            
            if cmd_args:
                full_cmd = ['kscreen-doctor'] + cmd_args
                subprocess.run(full_cmd, check=True)
                return True
        except Exception as e:
            print(f"KDE switch failed: {e}")
        return False

    def _get_kde_current_resolution(self) -> Optional[str]:
        try:
            output = subprocess.check_output(['kscreen-doctor', '-j'], universal_newlines=True)
            data = json.loads(output)
            for out in data.get('outputs', []):
                if not out.get('connected'):
                    continue

                # 1) Preferred: explicit currentModeId on the output (common in many kscreen versions)
                current_mode_id = out.get('currentModeId') or out.get('current_mode') or out.get('currentMode')
                if current_mode_id is not None:
                    for mode in out.get('modes', []):
                        mid = mode.get('id')
                        if mid is None:
                            continue
                        try:
                            if str(mid) == str(current_mode_id):
                                size = mode.get('size')
                                if size:
                                    return f"{size['width']}x{size['height']}"
                        except Exception:
                            continue

                # 2) Secondary: look for a mode flagged as current/active/preferred
                for mode in out.get('modes', []):
                    if mode.get('current') or mode.get('active') or mode.get('preferred'):
                        size = mode.get('size')
                        if size:
                            return f"{size['width']}x{size['height']}"

                # 3) Some outputs embed a simple 'mode' dict with width/height
                mode_obj = out.get('mode') or out.get('current')
                if isinstance(mode_obj, dict):
                    w = None
                    h = None
                    if 'width' in mode_obj and 'height' in mode_obj:
                        w = mode_obj.get('width')
                        h = mode_obj.get('height')
                    else:
                        size = mode_obj.get('size') if isinstance(mode_obj.get('size'), dict) else None
                        if size:
                            w = size.get('width')
                            h = size.get('height')
                    if w and h:
                        return f"{w}x{h}"

                # 4) Fallback: prefer a 'preferred' mode, otherwise try to infer
                preferred = next((m for m in out.get('modes', []) if m.get('preferred')), None)
                if preferred:
                    size = preferred.get('size')
                    if size:
                        return f"{size['width']}x{size['height']}"

                # 5) Last resort: pick the first mode that looks valid (avoid always picking the largest)
                modes = out.get('modes', [])
                if modes:
                    for mode in modes:
                        size = mode.get('size')
                        if size and size.get('width') and size.get('height'):
                            return f"{size['width']}x{size['height']}"
        except Exception:
            pass
        return None

    # ==================== GNOME Wayland Implementation ====================

    def _get_gnome_resolutions(self) -> List[str]:
        """Get resolutions via DBus from Mutter."""
        res_list = []
        try:
            # Connect to Session Bus
            bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
            
            # Call GetCurrentState
            # Signature: () -> (u, [(u,ii,u,b,b,b)], [(u,s,s,s,s,s,s,a{sv},[(u,u,d,u,b,b,b)],a{sv},a{sv})], a{sv})
            # Simplified: serial, monitors, logical_monitors, properties
            result = bus.call_sync(
                "org.gnome.Mutter.DisplayConfig",
                "/org/gnome/Mutter/DisplayConfig",
                "org.gnome.Mutter.DisplayConfig",
                "GetCurrentState",
                None,
                None,
                Gio.DBusCallFlags.NONE,
                -1,
                None
            )
            
            # Parse result (Variant)
            # data = (serial, monitors, logical_monitors, properties)
            data = result.unpack()
            monitors = data[1]

            def extract_modes_from_monitor(mon):
                if not isinstance(mon, (list, tuple)):
                    return []
                if len(mon) > 8 and isinstance(mon[8], (list, tuple)):
                    return mon[8]
                for item in mon:
                    if isinstance(item, (list, tuple)) and item:
                        first = item[0]
                        if isinstance(first, (list, tuple)) and len(first) >= 3:
                            try:
                                int(first[1]); int(first[2])
                                return item
                            except Exception:
                                continue
                return []

            for monitor in monitors:
                modes = extract_modes_from_monitor(monitor)
                for mode in modes:
                    try:
                        if len(mode) > 2:
                            width = int(mode[1])
                            height = int(mode[2])
                            res_list.append(f"{width}x{height}")
                    except Exception:
                        continue
                    
        except Exception as e:
            print(f"GNOME DBus detection failed: {e}")
            # Fallback
            return ["1920x1080", "1600x900", "1366x768", "1280x720", "1024x768"]
            
        return res_list

    def _get_gnome_current_resolution(self) -> Optional[str]:
        """Get current resolution via GDK first, then DBus as fallback.

        For Live ISO UX we prefer the actual geometry the user sees (GDK).
        If GDK fails, fall back to the DBus parsing logic (modes, preferred, first).
        """
        # FIRST: GDK (reliable for what's actually displayed)
        try:
            from gi.repository import Gdk
            display = Gdk.Display.get_default()
            if display:
                monitor = display.get_primary_monitor() or display.get_monitor(0)
                if monitor:
                    geometry = monitor.get_geometry()
                    # get_scale_factor exists on Gdk.Monitor in many versions
                    try:
                        scale = monitor.get_scale_factor()
                    except Exception:
                        scale = 1
                    width = int(geometry.width * scale)
                    height = int(geometry.height * scale)
                    print(f"[DEBUG] GDK reports actual resolution: {width}x{height}")
                    return f"{width}x{height}"
        except Exception as e:
            print(f"[DEBUG] GDK detection failed: {e}")

        # FALLBACK: DBus parsing (existing logic)
        try:
            bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)

            result = bus.call_sync(
                "org.gnome.Mutter.DisplayConfig",
                "/org/gnome/Mutter/DisplayConfig",
                "org.gnome.Mutter.DisplayConfig",
                "GetCurrentState",
                None, None, Gio.DBusCallFlags.NONE, -1, None
            )

            data = result.unpack()
            if not data or len(data) < 3:
                print("GNOME GetCurrentState returned unexpected structure")
                return None

            monitors = data[1] if len(data) > 1 else []
            logical_monitors = data[2] if len(data) > 2 else []

            for logical_mon in logical_monitors:
                try:
                    if not isinstance(logical_mon, (list, tuple)) or len(logical_mon) < 6:
                        continue

                    monitors_config = logical_mon[5]
                    if not monitors_config:
                        continue

                    mon_config = monitors_config[0]
                    if not isinstance(mon_config, (list, tuple)) or len(mon_config) < 2:
                        continue

                    connector_name = str(mon_config[0])
                    current_mode_id = mon_config[1]

                    def find_monitor_by_connector(monitors_list, name):
                        for mm in monitors_list:
                            try:
                                candidate = None
                                if isinstance(mm, (list, tuple)) and len(mm) > 0:
                                    head = mm[0]
                                    if isinstance(head, (list, tuple)) and len(head) > 0:
                                        candidate = head[0]
                                    else:
                                        candidate = head
                                if candidate is None:
                                    continue
                                if str(candidate) == str(name):
                                    return mm
                            except Exception:
                                continue
                        return None

                    target = find_monitor_by_connector(monitors, connector_name)
                    if not target:
                        continue

                    def extract_modes_from_monitor(mon):
                        if not isinstance(mon, (list, tuple)):
                            return []
                        if len(mon) > 8 and isinstance(mon[8], (list, tuple)):
                            return mon[8]
                        for item in mon:
                            if isinstance(item, (list, tuple)) and item:
                                first = item[0]
                                if isinstance(first, (list, tuple)) and len(first) >= 3:
                                    try:
                                        int(first[1]); int(first[2])
                                        return item
                                    except Exception:
                                        continue
                        return []

                    modes = extract_modes_from_monitor(target)

                    # 1) Try mode by ID
                    for mode in modes:
                        try:
                            if len(mode) > 0 and str(mode[0]) == str(current_mode_id):
                                if len(mode) > 2:
                                    width = int(mode[1])
                                    height = int(mode[2])
                                    print(f"[DEBUG] Found current resolution by mode ID: {width}x{height}")
                                    return f"{width}x{height}"
                        except Exception:
                            continue

                    # 2) Fallback: preferred mode
                    print(f"[DEBUG] Mode ID '{current_mode_id}' not found, trying preferred/first mode")
                    for mode in modes:
                        try:
                            if len(mode) > 4 and mode[4]:
                                width = int(mode[1])
                                height = int(mode[2])
                                print(f"[DEBUG] Using preferred mode: {width}x{height}")
                                return f"{width}x{height}"
                        except Exception:
                            continue

                    # 3) Fallback: first available mode
                    if modes and len(modes) > 0:
                        try:
                            first_mode = modes[0]
                            if len(first_mode) > 2:
                                width = int(first_mode[1])
                                height = int(first_mode[2])
                                print(f"[DEBUG] Using first available mode: {width}x{height}")
                                return f"{width}x{height}"
                        except Exception:
                            pass

                except (IndexError, TypeError) as e:
                    print(f"[DEBUG] Error parsing logical monitor: {e}")
                    continue

        except Exception as e:
            print(f"[DEBUG] GNOME current resolution detection (DBus) failed: {e}")
            import traceback
            traceback.print_exc()

        return None

    def _set_gnome_resolution(self, resolution: str) -> bool:
        """Set resolution via DBus ApplyMonitorsConfig."""
        try:
            w, h = map(int, resolution.split('x'))
            bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
            
            # 1. Get current state
            state = bus.call_sync(
                "org.gnome.Mutter.DisplayConfig",
                "/org/gnome/Mutter/DisplayConfig",
                "org.gnome.Mutter.DisplayConfig",
                "GetCurrentState",
                None, None, Gio.DBusCallFlags.NONE, -1, None
            )
            
            data = state.unpack()
            serial = data[0]
            monitors = data[1]
            logical_monitors = data[2]
            
            new_logical_monitors = []
            valid_change_made = False
            
            for logical_mon in logical_monitors:
                # Unpack with error handling
                try:
                    x = int(logical_mon[0])
                    y = int(logical_mon[1])
                    scale = float(logical_mon[2])
                    transform = int(logical_mon[3])
                    primary = bool(logical_mon[4])
                    monitors_config = logical_mon[5]
                except (IndexError, TypeError, ValueError) as e:
                    print(f"Error unpacking logical monitor: {e}")
                    continue
                
                new_monitors_config = []
                
                for mon_config in monitors_config:
                    try:
                        connector_name = str(mon_config[0])
                        current_mode_id = str(mon_config[1])
                        # Do not forward the original GVariant properties directly; use empty dict
                        mon_props = {}
                    except (IndexError, TypeError) as e:
                        print(f"Error unpacking monitor config: {e}")
                        continue
                    
                    # Find the physical monitor for this connector
                    target_monitor = None
                    for m in monitors:
                        try:
                            if str(m[0][0]) == connector_name:
                                target_monitor = m
                                break
                        except (IndexError, TypeError):
                            continue
                    
                    if target_monitor:
                        try:
                            # Extract modes defensively (modes might be at index 8 or nested differently)
                            def extract_modes_from_monitor(mon):
                                if not isinstance(mon, (list, tuple)):
                                    return []
                                if len(mon) > 8 and isinstance(mon[8], (list, tuple)):
                                    return mon[8]
                                for item in mon:
                                    if isinstance(item, (list, tuple)) and item:
                                        first = item[0]
                                        if isinstance(first, (list, tuple)) and len(first) >= 3:
                                            try:
                                                int(first[1]); int(first[2])
                                                return item
                                            except Exception:
                                                continue
                                return []

                            modes = extract_modes_from_monitor(target_monitor)
                            found_mode_id = None
                            best_refresh = 0.0

                            # Find mode with requested resolution (prefer highest refresh rate)
                            for mode in modes:
                                try:
                                    if not isinstance(mode, (list, tuple)) or len(mode) < 3:
                                        continue
                                    mode_id = str(mode[0])
                                    mode_w = int(mode[1])
                                    mode_h = int(mode[2])
                                    # Some mode tuples may not have refresh at index 3
                                    try:
                                        mode_refresh = float(mode[3]) if len(mode) > 3 else 0.0
                                    except Exception:
                                        mode_refresh = 0.0

                                    if mode_w == w and mode_h == h:
                                        if mode_refresh >= best_refresh:
                                            found_mode_id = mode_id
                                            best_refresh = mode_refresh
                                except Exception:
                                    continue
                            
                            if found_mode_id:
                                print(f"Changing {connector_name} from mode {current_mode_id} to {found_mode_id} ({w}x{h}@{best_refresh}Hz)")
                                new_monitors_config.append((connector_name, found_mode_id, mon_props))
                                valid_change_made = True
                            else:
                                # Keep existing mode if resolution not found
                                new_monitors_config.append((connector_name, current_mode_id, mon_props))
                        except (IndexError, TypeError, ValueError) as e:
                            print(f"Error processing modes: {e}")
                            new_monitors_config.append((connector_name, current_mode_id, mon_props))
                    else:
                        # Monitor not found, keep as is
                        new_monitors_config.append((connector_name, current_mode_id, mon_props))
                
                # Add this logical monitor to the new configuration
                new_logical_monitors.append((x, y, scale, transform, primary, new_monitors_config))
            
            if not valid_change_made:
                print(f"Resolution {resolution} not found in available modes")
                return False
            
            # Build the ApplyMonitorsConfig parameters
            # Signature: (serial, method, logical_monitors, properties)
            # method: 0=verify, 1=temporary, 2=persistent
            params = GLib.Variant(
                "(uua(iiduba(ssa{sv}))a{sv})",
                (
                    serial,
                    1,  # 1 = Temporary (use 2 for persistent)
                    new_logical_monitors,
                    {}  # Empty properties dict
                )
            )
            
            print(f"Applying GNOME resolution configuration...")
            
            result = bus.call_sync(
                "org.gnome.Mutter.DisplayConfig",
                "/org/gnome/Mutter/DisplayConfig",
                "org.gnome.Mutter.DisplayConfig",
                "ApplyMonitorsConfig",
                params,
                None,
                Gio.DBusCallFlags.NONE,
                5000,  # 5 second timeout
                None
            )
            
            print(f"Resolution changed successfully to {resolution}")
            return True
            
        except GLib.Error as e:
            print(f"GLib/DBus error: {e.message}")
            return False
        except Exception as e:
            print(f"GNOME resolution set failed: {e}")
            import traceback
            traceback.print_exc()
            return False
