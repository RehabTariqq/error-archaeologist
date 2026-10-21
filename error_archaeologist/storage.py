"""JSON file storage for debugging cases."""

import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

CATEGORIES = ["Syntax", "Runtime", "Compilation", "Logic", "Other"]


def default_data_file():
    """Return the data file path (override with ERROR_ARCHAEOLOGIST_DATA)."""
    override = os.environ.get("ERROR_ARCHAEOLOGIST_DATA")
    if override:
        return Path(override)
    return Path(__file__).resolve().parent.parent / "data" / "cases.json"


def now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


class CaseStore:
    """Reads and writes cases. All persistence goes through this class."""

    def __init__(self, path=None):
        self.path = Path(path) if path else default_data_file()

    # ---------- low level ----------
    def load(self):
        if not self.path.exists():
            return []
        try:
            with self.path.open("r", encoding="utf-8") as file:
                cases = json.load(file)
        except (json.JSONDecodeError, OSError) as error:
            self._backup_corrupt_file(error)
            return []
        if not isinstance(cases, list):
            self._backup_corrupt_file("top-level JSON value is not a list")
            return []
        return [case for case in cases if isinstance(case, dict)]

    def save(self, cases):
        """Write atomically so a crash can never leave a half-written file."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(
            dir=self.path.parent, prefix=".cases-", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as file:
                json.dump(cases, file, indent=4, ensure_ascii=False)
            os.replace(temp_name, self.path)
        except BaseException:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
            raise

    def _backup_corrupt_file(self, reason):
        """Keep a copy of an unreadable file instead of silently overwriting it."""
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = self.path.with_name(f"{self.path.name}.corrupt-{stamp}")
        try:
            shutil.copy2(self.path, backup)
            print(f"Warning: could not read {self.path.name} ({reason}).")
            print(f"A backup was saved as {backup.name}.")
        except OSError:
            print(f"Warning: could not read {self.path.name} ({reason}).")

    # ---------- helpers ----------
    @staticmethod
    def next_id(cases):
        ids = []
        for case in cases:
            try:
                ids.append(int(case.get("id", 0)))
            except (TypeError, ValueError):
                continue
        return max(ids, default=0) + 1

    @staticmethod
    def _same_id(case, case_id):
        try:
            return int(case.get("id", -1)) == int(case_id)
        except (TypeError, ValueError):
            return False

    # ---------- CRUD ----------
    def add(self, language, error, solution="", explanation="",
            attempted_fix="", category="Other", tags=None):
        cases = self.load()
        case = {
            "id": self.next_id(cases),
            "language": language.strip(),
            "error": error.strip(),
            "attempted_fix": attempted_fix.strip(),
            "solution": solution.strip(),
            "explanation": explanation.strip(),
            "category": category if category in CATEGORIES else "Other",
            "tags": list(tags or []),
            "timestamp": now_iso(),
        }
        cases.append(case)
        self.save(cases)
        return case

    def get(self, case_id):
        for case in self.load():
            if self._same_id(case, case_id):
                return case
        return None

    def update(self, case_id, **fields):
        cases = self.load()
        for case in cases:
            if self._same_id(case, case_id):
                case.update(fields)
                case["updated"] = now_iso()
                self.save(cases)
                return case
        return None

    def delete(self, case_id):
        cases = self.load()
        kept = [c for c in cases if not self._same_id(c, case_id)]
        if len(kept) == len(cases):
            return False
        self.save(kept)
        return True

    def find_duplicate(self, language, error, cases=None):
        def norm(value):
            return " ".join(str(value).casefold().split())

        for case in (self.load() if cases is None else cases):
            if (norm(case.get("language", "")) == norm(language)
                    and norm(case.get("error", "")) == norm(error)):
                return case
        return None
