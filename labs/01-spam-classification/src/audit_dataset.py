
from pathlib import Path

import pandas as pd
import csv

# Locate the dataset relative to this script.
DATASET_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "SMSSpamCollection"
)

def main():
    """Inspect the original UCI SMS Spam Collection."""

    df = pd.read_csv(
    DATASET_PATH,
    sep="\t",
    header=None,
    names=["label", "text"],
    encoding="utf-8",
    quoting=csv.QUOTE_NONE,
)

    print("=== DATASET AUDIT ===")
    print(f"Total records: {len(df)}")

    print("\nLabel distribution:")
    print(df["label"].value_counts())

    print("\nMissing values:")
    print(df.isna().sum())

    print(f"\nExact duplicate rows: {df.duplicated().sum()}")
    print(
        "Duplicate message texts:",
        df.duplicated(subset=["text"]).sum(),
    )

    invalid = ~df["label"].isin(["ham", "spam"])
    print(f"\nInvalid labels: {invalid.sum()}")
    
    # Inspect duplicates without modifying the dataset.
    duplicate_rows = df[df.duplicated(keep=False)]

    print("\nDuplicate label distribution:")
    print(duplicate_rows["label"].value_counts())

    # Look for identical text assigned conflicting labels.
    conflicting_texts = (
        df.groupby("text")["label"]
        .nunique()
        .gt(1)
        .sum()
    )

    print(
        "\nMessages with conflicting labels:",
        conflicting_texts,
    )

    unique_df = df.drop_duplicates(subset=["text"])

    print(
        "Unique messages after text deduplication:",
        len(unique_df),
    )
    print("\nDataset audit complete.")

if __name__ == "__main__":
    main()