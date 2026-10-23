import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import ou_dedetai.constants as constants
import ou_dedetai.wine as wine


@patch.object(constants, 'RUNMODE', 'binary')
@patch.dict(os.environ, {
    'LD_LIBRARY_PATH': '/pyinstaller/bundle',
    'LD_LIBRARY_PATH_ORIG': '/usr/local/lib',
})
class TestGetWineRelease(unittest.TestCase):
    def test_runs_wine_with_original_library_path(self):
        # Wine is often a shell script; PyInstaller's bundled libraries
        # break /bin/sh, so wine must see the user's LD_LIBRARY_PATH.
        with tempfile.TemporaryDirectory() as td:
            fake_wine = Path(td) / 'wine'
            fake_wine.write_text(
                '#!/bin/sh\n'
                '[ "$LD_LIBRARY_PATH" = /usr/local/lib ] || exit 1\n'
                'echo "wine-10.0 (Staging)"\n'
            )
            fake_wine.chmod(0o755)
            release, message = wine.get_wine_release(str(fake_wine))
        self.assertEqual(release, wine.WineRelease(10, 0, 'staging'))
        self.assertEqual(message, 'yes')


if __name__ == '__main__':
    unittest.main()
