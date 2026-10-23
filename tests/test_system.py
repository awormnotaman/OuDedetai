import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import ou_dedetai.system as system


class TestInstallDependenciesFailure(unittest.TestCase):
    def install_with_superuser_exiting(self, exit_code: int, expect_exit: bool = True) -> Mock:
        with tempfile.TemporaryDirectory() as td:
            fake_superuser = Path(td) / 'pkexec'
            fake_superuser.write_text(f'#!/bin/sh\nexit {exit_code}\n')
            fake_superuser.chmod(0o755)
            fake_pacman = Path(td) / 'pacman'  # `pacman -Q`: nothing installed
            fake_pacman.write_text('#!/bin/sh\n')
            fake_pacman.chmod(0o755)

            app = Mock()
            app.conf.skip_install_system_dependencies = False
            app.superuser_command = str(fake_superuser)
            app.exit.side_effect = SystemExit  # like the real App.exit
            only_pacman = {'pacman': '/usr/bin/pacman'}.get
            with (
                patch.object(system.distro, 'id', return_value='arch'),
                patch.object(system.shutil, 'which', side_effect=only_pacman),
                patch.dict(os.environ, {'PATH': f"{td}:{os.environ['PATH']}"}),
            ):
                if expect_exit:
                    with self.assertRaises(SystemExit):
                        system.install_dependencies(app)
                else:
                    system.install_dependencies(app)
        return app

    def test_successful_install_continues(self):
        app = self.install_with_superuser_exiting(0, expect_exit=False)
        app.exit.assert_not_called()

    def test_failed_install_exits(self):
        app = self.install_with_superuser_exiting(1)
        app.exit.assert_called_once()

    def test_install_command_not_started_exits(self):
        # run_command returns None when starting the command raises (e.g. OSError)
        real_run_command = system.run_command

        def run_command(command, **kwargs):
            if kwargs.get('shell'):  # the privileged install
                return None
            return real_run_command(command, **kwargs)

        with patch.object(system, 'run_command', side_effect=run_command):
            app = self.install_with_superuser_exiting(0)
        app.exit.assert_called_once()

    def test_cancelled_install_exits(self):
        app = self.install_with_superuser_exiting(127)
        app.exit.assert_called_once()


if __name__ == '__main__':
    unittest.main()
