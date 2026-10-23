import unittest
from unittest.mock import Mock

from ou_dedetai.app import App


class _ScriptedApp(App):
    """Minimal concrete App whose user types the given answers, in order."""

    def __init__(self, answers):
        self._answers = iter(answers)
        self.conf = Mock()
        self.conf._overrides.assume_yes = False

    def _ask(self, question, options):
        return next(self._answers)

    def _info(self, message):
        raise NotImplementedError

    def _status(self, message, percent=None):
        raise NotImplementedError

    def _pop_up(self, title: str, message: str):
        raise NotImplementedError


class TestAsk(unittest.TestCase):
    def test_answer_matching_case(self):
        self.assertTrue(_ScriptedApp(["Yes"]).approve("Continue?"))

    def test_answer_in_lowercase(self):
        self.assertTrue(_ScriptedApp(["yes"]).approve("Continue?"))
        self.assertFalse(_ScriptedApp(["no"]).approve("Continue?"))

    def test_answer_in_other_case_returns_option_casing(self):
        app = _ScriptedApp(["LOGOS"])
        self.assertEqual(app.ask("Which product?", ["Logos", "Verbum"]), "Logos")


if __name__ == '__main__':
    unittest.main()
