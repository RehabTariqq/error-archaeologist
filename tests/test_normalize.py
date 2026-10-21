import unittest

from error_archaeologist.normalize import (
    error_signature, extract_error_type, last_error_line, tokenize)


class NormalizeTests(unittest.TestCase):
    def test_signature_ignores_variable_names(self):
        a = error_signature("NameError: name 'x' is not defined")
        b = error_signature("NameError: name 'total' is not defined")
        self.assertEqual(a, b)

    def test_signature_ignores_paths_and_line_numbers(self):
        a = error_signature('File "/home/a/app.py", line 12, in main')
        b = error_signature('File "C:\\Users\\b\\other.py", line 99, in main')
        self.assertEqual(a, b)

    def test_extract_error_type(self):
        self.assertEqual(extract_error_type("TypeError: x is not a function"), "typeerror")
        self.assertEqual(extract_error_type("java.lang.NullPointerException: x"),
                         "nullpointerexception")
        self.assertEqual(extract_error_type("segmentation fault"), "")

    def test_tokenize_keeps_cpp_and_csharp(self):
        tokens = tokenize("C++ and C# in node.js")
        self.assertIn("c++", tokens)
        self.assertIn("c#", tokens)
        self.assertIn("node.js", tokens)
        self.assertIn("node", tokens)

    def test_last_error_line_prefers_exception_line(self):
        stderr = ("Traceback (most recent call last):\n"
                  '  File "a.py", line 1, in <module>\n'
                  "ZeroDivisionError: division by zero\n")
        self.assertEqual(last_error_line(stderr),
                         "ZeroDivisionError: division by zero")

    def test_last_error_line_empty(self):
        self.assertEqual(last_error_line(""), "")


if __name__ == "__main__":
    unittest.main()
