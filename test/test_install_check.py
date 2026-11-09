"""Tests for the warning about clashing pygame / pgzero installs."""
import io
import unittest
from unittest import mock

from pgzero import _install_check
from pgzero._install_check import clashing_installs, warning_message


def installed(*names):
    return lambda name: name in names


class ClashingInstallsTest(unittest.TestCase):
    def test_nothing_clashes(self):
        self.assertEqual(clashing_installs(installed("pygame-ce", "pgzero-plus")), [])

    def test_pygame_and_pygame_ce(self):
        self.assertEqual(
            clashing_installs(installed("pygame", "pygame-ce", "pgzero-plus")),
            [("pygame", "pygame-ce")],
        )

    def test_pgzero_and_pgzero_plus(self):
        self.assertEqual(
            clashing_installs(installed("pygame-ce", "pgzero", "pgzero-plus")),
            [("pgzero", "pgzero-plus")],
        )

    def test_both_pairs(self):
        self.assertEqual(
            clashing_installs(installed("pygame", "pygame-ce", "pgzero", "pgzero-plus")),
            [("pygame", "pygame-ce"), ("pgzero", "pgzero-plus")],
        )


class WarningMessageTest(unittest.TestCase):
    def test_names_the_clash_and_the_fix(self):
        message = warning_message([("pygame", "pygame-ce")], python="C:/Python313/python.exe")
        self.assertIn("pygame and pygame-ce are both installed", message)
        self.assertIn('"C:/Python313/python.exe" -m pip uninstall -y pgzero pgzero-plus pygame pygame-ce', message)
        self.assertIn('"C:/Python313/python.exe" -m pip install pgzero-plus', message)

    def test_printed_only_when_there_is_a_clash(self):
        for clashes, expected in [([], ""), ([("pygame", "pygame-ce")], "Warning")]:
            with mock.patch.object(_install_check, "clashing_installs", return_value=clashes), \
                    mock.patch("sys.stderr", new_callable=io.StringIO) as err:
                _install_check.warn_about_clashing_installs()
            self.assertIn(expected, err.getvalue())
            if not expected:
                self.assertEqual(err.getvalue(), "")

    def test_a_failing_check_never_stops_the_game(self):
        with mock.patch.object(_install_check, "clashing_installs", side_effect=RuntimeError), \
                mock.patch("sys.stderr", new_callable=io.StringIO) as err:
            _install_check.warn_about_clashing_installs()
        self.assertEqual(err.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
