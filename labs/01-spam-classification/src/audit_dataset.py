
from collections import Counter, defaultdict
from pathlib import Path

DATASET_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "SMSSpamCollection"
)

VALID_LABELS = {"ham", "spam"}


def load_records(path: Path):
    """Read exactly one SMS record per physical line."""
    records = []

    with path.open("r", encoding="utf-8", newline="") as source:
        for line_number, line in enumerate(source, start=1):
            line = line.removesuffix("\n").removesuffix("\r")

            if not line:
                raise ValueError(f"Blank line at {line_number}")

            if "\t" not in line:
                raise ValueError(
                    f"Missing label separator at line {line_number}"
                )

            # Only the first tab separates the label from the text.
            label, text = line.split("\t", 1)

            if label not in VALID_LABELS:
                raise ValueError(
                    f"Invalid label {label!r} at line {line_number}"
                )

            if not text:
                raise ValueError(
                    f"Empty message at line {line_number}"
                )

            records.append((label, text))

    if not records:
        raise ValueError("The dataset contains no records")

    return records


def audit(records):
    total = len(records)
    classes = Counter(label for label, _ in records)

    exact_counts = Counter(records)
    text_counts = Counter(text for _, text in records)

    labels_by_text = defaultdict(set)
    for label, text in records:
        labels_by_text[text].add(label)

    redundant_exact = sum(
        count - 1 for count in exact_counts.values()
    )
    duplicate_group_rows = sum(
        count for count in exact_counts.values()
        if count > 1
    )
    duplicate_groups = sum(
        count > 1 for count in exact_counts.values()
    )

    redundant_texts = total - len(text_counts)
    conflicting_texts = sum(
        len(labels) > 1 for labels in labels_by_text.values()
    )

    assert sum(classes.values()) == total
    assert (
        duplicate_group_rows - redundant_exact
        == duplicate_groups
    )
    assert total - redundant_texts == len(text_counts)

    if conflicting_texts:
        raise ValueError(
            f"{conflicting_texts} texts have conflicting labels"
        )

    print("=== DATASET AUDIT ===")
    print(f"Total records: {total}")
    print(f"Ham: {classes['ham']}")
    print(f"Spam: {classes['spam']}")
    print(f"Redundant exact rows: {redundant_exact}")
    print(f"Rows in exact duplicate groups: {duplicate_group_rows}")
    print(f"Exact duplicate groups: {duplicate_groups}")
    print(f"Redundant message texts: {redundant_texts}")
    print(f"Unique message texts: {len(text_counts)}")
    print(f"Conflicting text labels: {conflicting_texts}")
    print("Dataset audit complete.")


def main():
    records = load_records(DATASET_PATH)
    audit(records)


if __name__ == "__main__":
    main()
