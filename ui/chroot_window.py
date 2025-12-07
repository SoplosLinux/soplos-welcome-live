"""
ChRoot Window for Soplos Welcome Live.
Provides system rescue functionality - mount and access existing Linux installations.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, List, Dict

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.i18n_manager import _
from core.chroot_operations import SystemOperations
from ui import CSS_CLASSES


class ChRootWindow(Gtk.Window):
    """
    System rescue window for mounting and accessing existing installations.
    Supports btrfs subvolumes and standard partition layouts.
    """
    
    def __init__(self, parent_window: Optional[Gtk.Window] = None):
        """Initialize the ChRoot window."""
        super().__init__(title=_("System Rescue"))
        
        self.parent_window = parent_window
        
        if parent_window:
            self.set_transient_for(parent_window)
            self.set_modal(True)
        
        self.set_default_size(650, 450)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_border_width(10)
        
        # Initialize system operations
        self.sys_ops = SystemOperations()
        
        # Current state
        self.selected_disk = None
        self.partition_combos = {}
        self.btrfs_subvol_combos = {}
        self.current_partitions = []
        
        # Create UI
        self._create_ui()
        
        # Load disks
        self.load_disks()
    
    def _create_ui(self):
        """Create the user interface."""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(main_box)
        
        # Title
        title_label = Gtk.Label()
        title_label.set_text(_('System Rescue'))
        title_label.get_style_context().add_class(CSS_CLASSES['dialog_title'])
        main_box.pack_start(title_label, False, False, 5)
        
        # Description
        desc_label = Gtk.Label(label=_("Select a disk to mount an existing Linux installation for rescue or repair."))
        desc_label.set_line_wrap(True)
        main_box.pack_start(desc_label, False, False, 5)
        
        # Disk list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(150)
        main_box.pack_start(scrolled, True, True, 0)
        
        # Disk store: Device, Size, Model
        self.disks_store = Gtk.ListStore(str, str, str)
        self.disks_view = Gtk.TreeView(model=self.disks_store)
        
        # Columns
        columns = [
            (_("Device"), 0),
            (_("Size"), 1),
            (_("Model"), 2)
        ]
        
        for title, col_id in columns:
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=col_id)
            column.set_resizable(True)
            self.disks_view.append_column(column)
        
        scrolled.add(self.disks_view)
        
        # GParted button
        gparted_btn = Gtk.Button(label=_("Open GParted"))
        gparted_btn.connect("clicked", self._on_gparted_clicked)
        gparted_btn.set_tooltip_text(_("Open GParted partition editor"))
        main_box.pack_start(gparted_btn, False, False, 0)
        
        # Button row
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        main_box.pack_start(button_box, False, False, 0)
        
        # Close button
        close_btn = Gtk.Button(label=_("Close"))
        close_btn.connect("clicked", self._on_close_clicked)
        button_box.pack_start(close_btn, True, True, 0)
        
        # Next button
        next_btn = Gtk.Button(label=_("Next"))
        next_btn.connect("clicked", self._on_next_clicked)
        next_btn.get_style_context().add_class('suggested-action')
        button_box.pack_start(next_btn, True, True, 0)
    
    def load_disks(self):
        """Load available disks into the list."""
        try:
            self.disks_store.clear()
            disks = self.sys_ops.get_disks()
            
            for device, size, model in disks:
                self.disks_store.append([device, size, model])
            
            if not disks:
                self._show_message(
                    _("No Disks Found"),
                    _("No disk devices were found on this system."),
                    Gtk.MessageType.WARNING
                )
        except Exception as e:
            self._show_message(
                _("Error"),
                _("Error loading disks: {error}").format(error=str(e)),
                Gtk.MessageType.ERROR
            )
    
    def _on_gparted_clicked(self, button):
        """Open GParted."""
        try:
            subprocess.Popen(['pkexec', '/usr/sbin/gparted'],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
        except Exception as e:
            self._show_message(_("Error"), str(e), Gtk.MessageType.ERROR)
    
    def _on_next_clicked(self, button):
        """Proceed to partition selection."""
        selection = self.disks_view.get_selection()
        model, iter = selection.get_selected()
        
        if iter is None:
            self._show_message(
                _("No Selection"),
                _("Please select a disk to continue."),
                Gtk.MessageType.WARNING
            )
            return
        
        self.selected_disk = model[iter][0]
        
        try:
            partitions = self.sys_ops.get_disk_partitions(self.selected_disk)
            self.current_partitions = partitions
            self._show_partitions_dialog(partitions)
        except Exception as e:
            self._show_message(
                _("Error"),
                _("Error loading partitions: {error}").format(error=str(e)),
                Gtk.MessageType.ERROR
            )
    
    def _show_partitions_dialog(self, partitions: List[Dict]):
        """Show dialog for partition selection."""
        dialog = Gtk.Dialog(
            title=_("Select Partitions"),
            parent=self,
            flags=Gtk.DialogFlags.MODAL,
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK, Gtk.ResponseType.OK
            )
        )
        dialog.set_default_size(600, 500)
        
        box = dialog.get_content_area()
        box.set_spacing(10)
        box.set_border_width(10)
        
        if not partitions:
            label = Gtk.Label(label=_("No mountable partitions found on this disk."))
            box.pack_start(label, False, False, 0)
            box.show_all()
            dialog.run()
            dialog.destroy()
            return
        
        # Header
        header_label = Gtk.Label()
        header_label.set_text(_('Assign mount points to partitions'))
        header_label.get_style_context().add_class(CSS_CLASSES['features_header'])
        box.pack_start(header_label, False, False, 0)
        
        # Partition grid
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(8)
        box.pack_start(grid, True, True, 0)
        
        # Headers
        headers = [_("Mount Point"), _("Device"), _("Size"), _("Filesystem")]
        for i, header in enumerate(headers):
            label = Gtk.Label()
            label.set_text(header)
            label.get_style_context().add_class(CSS_CLASSES['features_header'])
            label.set_halign(Gtk.Align.START)
            grid.attach(label, i, 0, 1, 1)
        
        # Mount points
        mount_points = ['/', '/boot', '/boot/efi', '/home']
        self.partition_combos = {}
        self.btrfs_subvol_combos = {}
        
        row = 1
        for mount in mount_points:
            # Mount point label
            mount_label = Gtk.Label(label=mount)
            mount_label.set_halign(Gtk.Align.START)
            grid.attach(mount_label, 0, row, 1, 1)
            
            # Partition combo
            combo = Gtk.ComboBoxText()
            combo.append("none", _("-- Not used --"))
            
            for part in partitions:
                device = part.get('device', '')
                size = part.get('size', '')
                fstype = part.get('fstype', 'unknown')
                label_text = f"{device} ({size}, {fstype})"
                combo.append(device, label_text)
            
            combo.set_active(0)
            combo.connect("changed", self._on_partition_selected, mount)
            grid.attach(combo, 1, row, 1, 1)
            self.partition_combos[mount] = combo
            
            # Size label (will be updated when partition selected)
            size_label = Gtk.Label(label="-")
            size_label.set_halign(Gtk.Align.START)
            grid.attach(size_label, 2, row, 1, 1)
            
            # Filesystem label
            fs_label = Gtk.Label(label="-")
            fs_label.set_halign(Gtk.Align.START)
            grid.attach(fs_label, 3, row, 1, 1)
            
            row += 1
        
        # Btrfs subvolume section (shown conditionally)
        self.btrfs_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.btrfs_section.set_no_show_all(True)
        box.pack_start(self.btrfs_section, False, False, 10)
        
        btrfs_label = Gtk.Label()
        btrfs_label.set_text(_('Btrfs Subvolumes'))
        btrfs_label.get_style_context().add_class(CSS_CLASSES['features_header'])
        self.btrfs_section.pack_start(btrfs_label, False, False, 0)
        
        box.show_all()
        
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            self._perform_mount()
        
        dialog.destroy()
    
    def _on_partition_selected(self, combo, mount_point: str):
        """Handle partition selection for a mount point."""
        device_id = combo.get_active_id()
        
        if device_id and device_id != "none":
            # Find partition info
            for part in self.current_partitions:
                if part.get('device') == device_id:
                    # Check if btrfs
                    if part.get('is_btrfs') or part.get('fstype', '').lower() == 'btrfs':
                        self._show_btrfs_options(mount_point, part)
                    break
    
    def _show_btrfs_options(self, mount_point: str, partition: Dict):
        """Show btrfs subvolume options."""
        self.btrfs_section.show()
        
        # Clear previous subvolume combos for this mount
        # Add subvolume selector
        subvol_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        label = Gtk.Label(label=f"{mount_point} {_('subvolume')}:")
        subvol_box.pack_start(label, False, False, 0)
        
        subvol_combo = Gtk.ComboBoxText()
        subvol_combo.append("default", _("Default"))
        
        # Get subvolumes
        btrfs_info = partition.get('btrfs_subvolumes', {})
        subvolumes = btrfs_info.get('subvolumes', [])
        
        for subvol in subvolumes:
            name = subvol.get('name', subvol.get('path', 'unknown'))
            subvol_combo.append(name, name)
        
        subvol_combo.set_active(0)
        subvol_box.pack_start(subvol_combo, True, True, 0)
        
        self.btrfs_section.pack_start(subvol_box, False, False, 0)
        self.btrfs_subvol_combos[mount_point] = subvol_combo
        
        self.btrfs_section.show_all()
    
    def _perform_mount(self):
        """Perform the actual mounting of partitions."""
        mount_config = {}
        
        for mount_point, combo in self.partition_combos.items():
            device_id = combo.get_active_id()
            if device_id and device_id != "none":
                mount_config[mount_point] = {
                    'device': device_id,
                    'subvolume': None
                }
                
                # Check for btrfs subvolume
                if mount_point in self.btrfs_subvol_combos:
                    subvol_combo = self.btrfs_subvol_combos[mount_point]
                    subvol = subvol_combo.get_active_id()
                    if subvol and subvol != "default":
                        mount_config[mount_point]['subvolume'] = subvol
        
        if '/' not in mount_config:
            self._show_message(
                _("Error"),
                _("You must select a partition for the root (/) mount point."),
                Gtk.MessageType.ERROR
            )
            return
        
        # Perform mount
        try:
            success, message = self.sys_ops.mount_system(mount_config)
            
            if success:
                self._show_chroot_terminal()
            else:
                self._show_message(_("Mount Failed"), message, Gtk.MessageType.ERROR)
                
        except Exception as e:
            self._show_message(_("Error"), str(e), Gtk.MessageType.ERROR)
    
    def _show_chroot_terminal(self):
        """Show option to open terminal in chroot environment."""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.NONE,
            text=_("System Mounted Successfully")
        )
        
        dialog.format_secondary_text(
            _("The system has been mounted at {mount_point}.\n\n"
              "You can now open a terminal to perform repairs.").format(
                  mount_point=self.sys_ops.mount_point
              )
        )
        
        dialog.add_button(_("Close"), Gtk.ResponseType.CLOSE)
        dialog.add_button(_("Open Terminal"), Gtk.ResponseType.YES)
        dialog.add_button(_("Unmount"), Gtk.ResponseType.NO)
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            self._open_chroot_terminal()
        elif response == Gtk.ResponseType.NO:
            self._unmount_system()
    
    def _open_chroot_terminal(self):
        """Open a terminal in the chroot environment."""
        try:
            # Try common terminal emulators
            terminals = [
                ['xfce4-terminal', '-e'],
                ['konsole', '-e'],
                ['gnome-terminal', '--'],
                ['xterm', '-e']
            ]
            
            chroot_cmd = f"arch-chroot {self.sys_ops.mount_point} /bin/bash"
            
            for term_cmd in terminals:
                try:
                    full_cmd = ['pkexec'] + term_cmd + [chroot_cmd]
                    subprocess.Popen(full_cmd,
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
                    return
                except FileNotFoundError:
                    continue
            
            # Fallback message
            self._show_message(
                _("Terminal Not Found"),
                _("Could not find a terminal emulator.\n\n"
                  "To access the chroot manually, run:\n"
                  "sudo arch-chroot {mount_point}").format(
                      mount_point=self.sys_ops.mount_point
                  ),
                Gtk.MessageType.INFO
            )
            
        except Exception as e:
            self._show_message(_("Error"), str(e), Gtk.MessageType.ERROR)
    
    def _unmount_system(self):
        """Unmount the system."""
        try:
            success, message = self.sys_ops.unmount_system()
            
            if success:
                self._show_message(
                    _("Unmounted"),
                    _("The system has been unmounted successfully."),
                    Gtk.MessageType.INFO
                )
            else:
                self._show_message(_("Error"), message, Gtk.MessageType.ERROR)
                
        except Exception as e:
            self._show_message(_("Error"), str(e), Gtk.MessageType.ERROR)
    
    def _on_close_clicked(self, button):
        """Close the window."""
        # Check if system is mounted and offer to unmount
        if hasattr(self.sys_ops, 'is_mounted') and self.sys_ops.is_mounted():
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=Gtk.DialogFlags.MODAL,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text=_("Unmount System?")
            )
            dialog.format_secondary_text(_("Do you want to unmount the system before closing?"))
            
            response = dialog.run()
            dialog.destroy()
            
            if response == Gtk.ResponseType.YES:
                self._unmount_system()
        
        self.destroy()
    
    def _show_message(self, title: str, message: str, msg_type=Gtk.MessageType.INFO):
        """Show a message dialog."""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=Gtk.DialogFlags.MODAL,
            message_type=msg_type,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
