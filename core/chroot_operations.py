"""
System operations for chroot functionality.
Handles disk detection, partition management, mounting, and chroot operations.
Replicates legacy logic for robustness and compatibility.
"""

import subprocess
import os
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.i18n_manager import _


class SystemOperations:
    """
    Handles system operations for disk mounting and chroot.
    Replicates legacy functionality from Soplos Welcome 1.0 (Tyron/Tyson).
    """
    
    def __init__(self):
        """Initialize system operations."""
        self.mount_point = "/mnt/chroot"
        self._is_mounted = False
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def format_size(self, size) -> str:
        """Convert byte sizes to readable format."""
        try:
            size_val = int(size)
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if size_val < 1024.0:
                    return f"{size_val:.1f} {unit}"
                size_val /= 1024.0
            return f"{size_val:.1f} TB"
        except (ValueError, TypeError):
            return "Unknown"
    
    def get_disks(self) -> List[Tuple[str, str, str]]:
        """
        Get list of available disk devices.
        Matches legacy output format.
        """
        try:
            cmd = "lsblk -lnp -o NAME,SIZE,MODEL -d"
            output = subprocess.check_output(cmd.split(), text=True)
            
            disks = []
            for line in output.splitlines():
                if line.strip():
                    parts = line.split(maxsplit=2)
                    device = parts[0]
                    
                    # Skip loop devices, ram devices, etc.
                    if any(x in device for x in ['/loop', '/ram', '/zram']):
                        continue
                    
                    size = parts[1] if len(parts) > 1 else "Unknown"
                    model = parts[2] if len(parts) > 2 else _("Unknown Device")
                    
                    disks.append((device, size, model))
            
            return disks
        except Exception as e:
            self.logger.error(f"Error loading disks: {e}")
            return []

    def get_disk_partitions(self, disk_name: str) -> List[Dict[str, Any]]:
        """
        Get partitions for a disk with btrfs support.
        """
        try:
            # Prefer JSON output from lsblk
            cmd = ['lsblk', '-J', '-o', 'NAME,SIZE,FSTYPE,MOUNTPOINT,LABEL,UUID', disk_name]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            partitions = []
            used_suggestions = set()

            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    devices = data.get('blockdevices', [])
                    target = None
                    
                    # Search for device matching disk_name
                    for dev in devices:
                        dev_path = dev.get('path') or ("/dev/" + dev.get('name', ''))
                        if dev_path == disk_name or dev.get('name') == disk_name:
                            target = dev
                            break
                    
                    # If not found at root level, look into children
                    if not target:
                        for dev in devices:
                            for child in dev.get('children', []) or []:
                                cpath = child.get('path') or ("/dev/" + child.get('name', ''))
                                if cpath == disk_name or child.get('name') == disk_name:
                                    target = dev
                                    break
                            if target:
                                break

                    if target:
                        children = target.get('children') or []
                        for part in children:
                            device = part.get('path') or ("/dev/" + part.get('name', ''))
                            size = part.get('size') or ''
                            fstype = part.get('fstype') or 'unknown'
                            mount = part.get('mountpoint') or ''
                            label = part.get('label') or ''
                            uuid = part.get('uuid') or ''

                            if self._is_mountable_filesystem(fstype):
                                btrfs_info = None
                                is_btrfs = False
                                if fstype and fstype.lower() == 'btrfs':
                                    is_btrfs = True
                                    btrfs_info = self._detect_btrfs_subvolumes(device)

                                suggested = self._suggest_mount_point_intelligent(fstype, label, mount, used_suggestions, btrfs_info)
                                if suggested:
                                    used_suggestions.add(suggested)

                                partition_data = {
                                    'device': device,
                                    'size': size,
                                    'fstype': fstype,
                                    'mountpoint': mount,
                                    'label': label,
                                    'uuid': uuid,
                                    'suggested_mount': suggested,
                                    'is_btrfs': is_btrfs
                                }

                                if btrfs_info and btrfs_info.get('has_subvolumes'):
                                    partition_data['btrfs_subvolumes'] = btrfs_info

                                partitions.append(partition_data)
                    else:
                        raise ValueError("No target in lsblk JSON")
                except Exception as je:
                    self.logger.warning(f"JSON parsing failed, falling back: {je}")
                    # Fallback to text parsing implicitly if this block fails or returns empty
                    return self._get_partitions_text_fallback(disk_name)
            else:
                 return self._get_partitions_text_fallback(disk_name)

            return partitions
        except Exception as e:
            self.logger.error(f"Error in get_disk_partitions: {e}")
            return []

    def _get_partitions_text_fallback(self, disk_name: str) -> List[Dict[str, Any]]:
        """Fallback method using text parsing."""
        try:
            cmd = ['lsblk', '-lnp', '-o', 'NAME,SIZE,FSTYPE,MOUNTPOINT,LABEL,UUID', disk_name]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Error executing lsblk text fallback: {result.stderr}")

            partitions = []
            used_suggestions = set()

            for line in result.stdout.strip().split('\n'):
                parts = line.split()
                if not parts or parts[0] == disk_name:
                    continue
                
                device = parts[0]
                size = parts[1] if len(parts) > 1 else ''
                fstype = parts[2] if len(parts) > 2 and parts[2] != '' else 'unknown'
                mount = parts[3] if len(parts) > 3 and parts[3] != '' else ''
                label = parts[4] if len(parts) > 4 and parts[4] != '' else ''
                uuid = parts[5] if len(parts) > 5 and parts[5] != '' else ''

                if self._is_mountable_filesystem(fstype):
                    btrfs_info = None
                    is_btrfs = False
                    if fstype.lower() == 'btrfs':
                        is_btrfs = True
                        btrfs_info = self._detect_btrfs_subvolumes(device)

                    suggested = self._suggest_mount_point_intelligent(fstype, label, mount, used_suggestions, btrfs_info)
                    if suggested:
                        used_suggestions.add(suggested)

                    partition_data = {
                        'device': device,
                        'size': size,
                        'fstype': fstype,
                        'mountpoint': mount,
                        'label': label,
                        'uuid': uuid,
                        'suggested_mount': suggested,
                        'is_btrfs': is_btrfs
                    }

                    if btrfs_info and btrfs_info.get('has_subvolumes'):
                        partition_data['btrfs_subvolumes'] = btrfs_info

                    partitions.append(partition_data)
            return partitions
        except Exception as e:
            self.logger.error(f"Fallback partition detection failed: {e}")
            return []

    def _is_mountable_filesystem(self, fstype: str) -> bool:
        """Check if a filesystem type is mountable."""
        if not fstype:
            return False
        
        mountable = {
            'ext4', 'ext3', 'ext2', 'xfs', 'btrfs', 'f2fs',
            'vfat', 'fat32', 'fat16', 'ntfs', 'exfat', 'jfs', 'reiserfs'
        }
        non_mountable = {'swap', 'extended', 'LVM2_member', 'crypto_LUKS'}
        return fstype.lower() in mountable and fstype.lower() not in non_mountable

    def _detect_btrfs_subvolumes(self, device: str) -> Dict[str, Any]:
        """Detect btrfs subvolumes on a partition."""
        try:
            # Legacy robust method: mount to temp, list, get-default, unmount
            temp_mount = f"/tmp/btrfs_temp_{os.getpid()}"
            os.makedirs(temp_mount, exist_ok=True)
            
            try:
                mount_result = subprocess.run(
                    ['sudo', 'mount', '-t', 'btrfs', device, temp_mount],
                    capture_output=True, text=True, timeout=10
                )
                
                if mount_result.returncode != 0:
                    return {'has_subvolumes': False, 'subvolumes': []}
                
                subvol_result = subprocess.run(
                    ['sudo', 'btrfs', 'subvolume', 'list', temp_mount],
                    capture_output=True, text=True, timeout=10
                )
                
                default_result = subprocess.run(
                    ['sudo', 'btrfs', 'subvolume', 'get-default', temp_mount],
                    capture_output=True, text=True, timeout=10
                )
                
                subvolumes = []
                default_subvol_id = None
                
                if default_result.returncode == 0:
                    for line in default_result.stdout.split('\n'):
                        if 'ID' in line:
                            try:
                                default_subvol_id = line.split()[1]
                            except:
                                pass
                
                if subvol_result.returncode == 0:
                    for line in subvol_result.stdout.split('\n'):
                        if line.strip() and 'ID' in line:
                            try:
                                parts = line.split()
                                if len(parts) >= 9:
                                    subvol_id = parts[1]
                                    subvol_path = parts[8]
                                    
                                    suggested_mount = self._suggest_btrfs_mount_point(subvol_path)
                                    
                                    subvolumes.append({
                                        'id': subvol_id,
                                        'path': subvol_path,
                                        'name': subvol_path.split('/')[-1] if subvol_path else '',
                                        'is_default': subvol_id == default_subvol_id,
                                        'suggested_mount': suggested_mount
                                    })
                            except:
                                continue
                
                return {
                    'subvolumes': subvolumes,
                    'default_subvolume_id': default_subvol_id,
                    'has_subvolumes': len(subvolumes) > 0
                }
                
            finally:
                subprocess.run(['sudo', 'umount', temp_mount], 
                             capture_output=True, timeout=5)
                try:
                    os.rmdir(temp_mount)
                except:
                    pass
                    
        except Exception as e:
            self.logger.error(f"Error detecting btrfs subvolumes: {str(e)}")
            return {'has_subvolumes': False, 'subvolumes': []}

    def _suggest_btrfs_mount_point(self, subvol_path: str) -> Optional[str]:
        """Suggest mount point based on btrfs subvolume name."""
        path_lower = subvol_path.lower()
        
        mount_patterns = {
            '@': '/',
            '@root': '/',
            '@home': '/home',
            '@var': '/var',
            '@tmp': '/tmp',
            '@opt': '/opt',
            '@srv': '/srv',
            '@usr': '/usr',
            '@boot': '/boot',
            'root': '/',
            'home': '/home',
            'var': '/var',
            'tmp': '/tmp'
        }
        
        if subvol_path in mount_patterns:
            return mount_patterns[subvol_path]
        
        for pattern, mount_point in mount_patterns.items():
            if pattern in path_lower:
                return mount_point
                
        return None

    def _suggest_mount_point_intelligent(self, fstype, label, current_mount, used_suggestions, btrfs_info=None):
        """Intelligent mount point suggestions including btrfs."""
        if current_mount and self.mount_point in current_mount:
            current_mount = None

        fstype = (fstype or '').lower()
        label = (label or '').lower()

        # EFI filesystems - Aggressive detection
        if fstype in ['vfat', 'fat32', 'fat16', 'fat']:
            if '/boot/efi' not in used_suggestions:
                return '/boot/efi'
        
        # Btrfs filesystems - Auto-detect @ subvolume
        elif fstype == 'btrfs':
            if btrfs_info and btrfs_info.get('has_subvolumes'):
                # Search for @ or @root subvolume for root
                for subvol in btrfs_info['subvolumes']:
                    if subvol['path'] in ['@', '@root'] and '/' not in used_suggestions:
                        return '/'
                
                # If @ not found, search for default subvolume
                default_subvol = None
                for subvol in btrfs_info['subvolumes']:
                    if subvol.get('is_default'):
                        default_subvol = subvol
                        break
                
                if default_subvol and default_subvol.get('suggested_mount'):
                    suggested = default_subvol['suggested_mount']
                    if suggested not in used_suggestions:
                        return suggested
            
            # Fallback for btrfs without subvolumes
            if '/' not in used_suggestions:
                return '/'
        
        # Linux filesystems
        elif fstype in ['ext2', 'ext3', 'ext4', 'xfs', 'jfs', 'reiserfs', 'f2fs']:
            if 'root' in label or 'system' in label:
                if '/' not in used_suggestions:
                    return '/'
            elif 'home' in label:
                if '/home' not in used_suggestions:
                    return '/home'
            elif 'boot' in label and 'efi' not in label:
                if '/boot' not in used_suggestions:
                    return '/boot'
            
            elif current_mount == '/':
                if '/' not in used_suggestions:
                    return '/'
            elif current_mount == '/home':
                if '/home' not in used_suggestions:
                    return '/home'
            elif current_mount == '/boot':
                if '/boot' not in used_suggestions:
                    return '/boot'
            
            # Priority assignment
            elif '/' not in used_suggestions:
                return '/'
            elif '/boot' not in used_suggestions and fstype in ['ext2', 'ext3', 'ext4']:
                return '/boot'
            elif '/home' not in used_suggestions:
                return '/home'

        return None

    def unmount_all(self) -> bool:
        """Unmounts all partitions and virtual filesystems using safe script."""
        try:
            # Script matching legacy implementation exactly
            unmount_script = f"""#!/bin/bash
# Function to safely unmount a mount point
safe_umount() {{
    local mount_point="$1"
    if mount | grep -q " on $mount_point "; then
        echo "{_('Unmounting')} $mount_point..."
        umount -l "$mount_point" || umount -f "$mount_point" || true
    fi
}}

# Unmount virtual filesystems in reverse order
safe_umount {self.mount_point}/dev/pts
safe_umount {self.mount_point}/dev
safe_umount {self.mount_point}/proc
safe_umount {self.mount_point}/sys
safe_umount {self.mount_point}/boot/efi
safe_umount {self.mount_point}/boot
safe_umount {self.mount_point}/home
safe_umount {self.mount_point}

echo "{_('Unmount completed')}"
"""
            with open('/tmp/unmount.sh', 'w') as f:
                f.write(unmount_script)
            os.chmod('/tmp/unmount.sh', 0o755)
            
            subprocess.run(['sudo', '/tmp/unmount.sh'], check=False)
            self._is_mounted = False
            return True
        except Exception as e:
            self.logger.error(f"Error unmounting the system: {e}")
            return False

    def _validate_mounted_system(self) -> bool:
        """Verifies if the mounted system is a valid Linux."""
        essential_paths = [
            '/bin', '/usr/bin', '/lib', '/usr/lib', 
            '/etc/fstab', '/etc/passwd', '/etc/shadow'
        ]
        
        shell_paths = ['/bin/bash', '/bin/sh', '/usr/bin/bash', '/usr/bin/sh']
        
        essential_found = 0
        for path in essential_paths:
            full_path = os.path.join(self.mount_point, path.lstrip('/'))
            if os.path.exists(full_path):
                essential_found += 1
        
        shell_found = False
        for shell in shell_paths:
            full_path = os.path.join(self.mount_point, shell.lstrip('/'))
            if os.path.exists(full_path):
                shell_found = True
                break
        
        # Valid if >= 3 essential files and a shell
        return essential_found >= 3 and shell_found

    def mount_and_chroot(self, root_part, boot_part=None, efi_part=None, home_part=None, root_subvol=None, home_subvol=None):
        """
        Mounts partitions to /mnt/chroot and sets up the environment.
        Identical legacy logic with updated i18n messages.
        """
        try:
            self.logger.info(f"Starting mount - root={root_part}")
            
            # Clean previous mounts
            self.unmount_all()
            
            # Create mount directory
            subprocess.run(['sudo', 'mkdir', '-p', self.mount_point], check=True)
            
            # Mount root
            if root_subvol:
                mount_cmd = ['sudo', 'mount', '-t', 'btrfs', '-o', f'subvol={root_subvol}', root_part, self.mount_point]
            else:
                mount_cmd = ['sudo', 'mount', root_part, self.mount_point]
                
            result = subprocess.run(mount_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Error mounting root {root_part}: {result.stderr}")

            # Mount /boot
            if boot_part:
                boot_dir = os.path.join(self.mount_point, 'boot')
                subprocess.run(['sudo', 'mkdir', '-p', boot_dir], check=True)
                result = subprocess.run(['sudo', 'mount', boot_part, boot_dir], capture_output=True, text=True)
                if result.returncode != 0:
                    self.logger.warning(f"Could not mount /boot: {result.stderr}")

            # Mount /boot/efi
            if efi_part:
                efi_dir = os.path.join(self.mount_point, 'boot', 'efi')
                subprocess.run(['sudo', 'mkdir', '-p', efi_dir], check=True)
                result = subprocess.run(['sudo', 'mount', efi_part, efi_dir], capture_output=True, text=True)
                if result.returncode != 0:
                    self.logger.warning(f"Could not mount /boot/efi: {result.stderr}")

            # Mount /home
            if home_part:
                home_dir = os.path.join(self.mount_point, 'home')
                subprocess.run(['sudo', 'mkdir', '-p', home_dir], check=True)
                if home_subvol:
                    home_cmd = ['sudo', 'mount', '-t', 'btrfs', '-o', f'subvol={home_subvol}', home_part, home_dir]
                else:
                    home_cmd = ['sudo', 'mount', home_part, home_dir]
                
                result = subprocess.run(home_cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    self.logger.warning(f"Could not mount /home: {result.stderr}")

            # Mount virtual filesystems
            virtual_mounts = [
                ('/dev', 'dev'),
                ('/proc', 'proc'), 
                ('/sys', 'sys'),
                ('/dev/pts', 'dev/pts')
            ]
            
            for source, target in virtual_mounts:
                target_path = os.path.join(self.mount_point, target)
                subprocess.run(['sudo', 'mkdir', '-p', target_path], check=True)
                result = subprocess.run(['sudo', 'mount', '--bind', source, target_path], capture_output=True, text=True)
                if result.returncode != 0:
                    self.logger.warning(f"Could not bind mount {source}: {result.stderr}")

            # Copy resolv.conf
            etc_path = os.path.join(self.mount_point, 'etc')
            if os.path.exists(etc_path):
                subprocess.run(['sudo', 'cp', '/etc/resolv.conf', os.path.join(self.mount_point, 'etc/resolv.conf')], check=False)
            
            # Validate system
            if not self._validate_mounted_system():
                raise Exception(_("The mounted system does not appear to be a valid Linux - essential files not found"))
            
            self._is_mounted = True
            
            # Open terminal
            self._open_chroot_terminal()
            
        except Exception as e:
            self.logger.error(f"Error in mount_and_chroot: {e}")
            self.unmount_all()
            raise e

    def _open_chroot_terminal(self):
        """Opens chroot terminal with DE-specific priorities."""
        from core.environment import get_environment_detector, DesktopEnvironment
        
        chroot_title = _("CHROOT Recovery Environment")
        mount_msg = _("Mount point contents:")
        exit_msg = _("Type 'exit' to leave")
        separator = '=' * 34
        
        # Legacy script generation
        chroot_script = f"""#!/bin/bash
echo "{separator}"
echo "{chroot_title}"
echo "{mount_msg} {self.mount_point}"
echo "{exit_msg}"
echo "{separator}"

# Detect available shell
if [ -x "{self.mount_point}/bin/bash" ]; then
    SHELL_CMD="/bin/bash"
elif [ -x "{self.mount_point}/usr/bin/bash" ]; then
    SHELL_CMD="/usr/bin/bash"
else
    SHELL_CMD="/bin/sh"
fi

# Enter chroot
sudo chroot {self.mount_point} $SHELL_CMD

# Clean up on exit
echo "{_('Cleaning up mounts...')}"
sudo umount -l {self.mount_point}/dev/pts 2>/dev/null || true
sudo umount -l {self.mount_point}/dev 2>/dev/null || true
sudo umount -l {self.mount_point}/proc 2>/dev/null || true
sudo umount -l {self.mount_point}/sys 2>/dev/null || true
sudo umount -l {self.mount_point}/boot/efi 2>/dev/null || true
sudo umount -l {self.mount_point}/boot 2>/dev/null || true
sudo umount -l {self.mount_point}/home 2>/dev/null || true
sudo umount -l {self.mount_point} 2>/dev/null || true
echo "{_('Cleanup completed')}"
"""
        script_path = '/tmp/chroot_recovery.sh'
        with open(script_path, 'w') as f:
            f.write(chroot_script)
        os.chmod(script_path, 0o755)
        
        # Environment setup
        env = os.environ.copy()
        env.update({
            'NO_AT_BRIDGE': '1',
            'XDG_RUNTIME_DIR': f"/run/user/{os.getuid()}",
            'DISPLAY': os.environ.get('DISPLAY', ':0')
        })
        
        # Detect Desktop Environment
        de = get_environment_detector().desktop_environment
        
        # Terminal Definitions (binary -> command list)
        # Note: 'bash script' must be passed as a single arg to -e for some terminals
        terms_db = {
            'kitty': ['kitty', '--title', 'CHROOT Recovery', 'bash', script_path],
            'xfce4-terminal': ['xfce4-terminal', '--title=CHROOT Recovery', '-e', f'bash {script_path}'],
            'konsole': ['konsole', '--title', 'CHROOT Recovery', '-e', f'bash {script_path}'],
            'gnome-terminal': ['gnome-terminal', '--', 'bash', '-c', script_path],
            'ptyxis': ['ptyxis', '--', 'bash', script_path],
            'alacritty': ['alacritty', '-e', 'bash', script_path],
            'xterm': ['xterm', '-title', 'CHROOT Recovery', '-e', 'bash', script_path],
            'uterm': ['uterm', '-e', f'bash {script_path}']
        }

        # Priority Lists based on User Request
        priorities = []
        if de == DesktopEnvironment.XFCE:
            # Xfce: kitty, xfce4-terminal, xterm, uterm...
            priorities = ['kitty', 'xfce4-terminal', 'xterm', 'uterm', 'alacritty', 'gnome-terminal']
        elif de == DesktopEnvironment.KDE:
            # Plasma: Konsole, alacritty, Xterm, uterm...
            priorities = ['konsole', 'alacritty', 'xterm', 'uterm', 'kitty']
        elif de == DesktopEnvironment.GNOME:
            # Gnome: gnome-terminal, ptyxis, alacrity, xterm, uterm...
            priorities = ['gnome-terminal', 'ptyxis', 'alacritty', 'xterm', 'uterm']
        else:
            # Fallback generic list
            priorities = ['kitty', 'xfce4-terminal', 'konsole', 'gnome-terminal', 'ptyxis', 'xterm']

        # Try to launch one
        launched = False
        for term_name in priorities:
            if term_name in terms_db:
                cmd = terms_db[term_name]
                try:
                    # Check if binary exists first to avoid exception spam
                    if not shutil.which(term_name):
                        continue
                        
                    print(f"DEBUG: Attempting to launch {term_name} on {de.value}")
                    subprocess.Popen(cmd, start_new_session=True, env=env,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    launched = True
                    break
                except Exception as e:
                    self.logger.warning(f"Failed to launch {term_name}: {e}")
                    continue
        
        if not launched:
             raise Exception(_("No available terminal found. Please install kitty, xfce4-terminal, konsole, gnome-terminal or ptyxis."))
