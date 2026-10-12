
import unittest
from unittest.mock import patch
import tempfile
from pathlib import Path

import main


class ErrorArchaeologistTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_dir = main.DATA_DIR
        self.original_file = main.DATA_FILE

        main.DATA_DIR = Path(self.temp_dir.name)
        main.DATA_FILE = main.DATA_DIR / "cases.json"

    def tearDown(self):
        main.DATA_DIR = self.original_dir
        main.DATA_FILE = self.original_file
        self.temp_dir.cleanup()

    def test_save_and_load_cases(self):
        cases = [{
            "id": 1,
            "language": "Python",
            "error": "NameError: name x is not defined",
            "attempted_fix": "",
            "solution": "Define x before using it",
            "explanation": "The variable must exist before use"
        }]

        main.save_cases(cases)
        loaded = main.load_cases()

        self.assertEqual(loaded, cases)

    def test_missing_file_returns_empty_list(self):
        self.assertEqual(main.load_cases(), [])


if __name__ == "__main__":
    unittest.main()