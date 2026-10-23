import itertools
import threading
import unittest
from unittest.mock import Mock, patch

import ou_dedetai.logos as logos


class TestMonitorForPotentialIssues(unittest.TestCase):
    def setUp(self):
        self.app = Mock()
        self.app.conf._logos_appdata_dir = '/fake/appdata'
        self.manager = logos.LogosManager(app=self.app)
        self.manager.logos_state = logos.State.RUNNING
        # Don't actually wait between checks
        sleep = patch.object(logos.time, 'sleep')
        sleep.start()
        self.addCleanup(sleep.stop)

    def assert_returns(self):
        # Run in a daemon thread so a regression fails the test instead of hanging it
        thread = threading.Thread(target=self.manager.monitor_for_potential_issues, daemon=True)
        thread.start()
        thread.join(timeout=5)
        self.assertFalse(thread.is_alive(), "monitor_for_potential_issues never returned")

    def test_returns_once_user_is_signed_in(self):
        with patch.object(logos, 'get_logos_user_id', return_value='12345'):
            self.assert_returns()
        self.app.pop_up.assert_not_called()

    def test_shows_sign_in_help_once_then_returns(self):
        # Each call to time.time() is 200s later: past the ~2 minute threshold
        with (
            patch.object(logos, 'get_logos_user_id', return_value=None),
            patch.object(logos.time, 'time', side_effect=itertools.count(0, 200)),
        ):
            self.assert_returns()
        self.app.pop_up.assert_called_once()
        self.assertEqual(self.app.pop_up.call_args.args[0], "Trouble Signing In?")

    def test_returns_once_user_signs_in_while_starting(self):
        # start() sets STARTING; the user can sign in before monitor() sees Logos running
        self.manager.logos_state = logos.State.STARTING
        with patch.object(logos, 'get_logos_user_id', side_effect=[None, None, '12345']):
            self.assert_returns()
        self.app.pop_up.assert_not_called()

    def test_returns_when_logos_stops_before_sign_in(self):
        self.manager.logos_state = logos.State.STOPPED
        with patch.object(logos, 'get_logos_user_id', return_value=None):
            self.assert_returns()

    def test_returns_when_logos_stops_before_appdata_exists(self):
        self.app.conf._logos_appdata_dir = None
        self.manager.logos_state = logos.State.STOPPED
        self.assert_returns()


if __name__ == '__main__':
    unittest.main()
