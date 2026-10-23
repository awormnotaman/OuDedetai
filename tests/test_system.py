import os
import unittest
from pathlib import Path
from unittest.mock import patch

import ou_dedetai.constants as constants
import ou_dedetai.system as system

BUNDLE = '/tmp/_MEI123abc'


@patch.object(constants, 'RUNMODE', 'binary')
@patch.object(constants, 'BUNDLE_DIR', Path(BUNDLE))
class TestFixLdLibraryPath(unittest.TestCase):
    def test_restores_users_library_path(self):
        env = {'LD_LIBRARY_PATH': f'{BUNDLE}:/usr/local/lib', 'LD_LIBRARY_PATH_ORIG': '/usr/local/lib'}
        self.assertEqual(system.fix_ld_library_path(env), {'LD_LIBRARY_PATH': '/usr/local/lib'})

    def test_removes_bundle_path_when_user_had_none(self):
        # PyInstaller sets LD_LIBRARY_PATH to just its bundle, without _ORIG
        self.assertEqual(system.fix_ld_library_path({'LD_LIBRARY_PATH': BUNDLE}), {})

    def test_fixing_twice_keeps_users_library_path(self):
        # e.g. get_wine_env() fixes the env, then popen_command() fixes it again
        env = {'LD_LIBRARY_PATH': f'{BUNDLE}:/usr/local/lib', 'LD_LIBRARY_PATH_ORIG': '/usr/local/lib'}
        fixed_twice = system.fix_ld_library_path(system.fix_ld_library_path(env))
        self.assertEqual(fixed_twice, {'LD_LIBRARY_PATH': '/usr/local/lib'})

    def test_removes_bundle_path_without_orig_from_longer_value(self):
        # Never hand our bundled libraries to a child, whatever else is on the path
        env = {'LD_LIBRARY_PATH': f'{BUNDLE}/:/usr/local/lib'}
        self.assertEqual(system.fix_ld_library_path(env), {'LD_LIBRARY_PATH': '/usr/local/lib'})

    def test_does_not_modify_callers_env(self):
        env = {'LD_LIBRARY_PATH': BUNDLE}
        system.fix_ld_library_path(env)
        self.assertEqual(env, {'LD_LIBRARY_PATH': BUNDLE})

    def test_none_uses_process_environment(self):
        with patch.dict(os.environ, {'LD_LIBRARY_PATH': BUNDLE, 'OTHER': 'kept'}, clear=True):
            self.assertEqual(system.fix_ld_library_path(None), {'OTHER': 'kept'})


if __name__ == '__main__':
    unittest.main()
