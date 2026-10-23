import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import ou_dedetai.constants as constants
import ou_dedetai.installer as installer


@patch.object(installer, 'ensure_config_file', Mock())
@patch.object(constants, 'RUNMODE', 'binary')
class TestEnsureLauncherExecutable(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.install_dir = Path(self.tempdir.name) / 'install'
        self.install_dir.mkdir()
        self.launcher = self.install_dir / constants.BINARY_NAME

        self.app = Mock()
        self.app.conf = Mock()
        self.app.conf.install_dir = str(self.install_dir)
        self.app.installer_step_count = 0
        self.app.installer_step = 0

    def test_running_from_launcher_keeps_launcher(self):
        # The control panel shortcut runs the launcher in install_dir, so
        # updating from there runs the copy with itself as the source (#447)
        self.launcher.write_bytes(b'installed binary')
        with patch.object(sys, 'executable', str(self.launcher)):
            installer.ensure_launcher_executable(self.app)
        self.assertEqual(self.launcher.read_bytes(), b'installed binary')

    def test_running_from_symlink_to_launcher_keeps_launcher(self):
        # e.g. ~/bin/oudedetai -> install_dir/oudedetai (#446)
        self.launcher.write_bytes(b'installed binary')
        link = Path(self.tempdir.name) / 'bin' / constants.BINARY_NAME
        link.parent.mkdir()
        link.symlink_to(self.launcher)
        with patch.object(sys, 'executable', str(link)):
            installer.ensure_launcher_executable(self.app)
        self.assertEqual(self.launcher.read_bytes(), b'installed binary')

    def test_launcher_symlink_to_running_binary_becomes_copy(self):
        # The launcher must not depend on wherever this binary was run from
        downloaded = Path(self.tempdir.name) / constants.BINARY_NAME
        downloaded.write_bytes(b'new binary')
        self.launcher.symlink_to(downloaded)
        with patch.object(sys, 'executable', str(downloaded)):
            installer.ensure_launcher_executable(self.app)
        self.assertFalse(self.launcher.is_symlink())
        self.assertEqual(self.launcher.read_bytes(), b'new binary')

    def test_first_install_creates_launcher(self):
        downloaded = Path(self.tempdir.name) / constants.BINARY_NAME
        downloaded.write_bytes(b'new binary')
        with patch.object(sys, 'executable', str(downloaded)):
            installer.ensure_launcher_executable(self.app)
        self.assertEqual(self.launcher.read_bytes(), b'new binary')

    def test_running_from_other_binary_replaces_launcher(self):
        self.launcher.write_bytes(b'old binary')
        downloaded = Path(self.tempdir.name) / constants.BINARY_NAME
        downloaded.write_bytes(b'new binary')
        with patch.object(sys, 'executable', str(downloaded)):
            installer.ensure_launcher_executable(self.app)
        self.assertEqual(self.launcher.read_bytes(), b'new binary')


if __name__ == '__main__':
    unittest.main()
