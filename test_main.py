
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main


class ErrorArchaeologistTests(unittest.TestCase):

    def setUp(self):
        """Use temporary storage so tests never modify real saved cases."""
        self.temp_dir = tempfile.TemporaryDirectory()

        self.original_data_dir = main.DATA_DIR
        self.original_data_file = main.DATA_FILE

        main.DATA_DIR = Path(self.temp_dir.name)
        main.DATA_FILE = main.DATA_DIR / "cases.json"

    def tearDown(self):
        """Restore the original storage paths after each test."""
        main.DATA_DIR = self.original_data_dir
        main.DATA_FILE = self.original_data_file

        self.temp_dir.cleanup()

    def test_save_and_load_cases(self):
        """Saved cases should be loaded without changing their contents."""
        cases = [
            {
                "id": 1,
                "language": "Python",
                "error": "NameError: name x is not defined",
                "attempted_fix": "",
                "solution": "Define x before using it",
                "explanation": "The variable must exist before use",
                "category": "Runtime",
                "tags": ["variables"],
            }
        ]

        main.save_cases(cases)
        loaded = main.load_cases()

        self.assertEqual(loaded, cases)

    def test_missing_file_returns_empty_list(self):
        """Loading should return an empty list when no file exists."""
        self.assertEqual(main.load_cases(), [])

    def test_error_match_scores_higher_than_explanation(self):
        """An error-message match should rank above an explanation match."""
        error_case = {
            "error": "NameError undefined variable",
            "solution": "",
            "category": "Runtime",
            "tags": [],
            "attempted_fix": "",
            "explanation": "",
            "language": "Python",
        }

        explanation_case = {
            "error": "Something went wrong",
            "solution": "",
            "category": "Other",
            "tags": [],
            "attempted_fix": "",
            "explanation": "NameError undefined variable",
            "language": "Python",
        }

        query_words = {"nameerror"}

        error_score = main.score_case(error_case, query_words)
        explanation_score = main.score_case(
            explanation_case, query_words
        )

        self.assertGreater(error_score, explanation_score)

    @patch("builtins.input", return_value="pYtHoN")
    @patch("builtins.print")
    def test_language_filter_is_case_insensitive(
        self, mock_print, mock_input
    ):
        """Language filtering should ignore capitalization."""
        main.save_cases([
            {
                "id": 1,
                "language": "Python",
                "error": "NameError",
                "solution": "Define the variable",
            },
            {
                "id": 2,
                "language": "C++",
                "error": "Undefined reference",
                "solution": "Check the linker",
            },
        ])

        main.filter_by_language()

        printed_text = " ".join(
            str(call) for call in mock_print.call_args_list
        )

        self.assertIn("Found 1 case(s)", printed_text)
        self.assertIn("Case #1", printed_text)
        self.assertNotIn("Case #2", printed_text)

    def test_duplicate_detection_ignores_case_and_extra_spaces(self):
        """Duplicate detection should ignore case and extra whitespace."""
        cases = [
            {
                "id": 1,
                "language": "Python",
                "error": "NameError: name x is not defined",
            }
        ]

        duplicate = main.find_duplicate_case(
            " python ",
            "  NAMEERROR:   name x is not defined ",
            cases,
        )

        self.assertIsNotNone(duplicate)
        self.assertEqual(duplicate["id"], 1)

    def test_different_error_is_not_a_duplicate(self):
        """Different error messages should not count as duplicates."""
        cases = [
            {
                "id": 1,
                "language": "Python",
                "error": "NameError",
            }
        ]

        duplicate = main.find_duplicate_case(
            "Python",
            "TypeError",
            cases,
        )

        self.assertIsNone(duplicate)

    def test_same_error_in_different_language_is_not_duplicate(self):
        """The same error in another language should be allowed."""
        cases = [
            {
                "id": 1,
                "language": "Python",
                "error": "Undefined variable",
            }
        ]

        duplicate = main.find_duplicate_case(
            "JavaScript",
            "Undefined variable",
            cases,
        )

        self.assertIsNone(duplicate)


if __name__ == "__main__":
    unittest.main()