"""The filename case check works the same on Windows, macOS and Linux."""
import os
import shutil
import tempfile
import unittest
from pathlib import Path

import pygame

from pgzero import loaders

test_dir = Path(__file__).parent


class RealRelpathTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        os.makedirs(os.path.join(self.tmp, "Images", "Enemies"))
        open(os.path.join(self.tmp, "Images", "Enemies", "Bat.PNG"), "w").close()
        open(os.path.join(self.tmp, "Images", "alien.png"), "w").close()

    def real(self, *parts):
        return loaders.real_relpath(os.path.join(*parts), start=self.tmp)

    def test_correct_name_is_unchanged(self):
        self.assertEqual(self.real("Images", "alien.png"), os.path.join("Images", "alien.png"))

    def test_finds_the_real_capitalisation(self):
        self.assertEqual(
            self.real("images", "enemies", "bat.png"),
            os.path.join("Images", "Enemies", "Bat.PNG"),
        )

    def test_missing_file_is_left_alone(self):
        self.assertEqual(self.real("images", "cow.png"), os.path.join("Images", "cow.png"))


class LoaderCaseTest(unittest.TestCase):
    """A game folder whose own path has capitals (e.g. 'OneDrive - NCSSM', or
    a Windows short name like MICHAE~1) is fine; only the names inside it are
    checked."""

    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((10, 10))

    def setUp(self):
        self.addCleanup(setattr, loaders, "root", loaders.root)
        self.game = os.path.join(tempfile.mkdtemp(), "My Game")
        self.addCleanup(shutil.rmtree, os.path.dirname(self.game))
        os.makedirs(os.path.join(self.game, "images"))
        loaders.set_root(os.path.join(self.game, "game.py"))

    def copy_alien(self, name):
        shutil.copy(str(test_dir / "images" / "alien.png"), os.path.join(self.game, "images", name))

    def test_lowercase_file_loads(self):
        self.copy_alien("alien.png")
        self.assertIsNotNone(loaders.ImageLoader("images").load("alien"))

    def test_capitalised_file_is_caught(self):
        """Windows and macOS would find Alien.PNG; Linux wouldn't. Either way
        the student finds out now, not when the game runs on Codio."""
        self.copy_alien("Alien.PNG")
        with self.assertRaises((loaders.InvalidCase, KeyError)):
            loaders.ImageLoader("images").load("alien")

    def test_capitalised_folder_is_caught(self):
        os.rename(os.path.join(self.game, "images"), os.path.join(self.game, "Images"))
        with self.assertRaises((loaders.InvalidCase, KeyError)):
            loaders.ImageLoader("images").load("alien")


if __name__ == "__main__":
    unittest.main()
