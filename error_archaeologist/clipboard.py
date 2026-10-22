"""Read text from the system clipboard using built-in OS tools."""

import shutil
import subprocess
import sys


def _commands():
    if sys.platform.startswith("win"):
        script = ("[Console]::OutputEncoding=[Text.Encoding]::UTF8;"
                  "Get-Clipboard -Raw")
        return [["powershell", "-NoProfile", "-Command", script]]
    if sys.platform == "darwin":
        return [["pbpaste"]]
    return [
        ["wl-paste", "--no-newline"],
        ["xclip", "-selection", "clipboard", "-o"],
        ["xsel", "--clipboard", "--output"],
    ]


def read_clipboard():
    """Return clipboard text, or an empty string if it is unavailable."""
    for command in _commands():
        if shutil.which(command[0]) is None:
            continue
        try:
            result = subprocess.run(
                command, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=5,
            )
        except (OSError, subprocess.SubprocessError):
            continue
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    return ""
