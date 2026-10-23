import os
import subprocess
import sys
import unittest

from . import REPODIR


class TestCLIStatus(unittest.TestCase):
    def test_progress_bar_when_output_is_not_a_terminal(self):
        # e.g. `oudedetai --install-app -y > install.log`
        code = (
            "from ou_dedetai.cli import CLI\n"
            "CLI.__new__(CLI)._status('Downloading', 50)\n"
        )
        env = dict(os.environ, PYTHONPATH=str(REPODIR))
        env.pop('COLUMNS', None)
        result = subprocess.run(
            [sys.executable, '-c', code],
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        # Falls back to 80 columns: 77 chars inside the brackets, half of them done
        self.assertIn('[' + '-' * 38 + '>' + ' ' * 39 + ']', result.stdout)


if __name__ == '__main__':
    unittest.main()
