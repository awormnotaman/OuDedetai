import subprocess
import threading
import time
import unittest
from unittest.mock import Mock, patch

import ou_dedetai.logos as logos


def _start_thread(task, *args, daemon_bool=True, **kwargs):
    # Like App.start_thread, but daemon so a hung thread can't hang the tests
    thread = threading.Thread(target=task, args=args, kwargs=kwargs, daemon=True)
    thread.start()
    return thread


class TestIndex(unittest.TestCase):
    def setUp(self):
        self.app = Mock()
        self.app.start_thread.side_effect = _start_thread
        self.app.conf.logos_indexer_exe_windows_path = 'C:\\LogosIndexer.exe'
        self.manager = logos.LogosManager(app=self.app)
        for name in ('wineserver_kill', 'wineserver_wait'):
            p = patch.object(logos.wine, name)
            p.start()
            self.addCleanup(p.stop)

    def finished_statuses(self):
        return [c for c in self.app.status.call_args_list if c.args[0] == "Indexing has finished."]

    def test_reports_finished_only_after_indexer_exits(self):
        # wine returns as soon as the indexer is started; the indexer itself runs on
        indexer = subprocess.Popen(['sleep', '2'])
        self.addCleanup(indexer.kill)
        with patch.object(logos.wine, 'run_wine_application', return_value=indexer):
            self.manager.index()
            time.sleep(0.5)
            self.assertEqual(self.manager.indexing_state, logos.State.RUNNING)
            self.assertEqual(self.finished_statuses(), [])

            indexer.wait()
            deadline = time.time() + 5
            while self.manager.indexing_state != logos.State.STOPPED and time.time() < deadline:
                time.sleep(0.1)
        self.assertEqual(self.manager.indexing_state, logos.State.STOPPED)
        self.assertEqual(len(self.finished_statuses()), 1)


    def test_indexer_that_fails_to_start_is_not_reported_finished(self):
        with patch.object(logos.wine, 'run_wine_application', return_value=None):
            self.manager.index()
            deadline = time.time() + 5
            while self.manager.indexing_state != logos.State.STOPPED and time.time() < deadline:
                time.sleep(0.1)
        self.assertEqual(self.manager.indexing_state, logos.State.STOPPED)
        self.assertEqual(self.finished_statuses(), [])


if __name__ == '__main__':
    unittest.main()
