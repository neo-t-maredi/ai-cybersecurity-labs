"""Audit the UCI SMS Spam Collection without modifying it.

File format: one record per line, "<label>\\t<message>". Only the first tab
separates the label from the message; any later tabs belong to the message.
"""

import sys
from collections import Counter, defaultdict
from pathlib import Path

DATASET_PATH = Path(__file__).resolve().parent.parent / "data" / "SMSSpamCollection"
UCI_URL = "https://archive.ics.uci.edu/dataset/228/sms+spam+collection"
VALID_LABELS = ("ham", "spam")

# Total from the UCI dataset page. Class split from the readme bundled with
# the UCI download. A mismatch means the file or the parser has changed.
EXPECTED_COUNTS = {"total": 5574, "ham": 4827, "spam": 747}


class AuditError(Exception):
    """The dataset file breaks the one-record-per-line format."""


def load_records(path: Path) -> list[tuple[str, str]]:
    """Read exactly one (label, message) record per physical line.

    Lines are split on LF only, so a stray CR inside a message stays in the
    message. A CR directly before the LF is treated as a CRLF line ending.
    """
    lines = path.read_bytes().split(b"\n")
    if lines[-1] == b"":
        lines.pop()  # Empty string after the final newline is not a line.

    records = []
    for line_number, raw_line in enumerate(lines, start=1):
        try:
            line = raw_line.removesuffix(b"\r").decode("utf-8")
        except UnicodeDecodeError as error:
            raise AuditError(
                f"Invalid UTF-8 at line {line_number}, byte {error.start}"
            ) from error

        if not line:
            raise AuditError(f"Blank line at line {line_number}")
        if "\t" not in line:
            raise AuditError(f"Missing label separator at line {line_number}")

        label, text = line.split("\t", 1)
        if label not in VALID_LABELS:
            raise AuditError(f"Invalid label {label!r} at line {line_number}")
        if not text:
            raise AuditError(f"Empty message at line {line_number}")

        records.append((label, text))

    if not records:
        raise AuditError("The dataset contains no records")
    return records


def count_physical_lines(path: Path) -> int:
    """Count lines from the raw bytes, independently of load_records."""
    data = path.read_bytes()
    if not data:
        return 0
    return data.count(b"\n") + (0 if data.endswith(b"\n") else 1)


def audit(records: list[tuple[str, str]]) -> dict:
    """Compute dataset statistics. Pure function: no printing, no exits."""
    classes = Counter(label for label, _ in records)
    exact_counts = Counter(records)
    text_counts = Counter(text for _, text in records)

    labels_by_text = defaultdict(set)
    for label, text in records:
        labels_by_text[text].add(label)

    return {
        "total": len(records),
        "ham": classes["ham"],
        "spam": classes["spam"],
        "redundant_exact_rows": sum(n - 1 for n in exact_counts.values()),
        "rows_in_exact_groups": sum(n for n in exact_counts.values() if n > 1),
        "exact_groups": sum(1 for n in exact_counts.values() if n > 1),
        "unique_texts": len(text_counts),
        "redundant_texts": len(records) - len(text_counts),
        "conflicting_texts": sorted(
            text for text, labels in labels_by_text.items() if len(labels) > 1
        ),
    }


def find_failures(results: dict, physical_lines: int) -> list[str]:
    """Compare the audit against independent sources. Empty list means pass."""
    failures = []
    if results["total"] != physical_lines:
        failures.append(
            f"Parsed {results['total']} records but the file has {physical_lines} lines"
        )
    for key, expected in EXPECTED_COUNTS.items():
        if results[key] != expected:
            failures.append(f"{key}: expected {expected}, got {results[key]}")
    if results["conflicting_texts"]:
        shown = results["conflicting_texts"][:5]
        failures.append(
            f"{len(results['conflicting_texts'])} texts have conflicting labels, "
            f"for example: {shown}"
        )
    return failures


def print_report(results: dict) -> None:
    ham_share = 100 * results["ham"] / results["total"]
    print("=== DATASET AUDIT ===")
    print(f"Total records:                  {results['total']}")
    print(f"Ham:                            {results['ham']} ({ham_share:.1f}%)")
    print(f"Spam:                           {results['spam']} ({100 - ham_share:.1f}%)")
    print(f"Redundant exact rows:           {results['redundant_exact_rows']}")
    print(f"Rows in exact duplicate groups: {results['rows_in_exact_groups']}")
    print(f"Exact duplicate groups:         {results['exact_groups']}")
    print(f"Redundant message texts:        {results['redundant_texts']}")
    print(f"Unique message texts:           {results['unique_texts']}")
    print(f"Conflicting text labels:        {len(results['conflicting_texts'])}")


def main() -> int:
    if not DATASET_PATH.exists():
        print(f"Dataset not found at {DATASET_PATH}", file=sys.stderr)
        print(f"Download it from {UCI_URL}", file=sys.stderr)
        return 2

    try:
        records = load_records(DATASET_PATH)
    except AuditError as error:
        print(f"Format error: {error}", file=sys.stderr)
        return 1

    results = audit(records)
    print_report(results)

    failures = find_failures(results, count_physical_lines(DATASET_PATH))
    if failures:
        print("\nAUDIT FAILED", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
