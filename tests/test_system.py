import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import ou_dedetai.system as system

# Stand-in for pkexec: runs the outer `sh -c "..."`, and only records the
# privileged commands inside it, one JSON argv per line.
FAKE_SUPERUSER = f'''#!{sys.executable}
import json, os, sys
if sys.argv[1] == "sh":
    os.execvp("sh", sys.argv[1:])
with open(os.environ["SUPERUSER_LOG"], "a") as log:
    log.write(json.dumps(sys.argv[1:]) + "\\n")
'''


class TestInstallDependenciesSteamOS(unittest.TestCase):
    def test_runs_steamos_steps_around_install(self):
        with tempfile.TemporaryDirectory() as td:
            fake_bin = Path(td)
            fake_superuser = fake_bin / 'pkexec'
            fake_superuser.write_text(FAKE_SUPERUSER)
            fake_superuser.chmod(0o755)
            fake_pacman = fake_bin / 'pacman'  # `pacman -Q`: nothing installed
            fake_pacman.write_text('#!/bin/sh\n')
            fake_pacman.chmod(0o755)
            log = fake_bin / 'superuser.log'
            log.touch()

            app = Mock()
            app.conf.skip_install_system_dependencies = False
            app.superuser_command = str(fake_superuser)
            only_pacman = {'pacman': '/usr/bin/pacman'}.get
            env = {'PATH': f"{td}:{os.environ['PATH']}", 'SUPERUSER_LOG': str(log)}
            with (
                patch.object(system.distro, 'id', return_value='steamos'),
                patch.object(system.shutil, 'which', side_effect=only_pacman),
                patch.dict(os.environ, env),
            ):
                system.install_dependencies(app)
            commands = [json.loads(line) for line in log.read_text().splitlines()]

        self.assertEqual(commands[:1], [['steamos-readonly', 'disable']])
        self.assertIn(
            ['sed', '-i',
             's/mymachines resolve/mymachines mdns_minimal [NOTFOUND=return] resolve/',
             '/etc/nsswitch.conf'],
            commands,
        )
        # The chain must get all the way to making the system read-only again
        self.assertEqual(commands[-1:], [['steamos-readonly', 'enable']])


if __name__ == '__main__':
    unittest.main()
