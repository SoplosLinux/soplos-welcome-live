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
                if out.get('connected'):
                    # Look for current mode
                    for mode in out.get('modes', []):
                        if mode.get('current'):
                            size = mode.get('size')
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
            
            for monitor in monitors:
                # monitor structure: (connector_info, modes, props)
                # modes is standard at index 8 inside the struct if strictly parsed?
                # Actually, GVariant unpacking is recursive.
                # Monitor struct: (u, ii, u, b, b, b) is NOT it. That's Logical Monitor or something?
                # Let's check documentation signature for GetCurrentState:
                # Returns: (serial, monitors, logical_monitors, properties)
                # monitors: a(u,s,s,s,s,s,s,a{sv},[(u,u,d,u,b,b,b)],a{sv},a{sv})
                # The modes list is the 9th element (index 8) -> [(u,u,d,u,b,b,b)]
                # Mode struct: (id, width, height, rate, preferred, supported_scales, properties)
                
                modes = monitor[8]
                for mode in modes:
                    width = mode[1]
                    height = mode[2]
                    res_list.append(f"{width}x{height}")
                    
        except Exception as e:
            print(f"GNOME DBus detection failed: {e}")
            # Fallback
            return ["1920x1080", "1600x900", "1366x768", "1280x720", "1024x768"]
            
        return res_list

    def _get_gnome_current_resolution(self) -> Optional[str]:
        """Get current resolution via DBus."""
        # Getting the *active* resolution from DBus is complex because 'GetCurrentState'
        # returns all supported modes but doesn't explicitly flag the active one in a simple way
        # without parsing the LogicalMonitor layout which uses screen coordinates.
        # For a live ISO welcome screen, defaulting to automatic selection is acceptable.
        return None

    def _set_gnome_resolution(self, resolution: str) -> bool:
        """Set resolution via DBus ApplyMonitorsConfig preserving existing layout."""
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
            monitors = data[1] # list of ((connector, vendor, ...), [modes], properties)
            logical_monitors = data[2] # list of (x, y, scale, transform, primary, [monitors_config])
            
            # We will modify 'logical_monitors' directly to preserve layout
            new_logical_monitors = []
            
            # We need to find the TARGET MODE ID for the requested resolution
            # We assume we are applying this to the 'current' or 'primary' monitor if unclear,
            # or we check which monitor supports this mode.
            
            # Strategy: Iterate through existing logical monitors.
            # For each, check if its underlying monitor supports the requested WxH.
            # If so, update the mode_id. If not, keep as is.
            
            valid_change_made = False
            
            for logical_mon in logical_monitors:
                x, y, scale, transform, primary, monitors_config = logical_mon
                
                new_monitors_config = []
                
                for mon_config in monitors_config:
                    connector_name = mon_config[0]
                    current_mode_id = mon_config[1]
                    mon_props = mon_config[2]
                    
                    # Find the physical monitor definition for this connector
                    target_monitor = None
                    for m in monitors:
                        if m[0][0] == connector_name:
                            target_monitor = m
                            break
                    
                    if target_monitor:
                        modes = target_monitor[8]
                        # Look for requested resolution in this monitor's modes
                        found_mode_id = None
                        for mode in modes:
                             # mode: (id, w, h, rate, ...)
                             if int(mode[1]) == w and int(mode[2]) == h:
                                 found_mode_id = mode[0]
                                 break
                        
                        if found_mode_id:
                            # Update to new mode!
                            print(f"DEBUG: Changing {connector_name} to {found_mode_id} ({w}x{h})")
                            new_monitors_config.append((connector_name, found_mode_id, mon_props))
                            valid_change_made = True
                        else:
                            # Keep existing mode
                            new_monitors_config.append(mon_config)
                    else:
                         new_monitors_config.append(mon_config)

                # Append this logical monitor (maybe modified) to new list
                # Ensure types are strict for DBus (d for scale)
                new_logical_monitors.append((
                    int(x), int(y), float(scale), int(transform), bool(primary), new_monitors_config
                ))
            
            if valid_change_made:
                # Parameters: (serial, method, logical_monitors, properties)
                params = GLib.Variant(
                    "(uua(iiduba(ssa{sv}))a{sv})",
                    (
                        int(serial), 
                        int(2), # 2 = Temporary
                        new_logical_monitors, 
                        {}
                    )
                )
                
                print(f"DEBUG: Applying configuration: {new_logical_monitors}")
                
                bus.call_sync(
                    "org.gnome.Mutter.DisplayConfig",
                    "/org/gnome/Mutter/DisplayConfig",
                    "org.gnome.Mutter.DisplayConfig",
                    "ApplyMonitorsConfig",
                    params,
                    None,
                    Gio.DBusCallFlags.NONE,
                    -1,
                    None
                )
                return True
            else:
                print("DEBUG: Resolution not found supported for active monitors.")
                return False
                
        except Exception as e:
            print(f"GNOME resolution set failed: {e}")
            import traceback
            traceback.print_exc()
            
        return False
