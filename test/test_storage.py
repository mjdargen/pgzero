import io
import json
import os
import shutil
import tempfile
import types
import unittest
from unittest import mock
from unittest.mock import patch

from pgzero.storage import Storage
from pgzero.rect import ZRect


class StorageStaticMethodsTest(unittest.TestCase):
    def test_dict_with_no_errors(self):
        obj = {'level': 10, 'player_name': 'Daniel'}

        result = list(Storage._get_json_error_keys(obj))
        self.assertEqual(result, [])

    def test_dict_with_errors(self):
        obj = {'level': 10, 'player_name': 'Daniel', 'obj': object()}

        result = list(Storage._get_json_error_keys(obj))
        self.assertEqual(
            result,
            [("storage['obj']", "object")]
        )

    def test_dict_with_nested_dicts_errors(self):
        subobj0 = {'this_key_fails': object()}
        subobj1 = {'a': 10, 'b': {1, 2, 3}, 'c': 30, 'obj': subobj0}
        subobj2 = {'player_name': 'Daniel', 'level': 20, 'states': subobj1}
        obj = {'game': 'my_game', 'state': subobj2}

        result = sorted(Storage._get_json_error_keys(obj))
        self.assertEqual(result, [
            ("storage['state']['states']['b']", 'set'),
            ("storage['state']['states']['obj']['this_key_fails']", 'object'),
        ])

    def test_invalid_list_item(self):
        """We can report the index of an unserialisable list item."""
        obj = {'items': [1, 5, ZRect(0, 0, 10, 10)]}

        result = sorted(Storage._get_json_error_keys(obj))
        self.assertEqual(result, [
            ("storage['items'][2]", 'pgzero.rect.ZRect'),
        ])


class StorageTest(unittest.TestCase):
    @patch('pgzero.storage.os.path.exists')
    def setUp(self, exists_mock):
        exists_mock.return_value = True
        self.storage = Storage('asdf')

    @patch('builtins.open', mock.mock_open(read_data='{"a": "hello"}'))
    def test_get(self):
        self.storage.load()
        self.assertEqual(self.storage['a'], 'hello')


class StorageSaveLoadTest(unittest.TestCase):
    """Saving and loading files, in a temporary folder."""

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        # A save folder that doesn't exist yet, as on a new computer
        self.save_dir = os.path.join(self.root, "pgzero", "saves")
        patcher = patch.object(Storage, "STORAGE_DIR", self.save_dir)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.storages = Storage.storages[:]
        self.addCleanup(setattr, Storage, "storages", self.storages)

    def make(self):
        storage = Storage()
        storage._set_filename_from_path(os.path.join(self.root, "my_game.py"))
        return storage

    def test_save_creates_the_save_folder(self):
        storage = self.make()
        storage["highscore"] = 10
        storage.save()
        self.assertTrue(os.path.isdir(self.save_dir))
        with open(storage.path) as f:
            self.assertEqual(json.load(f), {"highscore": 10})

    def test_save_leaves_no_temporary_file(self):
        storage = self.make()
        storage["highscore"] = 10
        storage.save()
        self.assertEqual(os.listdir(self.save_dir), [os.path.basename(storage.path)])

    def test_values_are_there_next_time(self):
        storage = self.make()
        storage["highscore"] = 10
        storage.save()
        self.assertEqual(self.make()["highscore"], 10)

    def test_empty_storage_that_was_never_loaded_is_not_saved(self):
        self.make().save()
        self.assertFalse(os.path.exists(self.save_dir))

    def test_save_does_not_print(self):
        storage = self.make()
        storage["highscore"] = 10
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            storage.save()
        self.assertEqual(out.getvalue(), "")

    def test_damaged_save_file_is_set_aside(self):
        storage = self.make()
        os.makedirs(self.save_dir)
        with open(storage.path, "w") as f:
            f.write('{"highscore": 1')  # cut off part way through
        with patch("sys.stderr", new_callable=io.StringIO) as err:
            storage = self.make()
        self.assertEqual(dict(storage), {})
        self.assertIn("damaged", err.getvalue())
        self.assertTrue(os.path.exists(storage.path + ".bak"))
        self.assertFalse(os.path.exists(storage.path))

    def test_save_all_saves_every_storage(self):
        storage = self.make()
        storage["lives"] = 3
        Storage.save_all()
        self.assertEqual(self.make()["lives"], 3)


class RunModSavesStorageTest(unittest.TestCase):
    """The runner saves storage when a game ends, however it ends."""

    def run_mod_with(self, run):
        from pgzero import runner
        with patch.object(runner, "PGZeroGame") as game_class,                 patch.object(runner.pygame.display, "quit"),                 patch.object(runner.pygame.display, "init"),                 patch.object(Storage, "save_all") as save_all:
            game_class.return_value.run.side_effect = run
            try:
                runner.run_mod(types.ModuleType("game"))
            except RuntimeError:
                pass
        return save_all

    def test_saves_when_the_game_ends(self):
        self.run_mod_with(None).assert_called_once_with()

    def test_saves_when_the_game_crashes(self):
        def crash():
            raise RuntimeError("oops")

        self.run_mod_with(crash).assert_called_once_with()
