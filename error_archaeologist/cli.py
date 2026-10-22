"""Command-line interface and interactive menu."""

import argparse
import subprocess
import sys
from collections import Counter
from pathlib import Path

from . import __version__
from .clipboard import read_clipboard
from .exporter import parse_import, to_json, to_markdown
from .normalize import last_error_line
from .search import search
from .storage import CATEGORIES, CaseStore

LANGUAGE_BY_COMMAND = {
    "python": "Python", "python3": "Python", "py": "Python",
    "node": "JavaScript", "npm": "JavaScript", "deno": "JavaScript",
    "java": "Java", "javac": "Java", "gcc": "C", "g++": "C++",
    "cargo": "Rust", "rustc": "Rust", "go": "Go", "ruby": "Ruby",
    "php": "PHP", "dotnet": "C#",
}


# ---------------------------------------------------------------- display
def display_case(case):
    print(f"\n--- Case #{case.get('id', 'Unknown')} ---")
    print(f"Language: {case.get('language', 'Unknown')}")
    print(f"Category: {case.get('category', 'Other')}")
    print(f"Tags: {', '.join(case.get('tags', []))}")
    print(f"Error: {case.get('error', '')}")
    print(f"Attempted fix: {case.get('attempted_fix', '')}")
    print(f"Solution: {case.get('solution', '')}")
    print(f"Explanation: {case.get('explanation', '')}")
    print(f"Saved: {case.get('timestamp', 'Not recorded')}")
    if case.get("updated"):
        print(f"Updated: {case['updated']}")


def ask(prompt, default=""):
    value = input(prompt).strip()
    return value or default


def parse_tags(text):
    return [tag.strip() for tag in str(text).split(",") if tag.strip()]


