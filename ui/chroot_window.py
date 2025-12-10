import gi
import os
import subprocess
import shutil
import sys
from pathlib import Path

# Add the root directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
from core.chroot_operations import SystemOperations
from core.i18n_manager import _
from ui import CSS_CLASSES

# Disable accessibility warnings
os.environ['NO_AT_BRIDGE'] = '1'

class ChRootWindow(Gtk.Window):
    def __init__(self, parent=None):
        # Clean pycache before initializing
        self.clean_pycache()
        
        Gtk.Window.__init__(self, title=_("System Rescue"))
        self.set_default_size(650, 450)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_border_width(10)
        
        if parent:
            self.set_transient_for(parent)
            self.set_modal(True)
        
        self.sys_ops = SystemOperations()
        
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(main_box)
        
        # Title label
        title_label = Gtk.Label()
        title_label.set_markup(f"<span size='large' weight='bold'>{_('Select disk to rescue')}</span>")
        title_label.get_style_context().add_class(CSS_CLASSES.get('dialog_title', 'dialog-title'))
        main_box.pack_start(title_label, False, False, 10)
        
        # Disk list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        main_box.pack_start(scrolled, True, True, 0)
        
        self.disks_store = Gtk.ListStore(str, str, str)  # Device, Size, Model
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
            self.disks_view.append_column(column)
        
        scrolled.add(self.disks_view)
        
        # GParted Button
        gparted_button = Gtk.Button(label=_("Open GParted"))
        gparted_button.set_use_underline(True)
        gparted_button.connect("clicked", self.on_gparted_clicked)
        main_box.pack_start(gparted_button, False, False, 0)
        
        # Bottom buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        main_box.pack_start(button_box, False, False, 0)
        
        close_button = Gtk.Button(label=_("Close"))
        close_button.set_use_underline(True)
        close_button.connect("clicked", self.on_close_clicked)
        button_box.pack_start(close_button, True, True, 0)
        
        next_button = Gtk.Button(label=_("Next"))
        next_button.set_use_underline(True)
        next_button.connect("clicked", self.on_next_clicked)
        next_button.get_style_context().add_class(CSS_CLASSES.get('suggested_action', 'suggested-action'))
        button_box.pack_start(next_button, True, True, 0)
        
        # Load disks
        self.load_disks()
    
    def load_disks(self):
        """Loads the list of disks"""
        try:
            self.disks_store.clear()
            for device, size, model in self.sys_ops.get_disks():
                self.disks_store.append([device, size, model])
        except Exception as e:
            self.show_error(
                _("Error"),
                _("Error loading disks: {}").format(str(e))
            )
    
    def on_gparted_clicked(self, button):
        """Executes GParted"""
        try:
            # Run GParted directly with pkexec
            subprocess.Popen(['pkexec', '/usr/sbin/gparted'], 
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
        except Exception as e:
            self.show_error(_("Error"), str(e))
    
    def on_next_clicked(self, button):
        """Proceeds to the next step"""
        selection = self.disks_view.get_selection()
        model, iter = selection.get_selected()
        
        # Error messages
        if iter is None:
            self.show_error(
                _("Error"),
                _("Please select a disk to continue.")
            )
            return
        
        selected_disk = model[iter][0]
        # print(f"DEBUG: Selected disk: {selected_disk}")
        
        try:
            # Get disk partitions
            partitions = self.sys_ops.get_disk_partitions(selected_disk)
            
            # Show partitions selection dialog
            self.show_partitions_dialog(partitions)
        except Exception as e:
            self.show_error(
                _("Error"),
                _("Error loading partitions: {}").format(str(e))
            )
    
    def show_partitions_dialog(self, partitions):
        """Show dialog for partition selection with btrfs support and filtered options"""
        self.current_partitions = partitions
        
        dialog = Gtk.Dialog(
            title=_("Select Partitions"),
            parent=self,
            flags=0,
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK, Gtk.ResponseType.OK
            )
        )
        dialog.set_default_size(600, 500)
        
        # Configure Alt+key shortcuts for dialog buttons
        for button in dialog.get_action_area().get_children():
            button.set_use_underline(True)
        
        box = dialog.get_content_area()
        box.set_spacing(10)
        box.set_border_width(10)
        
        if not partitions:
            label = Gtk.Label(label=_("No partitions found on this disk."))
            box.pack_start(label, False, False, 0)
            box.show_all()
            dialog.run()
            dialog.destroy()
            return
            
        label = Gtk.Label(label=_("Assign mount points to partitions"))
        label.get_style_context().add_class(CSS_CLASSES.get('features_header', 'features-header'))
        box.pack_start(label, False, False, 0)
        
        # Partition list
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(5)
        
        # Create headers
        headers = [
            _("Mount Point"),
            _("Device"),
            _("Size"),
            _("Filesystem")
        ]
        for i, header in enumerate(headers):
            label = Gtk.Label(label=header)
            label.set_markup(f"<b>{header}</b>")
            grid.attach(label, i, 0, 1, 1)
        
        # Create partition rows
        mount_points = ['/', '/boot', '/boot/efi', '/home']
        self.partition_combos = {}
        self.btrfs_subvol_combos = {}

        current_row = 1
        for mount in mount_points:
            mount_label = Gtk.Label(label=mount)
            mount_label.set_halign(Gtk.Align.START)
            grid.attach(mount_label, 0, current_row, 1, 1)

            combo = Gtk.ComboBoxText()
            combo.append_text(_("Select option"))

            # Filter partitions/subvolumes according to the mount point (Legacy Logic)
            for part in partitions:
                fstype = (part.get('fstype') or '').lower()
                label = (part.get('label') or '').lower()
                suggested = part.get('suggested_mount')
                is_btrfs = part.get('is_btrfs', False)
                btrfs_info = part.get('btrfs_subvolumes') if is_btrfs and 'btrfs_subvolumes' in part else None

                show = False
                if mount == '/':
                    if fstype in ['ext2', 'ext3', 'ext4', 'xfs', 'btrfs', 'f2fs', 'reiserfs', 'jfs']:
                        show = True
                elif mount == '/boot':
                    if fstype in ['ext2', 'ext3', 'ext4', 'xfs'] and ('boot' in label or suggested == '/boot'):
                        show = True
                elif mount == '/boot/efi':
                    # Legacy aggressive check: Show ALL FAT partitions
                    if fstype in ['vfat', 'fat32', 'fat16', 'fat']:
                        show = True
                elif mount == '/home':
                    if fstype in ['ext2', 'ext3', 'ext4', 'xfs', 'btrfs', 'f2fs', 'reiserfs', 'jfs']:
                        # Btrfs subvolume check
                        if is_btrfs and btrfs_info and btrfs_info.get('has_subvolumes') and 'subvolumes' in btrfs_info:
                            for subvol in btrfs_info['subvolumes']:
                                if subvol.get('suggested_mount') == '/home' or 'home' in (subvol.get('path') or '').lower():
                                    show = True
                                    break
                        elif 'home' in label or suggested == '/home' or not is_btrfs:
                            show = True

                if show:
                    text = f"{part['device']} ({part['size']} - {part['fstype']})"
                    combo.append_text(text)

            combo.set_active(0)
            
            # Automatic selection if there is a suggestion
            for j, part in enumerate(partitions):
                if part.get('suggested_mount') == mount:
                    # Find matching text in combo
                    combo_text = f"{part['device']} ({part['size']} - {part['fstype']})"
                    model = combo.get_model()
                    for i in range(len(model)):
                        if model[i][0] == combo_text:
                            combo.set_active(i)
                            break

            self.partition_combos[mount] = combo
            combo.connect("changed", self.on_partition_combo_changed, mount, partitions, grid)
            grid.attach(combo, 1, current_row, 3, 1)
            current_row += 1

        box.pack_start(grid, True, True, 0)
        box.show_all()
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.process_selected_partitions()
        dialog.destroy()
    
    def on_partition_combo_changed(self, combo, mount_point, partitions, grid):
        """Handle partition selection change, showing btrfs options if necessary"""
        selection = combo.get_active_text()
        
        # Remove previous subvolume combo if exists
        if mount_point in self.btrfs_subvol_combos:
            old_combo = self.btrfs_subvol_combos[mount_point]
            grid.remove(old_combo)
            del self.btrfs_subvol_combos[mount_point]
        
        if selection and selection != _("Select option"):
            device = selection.split()[0]
            # Find corresponding partition
            selected_partition = None
            for part in partitions:
                if part['device'] == device:
                    selected_partition = part
                    break
            
            # Show subvolume combo if btrfs with subvolumes
            if (
                selected_partition and
                selected_partition.get('is_btrfs') and
                'btrfs_subvolumes' in selected_partition and
                selected_partition['btrfs_subvolumes'] and
                selected_partition['btrfs_subvolumes'].get('has_subvolumes') and
                'subvolumes' in selected_partition['btrfs_subvolumes']
            ):
                btrfs_info = selected_partition['btrfs_subvolumes']
                self.show_btrfs_subvolume_combo(mount_point, btrfs_info, grid, combo)

    def show_btrfs_subvolume_combo(self, mount_point, btrfs_info, grid, partition_combo):
        """Show combo for btrfs subvolume selection"""
        # Find partition combo row
        row = None
        for child in grid.get_children():
            if child == partition_combo:
                row = grid.child_get_property(child, "top-attach")
                break
        
        if row is None:
            return
        
        # Create combo for subvolumes
        subvol_combo = Gtk.ComboBoxText()
        subvol_combo.append_text(_("Select subvolume"))
        
        # Add subvolumes
        for subvol in btrfs_info['subvolumes']:
            is_default = " (default)" if subvol.get('is_default') else ""
            suggested = f" -> {subvol['suggested_mount']}" if subvol.get('suggested_mount') else ""
            text = f"{subvol['path']} (ID: {subvol['id']}){is_default}{suggested}"
            subvol_combo.append_text(text)
        
        # Auto-select if there's a suggestion
        for i, subvol in enumerate(btrfs_info['subvolumes'], 1):
            if subvol.get('suggested_mount') == mount_point or subvol.get('is_default'):
                subvol_combo.set_active(i)
                break
        else:
            subvol_combo.set_active(0)
        
        self.btrfs_subvol_combos[mount_point] = subvol_combo
        
        # Insert new row for subvolume combo
        grid.insert_row(row + 1)
        
        # Label for subvolume
        subvol_label = Gtk.Label()
        subvol_label.set_markup(f"<i>{_('Select subvolume')}:</i>")
        subvol_label.set_halign(Gtk.Align.START)
        grid.attach(subvol_label, 0, row + 1, 1, 1)
        
        grid.attach(subvol_combo, 1, row + 1, 3, 1)
        grid.show_all()

    def process_selected_partitions(self):
        """Processes the selected partitions and executes chroot"""
        try:
            mount_points = {}
            subvolumes = {}
            
            for mount, combo in self.partition_combos.items():
                device = combo.get_active_text()
                if device and device != _("Select option"):
                    device = device.split()[0]  # Get only the device
                    mount_points[mount] = device
                    
                    # Get subvolume if exists
                    if mount in self.btrfs_subvol_combos:
                        subvol_combo = self.btrfs_subvol_combos[mount]
                        subvol_text = subvol_combo.get_active_text()
                        if subvol_text and subvol_text != _("Select subvolume"):
                            # Extract the subvolume path (format: "path (ID: X)")
                            subvol_path = subvol_text.split(' (ID:')[0]
                            subvolumes[mount] = subvol_path

            # Auto-detect @ and @home subvolumes for the same partition
            if '/' in mount_points:
                root_device = mount_points['/']
                
                # Auto-detect @ subvolume for root if not manually selected
                if '/' not in subvolumes:
                    for partition in self.current_partitions:
                        if partition['device'] == root_device and partition.get('is_btrfs'):
                            btrfs_info = partition.get('btrfs_subvolumes')
                            if btrfs_info and btrfs_info.get('has_subvolumes'):
                                for subvol in btrfs_info['subvolumes']:
                                    if subvol['path'] == '@':
                                        subvolumes['/'] = '@'
                                        break
                
                # Auto-detect @home for /home on the same btrfs partition
                if '/home' not in mount_points:
                    for partition in self.current_partitions:
                        if partition['device'] == root_device and partition.get('is_btrfs'):
                            btrfs_info = partition.get('btrfs_subvolumes')
                            if btrfs_info and btrfs_info.get('has_subvolumes'):
                                for subvol in btrfs_info['subvolumes']:
                                    if subvol['path'] == '@home':
                                        mount_points['/home'] = root_device  # Use the same partition
                                        subvolumes['/home'] = '@home'
                                        break

            if '/' not in mount_points:
                self.show_error(
                    _("Error"),
                    _("You must select a root partition (/).")
                )
                return

            # Show a progress dialog
            self.show_progress_dialog(mount_points, subvolumes)
            
        except Exception as e:
            self.show_error(
                _("Error"), 
                str(e)
            )
    
    def show_progress_dialog(self, mount_points, subvolumes=None):
        """Shows a progress dialog while mounting and preparing chroot"""
        if subvolumes is None:
            subvolumes = {}
            
        dialog = Gtk.Dialog(
            title=_("Mounting system..."),
            parent=self,
            flags=0,
            buttons=(
                _("Close"), Gtk.ResponseType.CLOSE,
            )
        )
        dialog.set_default_size(400, 100)
        dialog.set_modal(True)
        
        for button in dialog.get_action_area().get_children():
            button.set_use_underline(True)
        
        box = dialog.get_content_area()
        box.set_spacing(10)
        box.set_border_width(10)
        
        label = Gtk.Label(label=_("Mounting partitions..."))
        box.pack_start(label, False, False, 0)
        
        progress_bar = Gtk.ProgressBar()
        progress_bar.set_fraction(0.0)
        box.pack_start(progress_bar, False, False, 5)
        
        status_label = Gtk.Label(label="")
        box.pack_start(status_label, False, False, 0)
        
        box.show_all()
        
        # Update progress and execute chroot
        def update_progress():
            try:
                # Mock progress sequence matching legacy feel
                status_label.set_text(_("Mounting partitions..."))
                progress_bar.set_fraction(0.3)
                while Gtk.events_pending():
                    Gtk.main_iteration()
                
                progress_bar.set_fraction(0.5)
                status_label.set_text(_("Mounting virtual filesystems..."))
                while Gtk.events_pending():
                    Gtk.main_iteration()
                
                # Execute blocking mount (identical to legacy logic)
                self.sys_ops.mount_and_chroot(
                    root_part=mount_points['/'],
                    boot_part=mount_points.get('/boot'),
                    efi_part=mount_points.get('/boot/efi'),
                    home_part=mount_points.get('/home'),
                    root_subvol=subvolumes.get('/'),
                    home_subvol=subvolumes.get('/home')
                )
                
                progress_bar.set_fraction(1.0)
                status_label.set_text(_("Chroot started successfully in new terminal."))
                
                # Automatically close dialog after 2 seconds
                GLib.timeout_add(2000, dialog.response, Gtk.ResponseType.CLOSE)
                
            except Exception as e:
                progress_bar.set_fraction(0.0)
                status_label.set_markup(f"<span color='red'>{_('Error')}: {str(e)}</span>")
                # Show specific error dialog
                self.show_mount_error(str(e))
                
            return False
        
        # Start the task after showing the dialog
        GLib.idle_add(update_progress)
        
        dialog.run()
        dialog.destroy()
    
    def on_close_clicked(self, button):
        """Closes the window"""
        self.clean_pycache()
        self.destroy()
    
    def show_error(self, title, message):
        """Shows an error dialog"""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def show_mount_error(self, error_message):
        """Shows a specific error dialog for mounting problems"""
        if any(keyword in error_message.lower() for keyword in ['valid linux', 'linux válido', 'linux valido']):
            self.show_error(
                _("Invalid Linux System"),
                _("The mounted system does not appear to be a valid Linux installation. Essential files (like /bin/bash or /etc/fstab) are missing.")
            )
        else:
            self.show_error(
                _("Mount Error"),
                _("An error occurred while mounting the system: {}").format(error_message)
            )
    
    def clean_pycache(self):
        """Cleans all project __pycache__ files"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for root, dirs, files in os.walk(base_dir):
            if '__pycache__' in dirs:
                try:
                    shutil.rmtree(os.path.join(root, '__pycache__'))
                except:
                    pass
