import shutil
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class NodePackageContext:
    def __init__(self):
        self.package_json = Path(settings.NODE_MODULES_ROOT).parent.joinpath(
            'package.json'
        )

    def __enter__(self):
        if not self.package_json.exists():
            self.package_json.symlink_to(settings.NODE_PACKAGE_JSON)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.package_json.is_symlink():
            self.package_json.unlink()
        return False


class Command(BaseCommand):
    help = 'Installs all dependencies listed in the package.json'

    def handle(self, **options):
        if not hasattr(settings, 'NODE_PACKAGE_JSON'):
            self.stderr.write('The "NODE_PACKAGE_JSON" setting is not specified.')
            return

        if not Path(settings.NODE_PACKAGE_JSON).exists():
            self.stderr.write(f'The "{settings.NODE_PACKAGE_JSON}" file not found.')
            return

        node_modules_root = Path(settings.NODE_MODULES_ROOT)

        if not node_modules_root.is_dir():
            node_modules_root.mkdir(parents=True)

        try:
            npm_executable = shutil.which('npm')
        except AttributeError:  # fallback for Python < 3.3
            npm_executable = '/usr/bin/npm'

        with NodePackageContext():
            try:
                output = subprocess.check_output(
                    args=[
                        getattr(
                            settings, 'NODE_PACKAGE_MANAGER_EXECUTABLE', npm_executable
                        ),
                        'install',
                        '--no-package-lock',
                    ],
                    cwd=node_modules_root.parent,
                    encoding='utf-8',
                )
            except subprocess.CalledProcessError:
                self.stderr.write('An error occurred.')
            else:
                self.stdout.write(output)
                self.stdout.write(
                    self.style.SUCCESS(
                        'All dependencies have been successfully installed.'
                    )
                )
