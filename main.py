
import json
import re
from datetime import datetime
from pathlib import Path


# --------------------------------------------------
# FILE STORAGE
# --------------------------------------------------

DATA_DIR = Path(__file__).parent / "data"
DATA_FILE = DATA_DIR / "cases.json"


# --------------------------------------------------
# CONSTANTS
# --------------------------------------------------

CATEGORIES = [
    "Syntax",
    "Runtime",
    "Compilation",
    "Logic",
    "Other",
]

STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were",
    "to", "of", "in", "on", "for", "and", "or",
    "with", "this", "that", "it", "my", "i", "we",
    "you", "how", "why", "what", "error", "fix",
}


# --------------------------------------------------
# LOAD AND SAVE CASES
# --------------------------------------------------

def load_cases():
    """Load saved debugging cases from the JSON file."""
    if not DATA_FILE.exists():
        return []

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            cases = json.load(file)

        if not isinstance(cases, list):
            print("Warning: The saved data must be a JSON list.")
            return []

        return cases

    except (json.JSONDecodeError, OSError) as error:
        print(f"Could not load saved cases: {error}")
        return []


def save_cases(cases):
    """Save debugging cases to a JSON file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(cases, file, indent=4, ensure_ascii=False)


# --------------------------------------------------
# DUPLICATE DETECTION
# --------------------------------------------------

def find_duplicate_case(language, error, cases):
    """Find a case with the same language and error message."""
    normalized_language = " ".join(
        str(language).casefold().split()
    )
    normalized_error = " ".join(
        str(error).casefold().split()
    )

    for case in cases:
        saved_language = " ".join(
            str(case.get("language", "")).casefold().split()
        )
        saved_error = " ".join(
            str(case.get("error", "")).casefold().split()
        )

        if (
            saved_language == normalized_language
            and saved_error == normalized_error
        ):
            return case

    return None


# --------------------------------------------------
# ADD A DEBUGGING CASE
# --------------------------------------------------

def add_case():
    """Collect information and save a debugging case."""
    print("\n=== Save a Debugging Case ===")

    language = input("Programming language: ").strip()
    error = input("Error message: ").strip()

    if not language or not error:
        print("Language and error message cannot be empty.")
        return

    cases = load_cases()

    duplicate = find_duplicate_case(language, error, cases)

    if duplicate is not None:
        print(
            f"\nPossible duplicate: Case "
            f"#{duplicate.get('id', '?')} already has this "
            "language and error message."
        )

        confirmation = input(
            "Save another copy anyway? (y/n): "
        ).strip().lower()

        if confirmation != "y":
            print("Case not saved.")
            return

    attempted_fix = input(
        "What did you try? (Press Enter to skip): "
    ).strip()

    print("\nChoose a category:")

    for number, category in enumerate(CATEGORIES, start=1):
        print(f"{number}. {category}")

    category_choice = input(
        "Category number (1-5, default 5): "
    ).strip()

    if category_choice.isdigit():
        category_number = int(category_choice)

        if 1 <= category_number <= len(CATEGORIES):
            category = CATEGORIES[category_number - 1]
        else:
            category = "Other"
    else:
        category = "Other"

    tags_input = input(
        "Tags separated by commas (optional): "
    ).strip()

    tags = [
        tag.strip()
        for tag in tags_input.split(",")
        if tag.strip()
    ]

    solution = input("Solution: ").strip()
    explanation = input(
        "Explanation (optional): "
    ).strip()

    existing_ids = []

    for case in cases:
        try:
            existing_ids.append(int(case.get("id", 0)))
        except (TypeError, ValueError):
            continue

    next_id = max(existing_ids, default=0) + 1

    new_case = {
        "id": next_id,
        "language": language,
        "error": error,
        "attempted_fix": attempted_fix,
        "solution": solution,
        "explanation": explanation,
        "category": category,
        "tags": tags,
        "timestamp": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
    }

    cases.append(new_case)

    try:
        save_cases(cases)
        print(f"\nCase #{next_id} saved successfully!")
    except OSError as error:
        print(f"Could not save the case: {error}")


# --------------------------------------------------
# DISPLAY CASES
# --------------------------------------------------

def display_case(case):
    """Display the information stored in one case."""
    print(f"\n--- Case #{case.get('id', 'Unknown')} ---")
    print(f"Language: {case.get('language', 'Unknown')}")
    print(f"Category: {case.get('category', 'Other')}")
    print(f"Tags: {', '.join(case.get('tags', []))}")
    print(f"Error: {case.get('error', '')}")
    print(f"Attempted fix: {case.get('attempted_fix', '')}")
    print(f"Solution: {case.get('solution', '')}")
    print(f"Explanation: {case.get('explanation', '')}")
    print(f"Timestamp: {case.get('timestamp', 'Not recorded')}")


def list_cases():
    """Display all saved debugging cases."""
    cases = load_cases()

    if not cases:
        print("\nNo debugging cases saved yet.")
        return

    print(f"\nYou have {len(cases)} saved case(s).")

    for case in cases:
        display_case(case)


# --------------------------------------------------
# WEIGHTED SEARCH
# --------------------------------------------------

def tokenize(text):
    """Convert text into lowercase searchable words."""
    return set(re.findall(r"\b[\w+#.-]+\b", str(text).casefold()))


def score_case(case, query_words):
    """Score a case by how relevant it is to a search query."""
    weights = {
        "error": 5,
        "solution": 3,
        "attempted_fix": 3,
        "category": 2,
        "tags": 2,
        "language": 2,
        "explanation": 1,
    }

    score = 0

    for field, weight in weights.items():
        value = case.get(field, "")

        if isinstance(value, list):
            value = " ".join(str(item) for item in value)

        field_words = tokenize(value)

        score += len(query_words & field_words) * weight

    return score


def search_cases():
    """Search saved cases and show the most relevant matches."""
    cases = load_cases()

    if not cases:
        print("\nNo saved cases to search.")
        return

    query = input("\nEnter error keywords: ").strip()

    if not query:
        print("Please enter at least one search keyword.")
        return

    query_words = tokenize(query) - STOP_WORDS

    if not query_words:
        query_words = tokenize(query)

    matches = []

    for case in cases:
        score = score_case(case, query_words)

        if score > 0:
            matches.append((score, case))

    matches.sort(
        key=lambda item: (
            item[0],
            str(item[1].get("timestamp", "")),
        ),
        reverse=True,
    )

    if not matches:
        print("\nNo matching cases found.")
        return

    print(f"\nFound {len(matches)} matching case(s):")

    for score, case in matches:
        display_case(case)
        print(f"Relevance score: {score}")


# --------------------------------------------------
# FILTER CASES BY LANGUAGE
# --------------------------------------------------

def filter_by_language():
    """Display cases matching a programming language."""
    cases = load_cases()

    if not cases:
        print("\nNo debugging cases saved yet.")
        return

    language = input(
        "\nEnter programming language to filter by: "
    ).strip()

    if not language:
        print("Please enter a programming language.")
        return

    matches = [
        case
        for case in cases
        if str(case.get("language", "")).casefold()
        == language.casefold()
    ]

    if not matches:
        print(f"\nNo cases found for {language}.")
        return

    print(f"\nFound {len(matches)} case(s) for {language}:")

    for case in matches:
        display_case(case)


# --------------------------------------------------
# VIEW ONE CASE BY ID
# --------------------------------------------------

def view_case_by_id():
    """Find and display one case using its ID."""
    cases = load_cases()

    if not cases:
        print("\nNo debugging cases saved yet.")
        return

    case_id_input = input("\nEnter case ID: ").strip()

    try:
        case_id = int(case_id_input)
    except ValueError:
        print("Please enter a valid numeric case ID.")
        return

    for case in cases:
        try:
            saved_id = int(case.get("id", -1))
        except (TypeError, ValueError):
            continue

        if saved_id == case_id:
            display_case(case)
            return

    print(f"\nCase #{case_id} was not found.")


# --------------------------------------------------
# MAIN MENU
# --------------------------------------------------

def main():
    """Run the application menu."""
    while True:
        print("\n=== Error Archaeologist ===")
        print("1. Save a debugging case")
        print("2. View saved cases")
        print("3. Search previous errors")
        print("4. Filter cases by language")
        print("5. View a case by ID")
        print("6. Exit")

        choice = input("Choose an option (1-6): ").strip()

        if choice == "1":
            add_case()
        elif choice == "2":
            list_cases()
        elif choice == "3":
            search_cases()
        elif choice == "4":
            filter_by_language()
        elif choice == "5":
            view_case_by_id()
        elif choice == "6":
            print("Goodbye! Keep learning from your bugs.")
            break
        else:
            print("Invalid choice. Enter a number from 1 to 6.")


if __name__ == "__main__":
    main()