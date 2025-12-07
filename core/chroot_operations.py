"""
System operations for chroot functionality.
Handles disk detection, partition management, mounting, and chroot operations.
Supports btrfs subvolumes.
"""

import subprocess
import os
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.i18n_manager import _


class SystemOperations:
    """
    Handles system operations for disk mounting and chroot.
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
            size = int(size)
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        except (ValueError, TypeError):
            return "Unknown"
    
    def get_disks(self) -> List[Tuple[str, str, str]]:
        """
        Get list of available disk devices.
        
        Returns:
            List of tuples: (device_path, size, model)
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
            self.logger.error(f"Error getting disks: {e}")
            return []
    
    def get_disk_partitions(self, disk_name: str) -> List[Dict[str, Any]]:
        """
        Get partitions for a disk with btrfs support.
        
        Args:
            disk_name: Device path (e.g., /dev/sda)
            
        Returns:
            List of partition dictionaries
        """
        try:
            # Use JSON output for reliable parsing
            cmd = ['lsblk', '-J', '-o', 'NAME,SIZE,FSTYPE,MOUNTPOINT,LABEL,UUID', disk_name]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"lsblk failed: {result.stderr}")
            
            partitions = []
            data = json.loads(result.stdout)
            devices = data.get('blockdevices', [])
            
            # Find the target disk
            target = None
            for dev in devices:
                dev_path = dev.get('path') or f"/dev/{dev.get('name', '')}"
                if dev_path == disk_name or f"/dev/{dev.get('name')}" == disk_name:
                    target = dev
                    break
            
            if not target:
                return []
            
            # Process children (partitions)
            children = target.get('children', [])
            
            for part in children:
                device = part.get('path') or f"/dev/{part.get('name', '')}"
                fstype = part.get('fstype') or ''
                
                # Skip non-mountable filesystems
                if not self._is_mountable_filesystem(fstype):
                    continue
                
                partition_data = {
                    'device': device,
                    'size': part.get('size', ''),
                    'fstype': fstype,
                    'mountpoint': part.get('mountpoint', ''),
                    'label': part.get('label', ''),
                    'uuid': part.get('uuid', ''),
                    'is_btrfs': fstype.lower() == 'btrfs'
                }
                
                # Get btrfs subvolumes if applicable
                if partition_data['is_btrfs']:
                    btrfs_info = self._detect_btrfs_subvolumes(device)
                    if btrfs_info.get('has_subvolumes'):
                        partition_data['btrfs_subvolumes'] = btrfs_info
                
                # Suggest mount point
                partition_data['suggested_mount'] = self._suggest_mount_point(
                    fstype, part.get('label', ''), device
                )
                
                partitions.append(partition_data)
            
            return partitions
            
        except json.JSONDecodeError:
            return self._get_partitions_text_fallback(disk_name)
        except Exception as e:
            self.logger.error(f"Error getting partitions: {e}")
            return []
    
    def _get_partitions_text_fallback(self, disk_name: str) -> List[Dict[str, Any]]:
        """Fallback method using text parsing."""
        try:
            cmd = ['lsblk', '-lnp', '-o', 'NAME,SIZE,FSTYPE,MOUNTPOINT,LABEL,UUID', disk_name]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            partitions = []
            for line in result.stdout.strip().split('\n'):
                parts = line.split()
                if not parts or parts[0] == disk_name:
                    continue
                
                device = parts[0]
                fstype = parts[2] if len(parts) > 2 else ''
                
                if not self._is_mountable_filesystem(fstype):
                    continue
                
                partitions.append({
                    'device': device,
                    'size': parts[1] if len(parts) > 1 else '',
                    'fstype': fstype,
                    'mountpoint': parts[3] if len(parts) > 3 else '',
                    'label': parts[4] if len(parts) > 4 else '',
                    'uuid': parts[5] if len(parts) > 5 else '',
                    'is_btrfs': fstype.lower() == 'btrfs'
                })
            
            return partitions
            
        except Exception as e:
            self.logger.error(f"Fallback partition detection failed: {e}")
            return []
    
    def _is_mountable_filesystem(self, fstype: str) -> bool:
        """Check if a filesystem type is mountable."""
        if not fstype:
            return False
        
        mountable = [
            'ext4', 'ext3', 'ext2', 'xfs', 'btrfs', 'f2fs',
            'vfat', 'fat32', 'fat16', 'ntfs', 'exfat'
        ]
        
        return fstype.lower() in mountable
    
    def _detect_btrfs_subvolumes(self, device: str) -> Dict[str, Any]:
        """
        Detect btrfs subvolumes on a partition.
        
        Args:
            device: Device path
            
        Returns:
            Dictionary with subvolume information
        """
        result = {
            'has_subvolumes': False,
            'subvolumes': [],
            'default_subvolume': None
        }
        
        try:
            # Create temporary mount point
            temp_mount = Path("/tmp/soplos_btrfs_detect")
            temp_mount.mkdir(exist_ok=True)
            
            # Mount the partition temporarily
            mount_result = subprocess.run(
                ['mount', '-t', 'btrfs', device, str(temp_mount)],
                capture_output=True, timeout=30
            )
            
            if mount_result.returncode != 0:
                return result
            
            try:
                # List subvolumes
                list_result = subprocess.run(
                    ['btrfs', 'subvolume', 'list', str(temp_mount)],
                    capture_output=True, text=True, timeout=30
                )
                
                if list_result.returncode == 0:
                    for line in list_result.stdout.strip().split('\n'):
                        if line:
                            # Parse: ID xxx gen xxx top level xxx path <path>
                            parts = line.split()
                            if len(parts) >= 9 and 'path' in parts:
                                path_idx = parts.index('path')
                                subvol_path = ' '.join(parts[path_idx + 1:])
                                subvol_id = parts[1] if len(parts) > 1 else ''
                                
                                result['subvolumes'].append({
                                    'id': subvol_id,
                                    'path': subvol_path,
                                    'name': subvol_path.split('/')[-1]
                                })
                
                result['has_subvolumes'] = len(result['subvolumes']) > 0
                
                # Get default subvolume
                default_result = subprocess.run(
                    ['btrfs', 'subvolume', 'get-default', str(temp_mount)],
                    capture_output=True, text=True, timeout=30
                )
                
                if default_result.returncode == 0:
                    result['default_subvolume'] = default_result.stdout.strip()
                    
            finally:
                # Always unmount
                subprocess.run(['umount', str(temp_mount)], capture_output=True)
                temp_mount.rmdir()
            
        except Exception as e:
            self.logger.warning(f"Btrfs detection warning: {e}")
        
        return result
    
    def _suggest_mount_point(self, fstype: str, label: str, device: str) -> Optional[str]:
        """Suggest a mount point based on filesystem and label."""
        label_lower = label.lower()
        
        # Check common patterns
        if 'efi' in label_lower or 'esp' in label_lower or fstype == 'vfat':
            if 'efi' in device.lower() or 'nvme' in device:
                return '/boot/efi'
        
        if 'boot' in label_lower:
            return '/boot'
        
        if 'home' in label_lower:
            return '/home'
        
        if 'root' in label_lower or label_lower == '/':
            return '/'
        
        # If ext4 and larger, likely root
        if fstype == 'ext4':
            return '/'
        
        return None
    
    def mount_system(self, mount_config: Dict[str, Dict]) -> Tuple[bool, str]:
        """
        Mount the system based on configuration.
        
        Args:
            mount_config: Dictionary mapping mount points to device info
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Create base mount point
            base_mount = Path(self.mount_point)
            base_mount.mkdir(parents=True, exist_ok=True)
            
            # Mount root first
            if '/' not in mount_config:
                return (False, _("Root partition (/) not specified"))
            
            root_config = mount_config['/']
            success, msg = self._mount_partition(
                root_config['device'],
                str(base_mount),
                subvolume=root_config.get('subvolume')
            )
            
            if not success:
                return (False, f"Failed to mount root: {msg}")
            
            # Mount other partitions
            for mount_point, config in sorted(mount_config.items()):
                if mount_point == '/':
                    continue
                
                target_path = base_mount / mount_point.lstrip('/')
                target_path.mkdir(parents=True, exist_ok=True)
                
                success, msg = self._mount_partition(
                    config['device'],
                    str(target_path),
                    subvolume=config.get('subvolume')
                )
                
                if not success:
                    self.logger.warning(f"Failed to mount {mount_point}: {msg}")
            
            # Bind mount necessary directories
            self._bind_mount_system_dirs()
            
            self._is_mounted = True
            return (True, _("System mounted successfully"))
            
        except Exception as e:
            return (False, str(e))
    
    def _mount_partition(self, device: str, target: str, 
                         subvolume: Optional[str] = None) -> Tuple[bool, str]:
        """Mount a single partition."""
        try:
            cmd = ['mount']
            
            if subvolume:
                cmd.extend(['-o', f'subvol={subvolume}'])
            
            cmd.extend([device, target])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return (True, "")
            else:
                return (False, result.stderr)
                
        except Exception as e:
            return (False, str(e))
    
    def _bind_mount_system_dirs(self):
        """Bind mount necessary system directories for chroot."""
        bind_dirs = [
            '/dev',
            '/dev/pts',
            '/proc',
            '/sys',
            '/run'
        ]
        
        for src in bind_dirs:
            target = Path(self.mount_point) / src.lstrip('/')
            target.mkdir(parents=True, exist_ok=True)
            
            try:
                if src == '/dev/pts':
                    subprocess.run(['mount', '-t', 'devpts', 'devpts', str(target)],
                                 capture_output=True, timeout=10)
                elif src == '/proc':
                    subprocess.run(['mount', '-t', 'proc', 'proc', str(target)],
                                 capture_output=True, timeout=10)
                elif src == '/sys':
                    subprocess.run(['mount', '-t', 'sysfs', 'sys', str(target)],
                                 capture_output=True, timeout=10)
                else:
                    subprocess.run(['mount', '--bind', src, str(target)],
                                 capture_output=True, timeout=10)
            except Exception as e:
                self.logger.warning(f"Failed to bind mount {src}: {e}")
    
    def unmount_system(self) -> Tuple[bool, str]:
        """Unmount the chroot system."""
        try:
            if not self._is_mounted:
                return (True, _("System was not mounted"))
            
            # Unmount in reverse order
            mount_point = Path(self.mount_point)
            
            # Get all mounted paths under our mount point
            result = subprocess.run(['findmnt', '-R', '-n', '-o', 'TARGET', 
                                    str(mount_point)],
                                   capture_output=True, text=True)
            
            mounted_paths = result.stdout.strip().split('\n')
            mounted_paths = [p for p in mounted_paths if p]
            mounted_paths.reverse()  # Unmount deepest first
            
            for path in mounted_paths:
                try:
                    subprocess.run(['umount', '-l', path], 
                                 capture_output=True, timeout=30)
                except Exception:
                    pass
            
            self._is_mounted = False
            return (True, _("System unmounted successfully"))
            
        except Exception as e:
            return (False, str(e))
    
    def is_mounted(self) -> bool:
        """Check if system is currently mounted."""
        return self._is_mounted
    
    def run_in_chroot(self, command: str) -> Tuple[int, str, str]:
        """
        Run a command in the chroot environment.
        
        Args:
            command: Command to run
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        try:
            result = subprocess.run(
                ['arch-chroot', self.mount_point, '/bin/bash', '-c', command],
                capture_output=True, text=True, timeout=300
            )
            return (result.returncode, result.stdout, result.stderr)
        except Exception as e:
            return (-1, "", str(e))
