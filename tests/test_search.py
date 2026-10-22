import unittest

from error_archaeologist.search import score_case, search

CASES = [
    {"id": 1, "language": "Python", "error": "NameError: name 'x' is not defined",
     "solution": "Define the variable before using it", "tags": ["variables"],
     "category": "Runtime", "attempted_fix": "", "explanation": "",
     "timestamp": "2026-01-01T00:00:00"},
    {"id": 2, "language": "JavaScript",
     "error": "TypeError: Cannot read properties of undefined (reading 'map')",
     "solution": "Default the array to [] before mapping", "tags": ["arrays"],
     "category": "Runtime", "attempted_fix": "", "explanation": "",
     "timestamp": "2026-01-02T00:00:00"},
    {"id": 3, "language": "C++", "error": "undefined reference to main",
     "solution": "Link the object files", "tags": ["linker"],
     "category": "Compilation", "attempted_fix": "", "explanation": "",
     "timestamp": "2026-01-03T00:00:00"},
]


class SearchTests(unittest.TestCase):
    def test_error_match_scores_higher_than_explanation(self):
        error_case = {"error": "NameError undefined variable", "language": "Python"}
        explanation_case = {"error": "Something went wrong", "language": "Python",
                            "explanation": "NameError undefined variable"}
        words = {"nameerror"}
        self.assertGreater(score_case(error_case, words),
                           score_case(explanation_case, words))

    def test_finds_case_with_different_variable_name(self):
        results = search(CASES, "NameError: name 'total' is not defined")
        self.assertEqual(results[0][1]["id"], 1)

    def test_finds_javascript_case_from_full_message(self):
        results = search(CASES, "TypeError: Cannot read properties of undefined (reading 'filter')")
        self.assertEqual(results[0][1]["id"], 2)

    def test_typo_tolerance(self):
        results = search(CASES, "linkr objct files")
        self.assertTrue(results)

    def test_language_filter(self):
        results = search(CASES, "undefined", language="c++")
        self.assertEqual([c["id"] for _, c in results], [3])

    def test_no_match_returns_empty(self):
        self.assertEqual(search(CASES, "kubernetes ingress"), [])

    def test_empty_query_returns_empty(self):
        self.assertEqual(search(CASES, "   "), [])

    def test_limit(self):
        self.assertEqual(len(search(CASES, "undefined", limit=1)), 1)

    def test_strict_drops_unrelated_errors(self):
        results = search(
            CASES, "python: can't open file 'x.py': No such file or directory",
            strict=True)
        self.assertEqual(results, [])

    def test_strict_keeps_related_error(self):
        results = search(CASES, "NameError: name 'z' is not defined", strict=True)
        self.assertEqual(results[0][1]["id"], 1)

    def test_non_strict_is_still_forgiving(self):
        self.assertTrue(search(CASES, "linkr objct files"))


if __name__ == "__main__":
    unittest.main()
