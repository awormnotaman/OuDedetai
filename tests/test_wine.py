import unittest
from unittest.mock import Mock

import ou_dedetai.network as network
import ou_dedetai.wine as wine


class TestEnforceIcuDataFiles(unittest.TestCase):
    def test_no_icu_release_exits_with_reason(self):
        class OfflineConfig:
            @property
            def icu_latest_version_url(self):
                raise network.LatestReleaseUnavailable("FaithLife-Community/icu")

            icu_latest_version = icu_latest_version_url

        app = Mock()
        app.conf = OfflineConfig()
        app.exit.side_effect = SystemExit  # like the real App.exit
        with self.assertRaises(SystemExit):
            wine.enforce_icu_data_files(app)
        app.exit.assert_called_once()
        self.assertIn("FaithLife-Community/icu", app.exit.call_args.args[0])


if __name__ == '__main__':
    unittest.main()
