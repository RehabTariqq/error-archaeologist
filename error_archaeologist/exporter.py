"""Export and import cases."""

import json


def to_markdown(cases):
    lines = ["# Error Archaeologist: Debugging Cases", ""]
    for case in cases:
        lines.append(f"## Case #{case.get('id', '?')}: {case.get('error', '')}")
        lines.append("")
        lines.append(f"- **Language:** {case.get('language', '')}")
        lines.append(f"- **Category:** {case.get('category', 'Other')}")
        tags = ", ".join(case.get("tags", []))
        if tags:
            lines.append(f"- **Tags:** {tags}")
        lines.append(f"- **Saved:** {case.get('timestamp', 'n/a')}")
        lines.append("")
        if case.get("attempted_fix"):
            lines.append(f"**What I tried:** {case['attempted_fix']}")
            lines.append("")
        lines.append(f"**Solution:** {case.get('solution', '')}")
        lines.append("")
        if case.get("explanation"):
            lines.append(f"**Why it works:** {case['explanation']}")
            lines.append("")
    return "\n".join(lines)


def to_json(cases):
    return json.dumps(cases, indent=4, ensure_ascii=False)


def parse_import(text):
    """Return a list of case dicts from JSON text, or raise ValueError."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError(f"Not valid JSON: {error}") from error
    if not isinstance(data, list):
        raise ValueError("Import file must contain a JSON list of cases.")
    return [item for item in data if isinstance(item, dict)
            and item.get("language") and item.get("error")]
