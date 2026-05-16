"""
Rescue operations window for Soplos Welcome Live.
Shown after successful chroot mount, offers guided rescue operations for novice users.
"""

import gi
import threading
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from core.i18n_manager import _
from ui import CSS_CLASSES


class RescueWindow(Gtk.Window):
    def __init__(self, parent, sys_ops, root_partition):
        Gtk.Window.__init__(self, title=_("System Rescue"))
        self.set_default_size(580, 370)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_border_width(15)
        self.set_transient_for(parent)
        self.set_modal(True)

        self.sys_ops = sys_ops
        self.root_partition = root_partition
        self.parent_window = parent

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.add(main_box)

        # Title
        title = Gtk.Label()
        title.set_markup(f"<span size='large' weight='bold'>{_('Rescue Operations')}</span>")
        title.set_halign(Gtk.Align.START)
        main_box.pack_start(title, False, False, 0)

        # Description
        desc = Gtk.Label(label=_("Select an operation to perform on the mounted system."))
        desc.set_halign(Gtk.Align.START)
        desc.get_style_context().add_class('dim-label')
        main_box.pack_start(desc, False, False, 0)

        # Operation buttons
        btn_grid = Gtk.Grid()
        btn_grid.set_column_spacing(10)
        btn_grid.set_row_spacing(10)
        btn_grid.set_column_homogeneous(True)
        btn_grid.set_hexpand(True)
        main_box.pack_start(btn_grid, False, False, 0)

        operations = [
            ('dialog-password', _("Reset Password"), _("Change a user's password."), self._on_reset_password),
            ('system-software-update', _("Repair GRUB"), _("Reinstall and update GRUB bootloader."), self._on_repair_grub),
            ('view-refresh', _("Update GRUB"), _("Run update-grub to refresh boot entries."), self._on_update_grub),
            ('applications-system', _("Regenerate initramfs"), _("Rebuild initramfs with dracut."), self._on_regen_initramfs),
        ]

        self.op_buttons = []
        for i, (icon_name, label_text, tooltip, handler) in enumerate(operations):
            btn = Gtk.Button()
            btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            btn_icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
            btn_label = Gtk.Label(label=label_text)
            btn_box.pack_start(btn_icon, False, False, 0)
            btn_box.pack_start(btn_label, False, False, 0)
            btn.add(btn_box)
            btn.set_size_request(-1, 42)
            btn.set_hexpand(True)
            btn.set_tooltip_text(tooltip)
            btn.get_style_context().add_class(CSS_CLASSES.get('button_secondary', 'button-secondary'))
            btn.connect('clicked', handler)
            btn_grid.attach(btn, i % 2, i // 2, 1, 1)
            self.op_buttons.append(btn)

        # Output area with frame
        output_frame = Gtk.Frame(label=_("Output"))
        output_frame.set_shadow_type(Gtk.ShadowType.IN)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 130)

        self.output_view = Gtk.TextView()
        self.output_view.set_editable(False)
        self.output_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.output_view.set_left_margin(8)
        self.output_view.set_right_margin(8)
        self.output_view.set_top_margin(6)
        self.output_buffer = self.output_view.get_buffer()
        scrolled.add(self.output_view)
        output_frame.add(scrolled)
        main_box.pack_start(output_frame, True, True, 0)

        # Bottom buttons
        bottom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        main_box.pack_start(bottom_box, False, False, 0)

        self.terminal_btn = Gtk.Button()
        term_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        term_icon = Gtk.Image.new_from_icon_name('utilities-terminal', Gtk.IconSize.BUTTON)
        term_label = Gtk.Label(label=_("Open Terminal"))
        term_box.pack_start(term_icon, False, False, 0)
        term_box.pack_start(term_label, False, False, 0)
        self.terminal_btn.add(term_box)
        self.terminal_btn.set_tooltip_text(_("Open a bash shell inside the chroot environment."))
        self.terminal_btn.connect('clicked', self._on_open_terminal)
        bottom_box.pack_start(self.terminal_btn, False, False, 0)

        close_btn = Gtk.Button(label=_("Close & Unmount"))
        close_btn.set_tooltip_text(_("Unmount all partitions and close this window."))
        close_btn.get_style_context().add_class('destructive-action')
        close_btn.connect('clicked', self._on_close)
        bottom_box.pack_end(close_btn, False, False, 0)

        self.show_all()

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _set_output(self, text):
        self.output_buffer.set_text(text)

    def _run_async(self, func, *args):
        """Run an operation in a background thread and update output."""
        self._set_output(_("Running..."))

        def run():
            try:
                result = func(*args)
                GLib.idle_add(self._set_output, result)
            except Exception as e:
                GLib.idle_add(self._set_output,
                              _("Error: {error}").format(error=str(e)))

        threading.Thread(target=run, daemon=True).start()

    # ── Handlers ─────────────────────────────────────────────────────────────

    def _on_reset_password(self, button):
        dialog = Gtk.Dialog(title=_("Reset User Password"), parent=self, flags=0)
        dialog.set_default_size(360, 0)

        box = dialog.get_content_area()
        box.set_spacing(10)
        box.set_border_width(15)

        for field_label, attr, visible in [
            (_("Username:"), 'user_entry', True),
            (_("New password:"), 'pass_entry', False),
            (_("Confirm:"), 'confirm_entry', False),
        ]:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            lbl = Gtk.Label(label=field_label)
            lbl.set_width_chars(14)
            lbl.set_halign(Gtk.Align.END)
            entry = Gtk.Entry()
            entry.set_visibility(visible)
            setattr(self, attr, entry)
            row.pack_start(lbl, False, False, 0)
            row.pack_start(entry, True, True, 0)
            box.pack_start(row, False, False, 0)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_box.set_halign(Gtk.Align.END)

        cancel_btn = Gtk.Button(label=_("Cancel"))
        cancel_btn.connect('clicked', lambda w: dialog.response(Gtk.ResponseType.CANCEL))
        btn_box.pack_start(cancel_btn, False, False, 0)

        apply_btn = Gtk.Button(label=_("Apply"))
        apply_btn.get_style_context().add_class('suggested-action')
        apply_btn.connect('clicked', lambda w: dialog.response(Gtk.ResponseType.OK))
        btn_box.pack_start(apply_btn, False, False, 0)

        box.pack_start(btn_box, False, False, 0)
        box.show_all()

        response = dialog.run()
        username = self.user_entry.get_text().strip()
        password = self.pass_entry.get_text()
        confirm = self.confirm_entry.get_text()
        dialog.destroy()

        if response != Gtk.ResponseType.OK:
            return
        if not username:
            self._set_output(_("Error: Username cannot be empty."))
            return
        if not password:
            self._set_output(_("Error: Password cannot be empty."))
            return
        if password != confirm:
            self._set_output(_("Error: Passwords do not match."))
            return

        self._run_async(self.sys_ops.reset_user_password, username, password)

    def _on_repair_grub(self, button):
        self._run_async(self.sys_ops.repair_grub, self.root_partition)

    def _on_update_grub(self, button):
        self._run_async(self.sys_ops.update_grub)

    def _on_regen_initramfs(self, button):
        self._run_async(self.sys_ops.regenerate_initramfs)

    def _on_open_terminal(self, button):
        try:
            # Disable all operation buttons — terminal script unmounts on exit
            for btn in self.op_buttons:
                btn.set_sensitive(False)
            self.terminal_btn.set_sensitive(False)
            self._set_output(_("Terminal opened. Operations are disabled while the terminal is active.\nClick 'Close & Unmount' when you are done."))
            self.sys_ops.open_chroot_terminal()
        except Exception as e:
            self._set_output(_("Error: {error}").format(error=str(e)))

    def _on_close(self, button):
        self.sys_ops.unmount_all()
        self.destroy()
        self.parent_window.destroy()
