import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from error_archaeologist import cli
from error_archaeologist.storage import CaseStore


def run(argv, store, inputs=None):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        if inputs is None:
            code = cli.main(argv, store=store)
        else:
            with patch("builtins.input", side_effect=inputs):
                code = cli.main(argv, store=store)
    return code, out.getvalue()


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = CaseStore(Path(self.temp.name) / "cases.json")

    def tearDown(self):
        self.temp.cleanup()

    def add_sample(self):
        return self.store.add("Python", "NameError: name 'x' is not defined",
                              "Define x first", tags=["variables"])

    def test_add_with_flags_needs_no_prompts(self):
        code, out = run(["add", "--language", "Python", "--error", "KeyError",
                         "--solution", "use .get()", "--attempted-fix", "",
                         "--category", "Runtime", "--tags", "dict,keys",
                         "--explanation", ""], self.store, inputs=[])
        self.assertEqual(code, 0)
        self.assertIn("saved successfully", out)
        self.assertEqual(self.store.load()[0]["tags"], ["dict", "keys"])

    def test_add_rejects_empty_error(self):
        code, _ = run(["add"], self.store, inputs=["Python", ""])
        self.assertEqual(code, 1)
        self.assertEqual(self.store.load(), [])

    def test_add_duplicate_can_be_cancelled(self):
        self.add_sample()
        code, out = run(["add"], self.store,
                        inputs=["python", "nameerror: name 'x' is not defined", "n"])
        self.assertIn("Possible duplicate", out)
        self.assertEqual(len(self.store.load()), 1)

    def test_list_filters_by_language(self):
        self.add_sample()
        self.store.add("C++", "undefined reference")
        _, out = run(["list", "--language", "PYTHON"], self.store)
        self.assertIn("Case #1", out)
        self.assertNotIn("Case #2", out)

    def test_search_command(self):
        self.add_sample()
        _, out = run(["search", "NameError", "total", "not", "defined"], self.store)
        self.assertIn("Case #1", out)
        self.assertIn("Relevance score", out)

    def test_search_clip_single_line(self):
        self.add_sample()
        with patch("error_archaeologist.cli.read_clipboard",
                   return_value="NameError: name 'total' is not defined"):
            code, out = run(["search", "--clip"], self.store)
        self.assertEqual(code, 0)
        self.assertIn("Searching clipboard", out)
        self.assertIn("Case #1", out)

    def test_search_clip_uses_last_line_of_traceback(self):
        self.add_sample()
        traceback_text = ("Traceback (most recent call last):\n"
                          '  File "a.py", line 3, in <module>\n'
                          "NameError: name 'y' is not defined")
        with patch("error_archaeologist.cli.read_clipboard",
                   return_value=traceback_text):
            _, out = run(["search", "--clip"], self.store)
        self.assertIn("Searching clipboard: NameError", out)
        self.assertIn("Case #1", out)

    def test_search_clip_empty_clipboard(self):
        self.add_sample()
        with patch("error_archaeologist.cli.read_clipboard", return_value=""):
            code, out = run(["search", "--clip"], self.store)
        self.assertEqual(code, 1)
        self.assertIn("clipboard is empty", out)

    def test_show_missing_case(self):
        code, out = run(["show", "42"], self.store)
        self.assertEqual(code, 1)
        self.assertIn("not found", out)

    def test_delete_requires_confirmation(self):
        self.add_sample()
        run(["delete", "1"], self.store, inputs=["n"])
        self.assertEqual(len(self.store.load()), 1)
        run(["delete", "1"], self.store, inputs=["y"])
        self.assertEqual(self.store.load(), [])

    def test_delete_with_yes_flag(self):
        self.add_sample()
        run(["delete", "1", "--yes"], self.store)
        self.assertEqual(self.store.load(), [])

    def test_edit_keeps_blank_fields(self):
        self.add_sample()
        # language, error, attempted, solution, explanation, category, tags
        run(["edit", "1"], self.store,
            inputs=["", "", "", "Define x before use", "", "", ""])
        case = self.store.get(1)
        self.assertEqual(case["solution"], "Define x before use")
        self.assertEqual(case["language"], "Python")

    def test_stats(self):
        self.add_sample()
        _, out = run(["stats"], self.store)
        self.assertIn("Total cases: 1", out)

    def test_export_markdown_and_import_json_round_trip(self):
        self.add_sample()
        out_file = Path(self.temp.name) / "backup.json"
        run(["export", "--format", "json", "--output", str(out_file)], self.store)
        other = CaseStore(Path(self.temp.name) / "other.json")
        _, out = run(["import", str(out_file)], other)
        self.assertIn("Imported 1", out)
        _, out = run(["import", str(out_file)], other)
        self.assertIn("skipped 1", out)

    def test_import_bad_file(self):
        bad = Path(self.temp.name) / "bad.json"
        bad.write_text("nope", encoding="utf-8")
        code, _ = run(["import", str(bad)], self.store)
        self.assertEqual(code, 1)

    def test_run_failing_command_finds_saved_case(self):
        self.store.add("Python", "ZeroDivisionError: division by zero",
                       "check the divisor")
        code, out = run(["run", "--", sys.executable, "-c", "1/0"], self.store)
        self.assertNotEqual(code, 0)
        self.assertIn("seen something like this", out)
        self.assertIn("check the divisor", out)

    def test_run_successful_command(self):
        code, out = run(["run", "--", sys.executable, "-c", "print('hi')"], self.store)
        self.assertEqual(code, 0)
        self.assertIn("without errors", out)

    def test_run_unknown_command(self):
        code, out = run(["run", "--", "definitely-not-a-command"], self.store)
        self.assertEqual(code, 127)

    def test_menu_exit(self):
        code, out = run([], self.store, inputs=["9"])
        self.assertEqual(code, 0)
        self.assertIn("Goodbye", out)


if __name__ == "__main__":
    unittest.main()
