import os
import subprocess

class NumlockxManager:
    def __init__(self):
        self.packages_conf = "/etc/calamares/modules/packages.conf"
        self.system_script = "/usr/local/bin/disable-numlockx"  # Use system script

    def disable_numlockx(self):
        """Prepare numlockx deactivation"""
        try:
            # 1. Modify packages.conf to uninstall numlockx
            with open(self.packages_conf, 'r') as f:
                content = f.readlines()
            
            for i, line in enumerate(content):
                if "'soplos-packager'" in line:
                    content.insert(i + 1, "      - 'numlockx'\n")
                    break
            
            with open('/tmp/packages.conf', 'w') as f:
                f.writelines(content)
            
            subprocess.run(['pkexec', 'mv', '/tmp/packages.conf', self.packages_conf], check=True)

            # 2. Modify existing shellprocess.conf to use system script
            if os.path.exists('/etc/calamares/modules/shellprocess.conf'):
                with open('/etc/calamares/modules/shellprocess.conf', 'r') as f:
                    content = f.readlines()
                
                # Find script: section and add our script
                for i, line in enumerate(content):
                    if 'script:' in line:
                        content.insert(i + 1, f'   - "{self.system_script}"\n')
                        break
                
                with open('/tmp/shellprocess.conf', 'w') as f:
                    f.writelines(content)
                
                subprocess.run(['pkexec', 'mv', '/tmp/shellprocess.conf', 
                              '/etc/calamares/modules/shellprocess.conf'], check=True)

        except Exception as e:
            raise Exception(f"Error disabling numlockx: {str(e)}")

    def enable_numlockx(self):
        """Prepare numlockx reactivation"""
        try:
            # 1. Modify packages.conf to keep numlockx
            with open(self.packages_conf, 'r') as f:
                content = f.readlines()
            
            content = [line for line in content if "'numlockx'" not in line]
            
            with open('/tmp/packages.conf', 'w') as f:
                f.writelines(content)
            
            subprocess.run(['pkexec', 'mv', '/tmp/packages.conf', self.packages_conf], check=True)

            # 2. Update shellprocess module configuration
            shellprocess_conf = """---
# Shellprocess module for managing numlockx
type: job
name: shellprocess@manage_numlockx
command: "/etc/calamares/scripts/manage-numlockx.sh"
configurations:
  - exec: /etc/calamares/scripts/manage-numlockx.sh enable
    timeout: 10
    chroot: true
"""
            with open('/tmp/shellprocess_manage_numlockx.conf', 'w') as f:
                f.write(shellprocess_conf)
            
            subprocess.run(['pkexec', 'mv', '/tmp/shellprocess_manage_numlockx.conf',
                          '/etc/calamares/modules/shellprocess_manage_numlockx.conf'], check=True)

            # 3. Ensure module is in sequence
            self._update_calamares_sequence('shellprocess@manage_numlockx')

        except Exception as e:
            raise Exception(f"Error enabling numlockx: {str(e)}")

    def _update_calamares_sequence(self, module_name):
        """Update Calamares module sequence"""
        try:
            with open('/etc/calamares/settings.conf', 'r') as f:
                settings = f.readlines()

            # Find sequence section and add our module if it doesn't exist
            module_exists = any(module_name in line for line in settings)
            if not module_exists:
                for i, line in enumerate(settings):
                    if '- packages' in line:
                        settings.insert(i, f'  - {module_name}\n')
                        break

                with open('/tmp/settings.conf', 'w') as f:
                    f.writelines(settings)

                subprocess.run(['pkexec', 'mv', '/tmp/settings.conf', 
                              '/etc/calamares/settings.conf'], check=True)

        except Exception as e:
            raise Exception(f"Error updating Calamares sequence: {str(e)}")

    def is_enabled(self):
        """Check if numlockx is enabled in lightdm.conf"""
        try:
            with open('/etc/lightdm/lightdm.conf', 'r') as f:
                for line in f:
                    if 'greeter-setup-script=/usr/bin/numlockx on' in line:
                        # If line is commented, return False
                        return not line.strip().startswith('#')
            return False
        except Exception:
            # If there's any error, assume it's enabled (default behavior)
            return True