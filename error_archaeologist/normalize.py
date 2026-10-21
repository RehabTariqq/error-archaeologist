"""Turn raw error text into comparable forms.

The same bug produces different text on different days: file paths, line
numbers and variable names change. Normalising removes that noise so
"NameError: name 'x' is not defined" matches "NameError: name 'total' is
not defined".
"""

import re

_SIGNATURE_RULES = [
    (re.compile(r"0x[0-9a-fA-F]+"), "<hex>"),
    (re.compile(r"(?:[A-Za-z]:)?(?:[\\/][^\s\\/:'\"]+)+"), "<path>"),
    (re.compile(r"\bline \d+", re.IGNORECASE), "line <n>"),
    (re.compile(r":\d+(?::\d+)?"), ":<n>"),
    (re.compile(r"'[^']*'|\"[^\"]*\"|`[^`]*`"), "<name>"),
    (re.compile(r"\b\d+\b"), "<n>"),
]

_ERROR_TYPE = re.compile(
    r"\b([A-Za-z_][\w.]*?(?:Error|Exception|Warning|Fault|Panic))\b"
)

_TOKEN = re.compile(r"\w+(?:[.#+-]+\w+)*[+#]*")


def error_signature(text):
    """Lowercase text with paths, numbers and quoted names replaced."""
    result = str(text)
    for pattern, replacement in _SIGNATURE_RULES:
        result = pattern.sub(replacement, result)
    return " ".join(result.casefold().split())


def extract_error_type(text):
    """Return e.g. 'TypeError' from 'TypeError: x is not a function'."""
    match = _ERROR_TYPE.search(str(text))
    if not match:
        return ""
    return match.group(1).split(".")[-1].casefold()


def tokenize(text):
    """Return searchable lowercase tokens (also keeps c++, c#, node.js)."""
    tokens = set()
    for raw in _TOKEN.findall(str(text).casefold()):
        tokens.add(raw)
        if re.search(r"[.-]", raw):
            tokens.update(part for part in re.split(r"[.-]+", raw) if part)
    return tokens


def last_error_line(stderr_text):
    """Pick the most useful error line from captured stderr output."""
    lines = [line.strip() for line in str(stderr_text).splitlines() if line.strip()]
    for line in reversed(lines):
        if _ERROR_TYPE.search(line):
            return line
    return lines[-1] if lines else ""
