import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ou_dedetai.config import PersistentConfiguration


class TestWriteConfig(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.config_dir = Path(self.tempdir.name) / 'FaithLife-Community'
        self.config_dir.mkdir()
        self.config_file = self.config_dir / 'oudedetai.json'
        env = patch.dict(os.environ, {'CONFIG_FILE': str(self.config_file)})
        env.start()
        self.addCleanup(env.stop)

    def test_writes_config(self):
        PersistentConfiguration(faithlife_product='Logos').write_config()
        self.assertEqual(json.loads(self.config_file.read_text())['faithlife_product'], 'Logos')
        # No temporary files left behind
        self.assertEqual([p.name for p in self.config_dir.iterdir()], ['oudedetai.json'])

    def test_failed_write_keeps_existing_config(self):
        self.config_file.write_text('{"faithlife_product": "Logos"}\n')
        unserializable = PersistentConfiguration(faithlife_product='Logos', backup_dir=object())  # type: ignore
        with self.assertRaises(TypeError):
            unserializable.write_config()
        self.assertEqual(self.config_file.read_text(), '{"faithlife_product": "Logos"}\n')

    def test_keeps_existing_permissions(self):
        self.config_file.write_text('{}')
        self.config_file.chmod(0o644)
        PersistentConfiguration(faithlife_product='Logos').write_config()
        self.assertEqual(self.config_file.stat().st_mode & 0o777, 0o644)

    def test_interrupted_write_leaves_no_temp_file(self):
        self.config_file.write_text('{}')
        with patch.object(os, 'fsync', side_effect=KeyboardInterrupt), self.assertRaises(KeyboardInterrupt):
            PersistentConfiguration(faithlife_product='Logos').write_config()
        self.assertEqual([p.name for p in self.config_dir.iterdir()], ['oudedetai.json'])
        self.assertEqual(self.config_file.read_text(), '{}')

    def test_symlinked_config_stays_a_symlink(self):
        # e.g. dotfiles managed with stow
        dotfiles = Path(self.tempdir.name) / 'dotfiles' / 'oudedetai.json'
        dotfiles.parent.mkdir()
        dotfiles.write_text('{}')
        self.config_file.symlink_to(dotfiles)
        PersistentConfiguration(faithlife_product='Verbum').write_config()
        self.assertTrue(self.config_file.is_symlink())
        self.assertEqual(json.loads(dotfiles.read_text())['faithlife_product'], 'Verbum')


if __name__ == '__main__':
    unittest.main()