def choose_category(current="Other"):
    print("\nChoose a category:")
    for number, name in enumerate(CATEGORIES, start=1):
        print(f"{number}. {name}")
    choice = input(f"Category number (1-{len(CATEGORIES)}, Enter keeps '{current}'): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(CATEGORIES):
        return CATEGORIES[int(choice) - 1]
    return current


# ---------------------------------------------------------------- commands
def cmd_add(store, language=None, error=None, solution=None,
            explanation=None, attempted_fix=None, category=None, tags=None):
    print("\n=== Save a Debugging Case ===")
    language = language or ask("Programming language: ")
    error = error or ask("Error message: ")
    if not language or not error:
        print("Language and error message cannot be empty.")
        return 1

    duplicate = store.find_duplicate(language, error)
    if duplicate is not None:
        print(f"\nPossible duplicate: Case #{duplicate.get('id', '?')} "
              "already has this language and error message.")
        if ask("Save another copy anyway? (y/n): ").lower() != "y":
            print("Case not saved.")
            return 0

    if attempted_fix is None:
        attempted_fix = ask("What did you try? (Enter to skip): ")
    if category is None:
        category = choose_category("Other")
    if tags is None:
        tags = parse_tags(ask("Tags separated by commas (optional): "))
    if solution is None:
        solution = ask("Solution: ")
    if explanation is None:
        explanation = ask("Explanation (optional): ")

    try:
        case = store.add(language, error, solution, explanation,
                         attempted_fix, category, tags)
    except OSError as problem:
        print(f"Could not save the case: {problem}")
        return 1
    print(f"\nCase #{case['id']} saved successfully!")
    return 0


def cmd_list(store, language=None, category=None, tag=None):
    cases = store.load()
    if language:
        cases = [c for c in cases
                 if str(c.get("language", "")).casefold() == language.casefold()]
    if category:
        cases = [c for c in cases
                 if str(c.get("category", "")).casefold() == category.casefold()]
    if tag:
        cases = [c for c in cases
                 if tag.casefold() in [str(t).casefold() for t in c.get("tags", [])]]
    if not cases:
        print("\nNo matching debugging cases.")
        return 0
    print(f"\n{len(cases)} case(s):")
    for case in cases:
        display_case(case)
    return 0


def cmd_search(store, query=None, language=None, limit=5, use_clipboard=False):
    cases = store.load()
    if not cases:
        print("\nNo saved cases to search.")
        return 0
    if use_clipboard:
        text = read_clipboard()
        if not text:
            print("The clipboard is empty or could not be read.")
            return 1
        query = last_error_line(text) if "\n" in text else text
        print(f"\nSearching clipboard: {query}")
    query = query or ask("\nPaste the error or enter keywords: ")
    if not query:
        print("Please enter at least one search keyword.")
        return 1
    results = search(cases, query, language=language, limit=limit,
                     strict=use_clipboard)
    if not results:
        print("\nNo matching cases found.")
        return 0
    print(f"\nTop {len(results)} match(es):")
    for score, case in results:
        display_case(case)
        print(f"Relevance score: {score}")
    return 0


def cmd_show(store, case_id=None):
    if case_id is None:
        raw = ask("\nEnter case ID: ")
        try:
            case_id = int(raw)
        except ValueError:
            print("Please enter a valid numeric case ID.")
            return 1
    case = store.get(case_id)
    if case is None:
        print(f"\nCase #{case_id} was not found.")
        return 1
    display_case(case)
    return 0


def cmd_edit(store, case_id=None):
    if case_id is None:
        raw = ask("\nEnter case ID to edit: ")
        try:
            case_id = int(raw)
        except ValueError:
            print("Please enter a valid numeric case ID.")
            return 1
    case = store.get(case_id)
    if case is None:
        print(f"\nCase #{case_id} was not found.")
        return 1
    print(f"\nEditing Case #{case_id}. Press Enter to keep the current value.")
    changes = {}
    for field, label in [("language", "Language"), ("error", "Error"),
                         ("attempted_fix", "Attempted fix"),
                         ("solution", "Solution"),
                         ("explanation", "Explanation")]:
        new = ask(f"{label} [{case.get(field, '')}]: ")
        if new:
            changes[field] = new
    changes["category"] = choose_category(case.get("category", "Other"))
    tags = ask(f"Tags [{', '.join(case.get('tags', []))}]: ")
    if tags:
        changes["tags"] = parse_tags(tags)
    store.update(case_id, **changes)
    print(f"\nCase #{case_id} updated.")
    return 0


def cmd_delete(store, case_id=None, assume_yes=False):
    if case_id is None:
        raw = ask("\nEnter case ID to delete: ")
        try:
            case_id = int(raw)
        except ValueError:
            print("Please enter a valid numeric case ID.")
            return 1
    case = store.get(case_id)
    if case is None:
        print(f"\nCase #{case_id} was not found.")
        return 1
    if not assume_yes:
        print(f"About to delete Case #{case_id}: {case.get('error', '')}")
        if ask("Are you sure? (y/n): ").lower() != "y":
            print("Cancelled.")
            return 0
    store.delete(case_id)
    print(f"Case #{case_id} deleted.")
    return 0


def cmd_stats(store):
    cases = store.load()
    if not cases:
        print("\nNo debugging cases saved yet.")
        return 0
    print(f"\nTotal cases: {len(cases)}")
    for title, counter in [
        ("By language", Counter(str(c.get("language", "?")) for c in cases)),
        ("By category", Counter(str(c.get("category", "Other")) for c in cases)),
        ("Top tags", Counter(str(t).casefold() for c in cases
                             for t in c.get("tags", []))),
    ]:
        if counter:
            print(f"\n{title}:")
            for name, count in counter.most_common(5):
                print(f"  {name}: {count}")
    return 0


def cmd_export(store, fmt="markdown", output=None):
    cases = store.load()
    text = to_markdown(cases) if fmt == "markdown" else to_json(cases)
    if output:
        Path(output).write_text(text, encoding="utf-8")
        print(f"Exported {len(cases)} case(s) to {output}")
    else:
        print(text)
    return 0


def cmd_import(store, path):
    try:
        incoming = parse_import(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as problem:
        print(f"Could not import: {problem}")
        return 1
    cases = store.load()
    added = skipped = 0
    for item in incoming:
        if store.find_duplicate(item["language"], item["error"], cases):
            skipped += 1
            continue
        item = dict(item)
        item["id"] = store.next_id(cases)
        item.setdefault("tags", [])
        item.setdefault("category", "Other")
        cases.append(item)
        added += 1
    store.save(cases)
    print(f"Imported {added} case(s), skipped {skipped} duplicate(s).")
    return 0


def cmd_run(store, command):
    """Run a command; if it fails, search the archive for its error."""
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        print("Usage: run -- <command> [arguments]")
        return 1
    try:
        process = subprocess.run(command, capture_output=True, text=True)
    except FileNotFoundError:
        print(f"Command not found: {command[0]}")
        return 127
    sys.stdout.write(process.stdout)
    sys.stderr.write(process.stderr)
    if process.returncode == 0:
        print("\nCommand finished without errors.")
        return 0

    error_line = last_error_line(process.stderr)
    print(f"\nCommand failed (exit code {process.returncode}).")
    if not error_line:
        print("No error text was captured.")
        return process.returncode
    print(f"Detected error: {error_line}")

    results = search(store.load(), error_line, limit=3, strict=True)
    if results:
        print("\nYou have seen something like this before:")
        for score, case in results:
            display_case(case)
            print(f"Relevance score: {score}")
        return process.returncode

    print("\nNo similar case saved yet.")
    if ask("Save this error now so you remember the fix? (y/n): ").lower() == "y":
        language = LANGUAGE_BY_COMMAND.get(Path(command[0]).stem.lower(), "")
        language = ask(f"Language [{language}]: ", language)
        solution = ask("Solution (leave empty to add it later with 'edit'): ")
        case = store.add(language or "Unknown", error_line, solution=solution)
        print(f"Saved as Case #{case['id']}.")
    return process.returncode


# ---------------------------------------------------------------- menu
def interactive_menu(store):
    actions = {
        "1": ("Save a debugging case", cmd_add),
        "2": ("View saved cases", cmd_list),
        "3": ("Search previous errors", cmd_search),
        "4": ("Filter cases by language",
              lambda s: cmd_list(s, language=ask("\nLanguage: "))),
        "5": ("View a case by ID", cmd_show),
        "6": ("Edit a case", cmd_edit),
        "7": ("Delete a case", cmd_delete),
        "8": ("Statistics", cmd_stats),
    }
    while True:
        print("\n=== Error Archaeologist ===")
        for key, (label, _) in actions.items():
            print(f"{key}. {label}")
        print("9. Exit")
        choice = input("Choose an option (1-9): ").strip()
        if choice == "9":
            print("Goodbye! Keep learning from your bugs.")
            return 0
        if choice in actions:
            actions[choice][1](store)
        else:
            print("Invalid choice. Enter a number from 1 to 9.")


# ---------------------------------------------------------------- parser
def build_parser():
    parser = argparse.ArgumentParser(
        description="Error Archaeologist: remember how you fixed it.",
    )
    parser.add_argument("--version", action="version",
                        version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("add", help="save a debugging case")
    p.add_argument("--language")
    p.add_argument("--error")
    p.add_argument("--solution")
    p.add_argument("--explanation")
    p.add_argument("--attempted-fix", dest="attempted_fix")
    p.add_argument("--category", choices=CATEGORIES)
    p.add_argument("--tags", help="comma separated")

    p = sub.add_parser("list", help="list saved cases")
    p.add_argument("--language")
    p.add_argument("--category")
    p.add_argument("--tag")

    p = sub.add_parser("search", help="search saved cases")
    p.add_argument("query", nargs="*", help="error text or keywords")
    p.add_argument("--language")
    p.add_argument("--limit", type=int, default=5)
    p.add_argument("--clip", action="store_true",
                   help="search the error currently on the clipboard")

    p = sub.add_parser("show", help="show one case")
    p.add_argument("id", type=int)

    p = sub.add_parser("edit", help="edit a case")
    p.add_argument("id", type=int)

    p = sub.add_parser("delete", help="delete a case")
    p.add_argument("id", type=int)
    p.add_argument("-y", "--yes", action="store_true")

    sub.add_parser("stats", help="show statistics")

    p = sub.add_parser("export", help="export all cases")
    p.add_argument("--format", choices=["markdown", "json"], default="markdown")
    p.add_argument("--output")

    p = sub.add_parser("import", help="import cases from a JSON file")
    p.add_argument("path")

    p = sub.add_parser("run", help="run a command and search its error")
    p.add_argument("cmd", nargs=argparse.REMAINDER)
    return parser


def main(argv=None, store=None):
    store = store or CaseStore()
    args = build_parser().parse_args(argv)

    if args.command is None:
        return interactive_menu(store)
    if args.command == "add":
        tags = parse_tags(args.tags) if args.tags is not None else None
        return cmd_add(store, args.language, args.error, args.solution,
                       args.explanation, args.attempted_fix, args.category, tags)
    if args.command == "list":
        return cmd_list(store, args.language, args.category, args.tag)
    if args.command == "search":
        return cmd_search(store, " ".join(args.query) or None,
                          args.language, args.limit, args.clip)
    if args.command == "show":
        return cmd_show(store, args.id)
    if args.command == "edit":
        return cmd_edit(store, args.id)
    if args.command == "delete":
        return cmd_delete(store, args.id, args.yes)
    if args.command == "stats":
        return cmd_stats(store)
    if args.command == "export":
        return cmd_export(store, args.format, args.output)
    if args.command == "import":
        return cmd_import(store, args.path)
    if args.command == "run":
        return cmd_run(store, args.cmd)
    return 0
