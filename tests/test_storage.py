import json
import os
import tempfile
import unittest
from pathlib import Path

from unittest.mock import patch

from error_archaeologist import storage
from error_archaeologist.storage import CaseStore


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = CaseStore(Path(self.temp.name) / "cases.json")

    def tearDown(self):
        self.temp.cleanup()

    def test_missing_file_returns_empty_list(self):
        self.assertEqual(self.store.load(), [])

    def test_save_and_load_round_trip(self):
        cases = [{"id": 1, "language": "Python", "error": "NameError"}]
        self.store.save(cases)
        self.assertEqual(self.store.load(), cases)

    def test_saved_data_is_valid_json(self):
        self.store.save([{"id": 1, "language": "Python", "error": "x"}])
        with self.store.path.open(encoding="utf-8") as file:
            self.assertIsInstance(json.load(file), list)

    def test_add_assigns_incrementing_ids(self):
        first = self.store.add("Python", "NameError", "fix")
        second = self.store.add("Python", "TypeError", "fix")
        self.assertEqual((first["id"], second["id"]), (1, 2))

    def test_invalid_category_becomes_other(self):
        case = self.store.add("Python", "x", category="Nonsense")
        self.assertEqual(case["category"], "Other")

    def test_update_changes_fields_and_sets_updated(self):
        case = self.store.add("Python", "x", "old")
        changed = self.store.update(case["id"], solution="new")
        self.assertEqual(changed["solution"], "new")
        self.assertIn("updated", changed)

    def test_update_missing_case_returns_none(self):
        self.assertIsNone(self.store.update(99, solution="x"))

    def test_delete(self):
        case = self.store.add("Python", "x")
        self.assertTrue(self.store.delete(case["id"]))
        self.assertFalse(self.store.delete(case["id"]))
        self.assertEqual(self.store.load(), [])

    def test_ids_are_not_reused_after_delete_of_older_case(self):
        a = self.store.add("Python", "a")
        self.store.add("Python", "b")
        self.store.delete(a["id"])
        self.assertEqual(self.store.add("Python", "c")["id"], 3)

    def test_corrupt_file_is_backed_up_not_lost(self):
        self.store.path.write_text("{not json", encoding="utf-8")
        self.assertEqual(self.store.load(), [])
        backups = list(Path(self.temp.name).glob("cases.json.corrupt-*"))
        self.assertEqual(len(backups), 1)

    def test_duplicate_detection_ignores_case_and_extra_spaces(self):
        cases = [{"id": 1, "language": "Python",
                  "error": "NameError: name x is not defined"}]
        duplicate = self.store.find_duplicate(
            " python ", " NAMEERROR: name x is not defined ", cases)
        self.assertEqual(duplicate["id"], 1)

    def test_different_error_is_not_duplicate(self):
        cases = [{"id": 1, "language": "Python", "error": "NameError"}]
        self.assertIsNone(self.store.find_duplicate("Python", "TypeError", cases))

    def test_same_error_other_language_is_not_duplicate(self):
        cases = [{"id": 1, "language": "Python", "error": "Undefined variable"}]
        self.assertIsNone(
            self.store.find_duplicate("JavaScript", "Undefined variable", cases))


class DataLocationTests(unittest.TestCase):
    def test_env_variable_overrides_location(self):
        with patch.dict(os.environ, {"ERROR_ARCHAEOLOGIST_DATA": "/tmp/x/cases.json"}):
            self.assertEqual(storage.default_data_file(), Path("/tmp/x/cases.json"))

    def test_source_checkout_uses_project_data_folder(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ERROR_ARCHAEOLOGIST_DATA", None)
            path = storage.default_data_file()
        self.assertEqual(path.name, "cases.json")
        self.assertEqual(path.parent.name, "data")

    def test_user_data_dir_ends_with_app_name(self):
        self.assertEqual(storage.user_data_dir().name, "error-archaeologist")


if __name__ == "__main__":
    unittest.main()
