
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


    def test_error_message_match_scores_higher_than_explanation(self):
        error_match = {
            "id": 1,
            "language": "Python",
            "error": "NameError undefined variable",
            "solution": "",
            "explanation": "",
            "attempted_fix": "",
            "category": "Runtime",
            "tags": []
        }

        explanation_match = {
            "id": 2,
            "language": "Python",
            "error": "Something went wrong",
            "solution": "",
            "explanation": "NameError undefined variable",
            "attempted_fix": "",
            "category": "Other",
            "tags": []
        }

        query_words = {"nameerror"}

        error_score = main.score_case(error_match, query_words)
        explanation_score = main.score_case(
            explanation_match, query_words
        )

        self.assertGreater(error_score, explanation_score)
if __name__ == "__main__":
    unittest.main()