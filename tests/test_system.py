import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import ou_dedetai.system as system

# Stand-in for `rpm -qa --qf FORMAT`: like rpm, it expands %{NAME} and
# backslash escapes in FORMAT once per installed package, with no separator.
FAKE_RPM = r'''#!/bin/sh
for name in fuse fuse-libs cabextract; do
    fmt=$(printf '%s' "$3" | sed "s/%{NAME}/$name/g")
    printf "$fmt"
done
'''


class TestQueryPackagesFedora(unittest.TestCase):
    def test_installed_packages_are_found(self):
        with tempfile.TemporaryDirectory() as td:
            fake_rpm = Path(td) / 'rpm'
            fake_rpm.write_text(FAKE_RPM)
            fake_rpm.chmod(0o755)
            only_dnf = {'dnf': '/usr/bin/dnf'}.get
            with (
                patch.object(system.shutil, 'which', side_effect=only_dnf),
                patch.dict(os.environ, {'PATH': f"{td}:{os.environ['PATH']}"}),
            ):
                package_manager = system.get_package_manager()
                assert package_manager is not None
                missing = system.query_packages(
                    package_manager,
                    ['fuse', 'cabextract', 'glx-utils'],
                )
        self.assertEqual(missing, ['glx-utils'])


if __name__ == '__main__':
    unittest.main()
