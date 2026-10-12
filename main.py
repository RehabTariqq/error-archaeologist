
import json
import re
from datetime import datetime
from pathlib import Path

# Project storage locations
DATA_DIR = Path(__file__).parent / "data"
DATA_FILE = DATA_DIR / "cases.json"


def load_cases():
    """Load saved debugging cases from the JSON file."""
    if not DATA_FILE.exists():
        return []

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            cases = json.load(file)

        if not isinstance(cases, list):
            print("Warning: Saved data must be a list.")
            return []

        return cases

    except (json.JSONDecodeError, OSError):
        print("Warning: Could not read the saved cases file.")
        return []


def save_cases(cases):
    """Save debugging cases to the JSON file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(cases, file, indent=4, ensure_ascii=False)


def add_case():
    """Collect and save a new debugging case."""
    print("\n--- Save a debugging case ---")

    language = input("Programming language: ").strip()
    error = input("Error message: ").strip()
    attempted_fix = input("What did you try? ").strip()
    solution = input("What solution worked? ").strip()
    explanation = input("Why did it work? ").strip()

    if not language or not error or not solution:
        print("Language, error, and solution are required.")
        return

    cases = load_cases()

    next_id = max(
        (case.get("id", 0) for case in cases),
        default=0
    ) + 1

    case = {
        "id": next_id,
        "created_at": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "language": language,
        "error": error,
        "attempted_fix": attempted_fix,
        "solution": solution,
        "explanation": explanation,
    }

    cases.append(case)
    save_cases(cases)

    print(f"\nCase #{next_id} saved successfully!")


def list_cases():
    """Display all saved debugging cases."""
    cases = load_cases()

    if not cases:
        print("\nNo debugging cases saved yet.")
        return

    print(f"\n--- Saved cases: {len(cases)} ---")

    for case in cases:
        print(f"\nCase #{case['id']} | {case['language']}")
        print(f"Created: {case.get('created_at', 'Unknown')}")
        print(f"Error: {case['error']}")
        print(f"Attempted fix: {case.get('attempted_fix', '')}")
        print(f"Solution: {case['solution']}")
        print(f"Why it worked: {case.get('explanation', '')}")


def search_cases():
    """Search saved cases using keyword matching."""
    query = input("\nEnter the error or keywords to search: ").strip()

    if not query:
        print("Please enter something to search for.")
        return

    query_words = set(re.findall(r"[a-zA-Z0-9_]+", query.lower()))

    stop_words = {
        "the", "a", "an", "is", "in", "on", "to", "of",
        "and", "or", "for", "with", "my", "i", "it"
    }

    query_words -= stop_words

    if not query_words:
        print("Try using more specific error keywords.")
        return

    cases = load_cases()
    matches = []

    for case in cases:
        searchable_text = " ".join([
            case.get("language", ""),
            case.get("error", ""),
            case.get("attempted_fix", ""),
            case.get("solution", ""),
            case.get("explanation", ""),
        ]).lower()

        case_words = set(
            re.findall(r"[a-zA-Z0-9_]+", searchable_text)
        )

        matching_words = query_words & case_words
        score = len(matching_words) / len(query_words)

        if score > 0:
            matches.append((score, case))

    matches.sort(key=lambda item: item[0], reverse=True)

    if not matches:
        print("\nNo matching cases found.")
        print("Try different keywords or save a case first.")
        return

    print(f"\nFound {len(matches)} matching case(s).")

    for score, case in matches:
        print(f"\n--- Case #{case['id']} ---")
        print(f"Match: {score:.0%}")
        print(f"Language: {case['language']}")
        print(f"Previous error: {case['error']}")
        print(f"Attempted fix: {case.get('attempted_fix', '')}")
        print(f"Working solution: {case['solution']}")
        print(f"Why it worked: {case.get('explanation', '')}")


def main():
    """Run the Error Archaeologist menu."""
    while True:
        print("\n=== Error Archaeologist ===")
        print("1. Save a debugging case")
        print("2. View saved cases")
        print("3. Search previous errors")
        print("4. Exit")

        choice = input("Choose an option (1-4): ").strip()

        if choice == "1":
            add_case()
        elif choice == "2":
            list_cases()
        elif choice == "3":
            search_cases()
        elif choice == "4":
            print("Goodbye! Keep learning from your bugs.")
            break
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")


if __name__ == "__main__":
    main()