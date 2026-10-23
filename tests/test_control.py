import os
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from zipfile import ZipFile

import ou_dedetai.constants as constants
import ou_dedetai.control as control


class TestGetSupport(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.tmp = Path(self.tempdir.name)
        self.zip_path = self.tmp / 'support.zip'

        self.app = Mock()
        self.app.ask.side_effect = [str(self.zip_path), 'Show links']
        missing = str(self.tmp / 'missing')
        self.app.conf.config_file_path = missing
        self.app.conf.app_log_path = missing
        self.app.conf.app_wine_log_path = missing
        self.app.conf.app_wine_log_previous_path = missing
        self.app.conf._faithlife_crash_log = None
        self.app.conf._raw.wine_binary = None
        self.app.conf._raw._as_dict.return_value = {}
        self.app.conf._network._cache._as_dict.return_value = {}
        self.app.conf._overrides = types.SimpleNamespace()

    def test_commands_run_with_original_library_path(self):
        # Tools like xdg-mime and inxi are scripts; PyInstaller's bundled
        # libraries break their interpreters, so they must see the user's
        # LD_LIBRARY_PATH.
        fake_bin = self.tmp / 'bin'
        fake_bin.mkdir()
        fake_df = fake_bin / 'df'
        fake_df.write_text('#!/bin/sh\nprintf "%s" "$LD_LIBRARY_PATH"\n')
        fake_df.chmod(0o755)
        env = {
            'PATH': str(fake_bin),
            'LD_LIBRARY_PATH': '/pyinstaller/bundle',
            'LD_LIBRARY_PATH_ORIG': '/usr/local/lib',
            'DIALOG': 'cli',
        }
        with patch.object(constants, 'RUNMODE', 'binary'), patch.dict(os.environ, env):
            control.get_support(self.app)

        with ZipFile(self.zip_path) as zip:
            df_output = [n for n in zip.namelist() if n.endswith('df -h')]
            self.assertEqual(len(df_output), 1)
            self.assertEqual(zip.read(df_output[0]).decode(), '/usr/local/lib')


if __name__ == '__main__':
    unittest.main()
