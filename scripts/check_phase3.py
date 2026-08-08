from pathlib import Path
import json

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
)

SLOTS_PATH = (
    PROJECT_ROOT
    / "frameworks"
    / "slots.json"
)


def load_valid_slots():

    with SLOTS_PATH.open(
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    return set(
        data["slots"].keys()
    )


def check_file(filename, required_columns):

    path = PROCESSED_DIR / filename

    if not path.exists():

        raise FileNotFoundError(
            f"Missing Phase Three file: {filename}"
        )

    df = pd.read_csv(path).fillna("")

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            f"{filename} missing columns: {missing}"
        )

    print(
        f"✓ {filename}: "
        f"{len(df):,} rows"
    )

    return df


def main():

    valid_slots = load_valid_slots()

    labeled = check_file(
        "mts_labeled_examples.csv",
        [
            "annotation_id",
            "utterance",
            "final_slots",
            "review_status"
        ]
    )

    phrases = check_file(
        "dialogflow_phrase_candidates.csv",
        [
            "utterance",
            "final_slots"
        ]
    )

    check_file(
        "contextual_examples.csv",
        [
            "doctor_prompt",
            "utterance",
            "final_slots"
        ]
    )

    entities = check_file(
        "entity_terms.csv",
        [
            "term",
            "entity_type",
            "canonical_value",
            "decision"
        ]
    )

    invalid_slots = []

    for _, row in labeled.iterrows():

        slots = [
            value.strip()
            for value in str(
                row["final_slots"]
            ).split(";")
            if value.strip()
        ]

        for slot in slots:

            if slot not in valid_slots:
                invalid_slots.append(slot)

    if invalid_slots:

        raise ValueError(
            "Invalid slot labels found: "
            f"{sorted(set(invalid_slots))}"
        )

    print()

    print("Examples by final slot:")

    counts = {}

    for value in labeled[
        "final_slots"
    ].astype(str):

        for slot in value.split(";"):

            slot = slot.strip()

            if not slot:
                continue

            counts[slot] = (
                counts.get(slot, 0) + 1
            )

    for slot in sorted(counts):

        print(
            f" - {slot}: "
            f"{counts[slot]}"
        )

    print()

    duplicates = (
        phrases["utterance"]
        .astype(str)
        .str.lower()
        .duplicated()
        .sum()
    )

    print(
        f"Exact duplicate self-contained phrases: "
        f"{duplicates}"
    )

    print()

    print(
        "✓ Phase Three dataset validation passed."
    )


if __name__ == "__main__":
    main()