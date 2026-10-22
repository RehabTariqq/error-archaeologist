import subprocess
import unittest
from unittest.mock import patch

from error_archaeologist import clipboard


class ClipboardTests(unittest.TestCase):
    def fake_result(self, text, code=0):
        return subprocess.CompletedProcess(["x"], code, stdout=text, stderr="")

    def test_returns_stripped_text(self):
        with patch.object(clipboard, "_commands", return_value=[["tool"]]), \
             patch("shutil.which", return_value="/bin/tool"), \
             patch("subprocess.run", return_value=self.fake_result("  hello \n")):
            self.assertEqual(clipboard.read_clipboard(), "hello")

    def test_missing_tool_returns_empty(self):
        with patch.object(clipboard, "_commands", return_value=[["tool"]]), \
             patch("shutil.which", return_value=None):
            self.assertEqual(clipboard.read_clipboard(), "")

    def test_failed_command_returns_empty(self):
        with patch.object(clipboard, "_commands", return_value=[["tool"]]), \
             patch("shutil.which", return_value="/bin/tool"), \
             patch("subprocess.run", return_value=self.fake_result("x", code=1)):
            self.assertEqual(clipboard.read_clipboard(), "")

    def test_timeout_is_handled(self):
        with patch.object(clipboard, "_commands", return_value=[["tool"]]), \
             patch("shutil.which", return_value="/bin/tool"), \
             patch("subprocess.run",
                   side_effect=subprocess.TimeoutExpired("tool", 5)):
            self.assertEqual(clipboard.read_clipboard(), "")

    def test_falls_back_to_next_tool(self):
        calls = [self.fake_result("", 1), self.fake_result("second")]
        with patch.object(clipboard, "_commands",
                          return_value=[["a"], ["b"]]), \
             patch("shutil.which", return_value="/bin/x"), \
             patch("subprocess.run", side_effect=calls):
            self.assertEqual(clipboard.read_clipboard(), "second")


if __name__ == "__main__":
    unittest.main()
