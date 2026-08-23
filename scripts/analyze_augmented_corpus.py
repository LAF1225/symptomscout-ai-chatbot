from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "augmented_corpus_v1.csv"
)


VALID_SLOTS = [
    "main_symptom",
    "site",
    "onset",
    "character",
    "radiation",
    "associated",
    "timing",
    "exacerbating",
    "relieving",
    "severity",
]


def parse_slots(value):
    if pd.isna(value):
        return []

    return [
        slot.strip()
        for slot in str(value).split(";")
        if slot.strip()
    ]


def print_section(title):
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def main():

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Could not find final corpus:\n{INPUT_PATH}"
        )

    df = pd.read_csv(INPUT_PATH).fillna("")

    print_section("FINAL CORPUS SUMMARY")

    print(f"File: {INPUT_PATH}")
    print(f"Total rows: {len(df):,}")

    duplicate_ids = df["annotation_id"].duplicated().sum()

    print(f"Duplicate annotation IDs: {duplicate_ids}")

    if duplicate_ids:
        raise ValueError(
            "Duplicate annotation IDs were found."
        )

    # -----------------------------------------------------
    # Review status
    # -----------------------------------------------------

    print_section("REVIEW STATUS")

    if "review_status" in df.columns:
        print(
            df["review_status"]
            .value_counts()
            .to_string()
        )
    else:
        print("Missing column: review_status")

    # -----------------------------------------------------
    # Keep-only dataset
    # -----------------------------------------------------

    keep_df = df[
        df["review_status"]
        .astype(str)
        .str.lower()
        .eq("keep")
    ].copy()

    print()
    print(
        f"Rows eligible for later training: "
        f"{len(keep_df):,}"
    )

    # -----------------------------------------------------
    # Slot counts
    # -----------------------------------------------------

    print_section("SLOT COUNTS — KEEP ROWS ONLY")

    slot_counts = {
        slot: 0
        for slot in VALID_SLOTS
    }

    unknown_slots = set()

    for value in keep_df["final_slots"]:

        for slot in parse_slots(value):

            if slot in slot_counts:
                slot_counts[slot] += 1
            else:
                unknown_slots.add(slot)

    for slot in VALID_SLOTS:
        print(
            f"{slot:15} "
            f"{slot_counts[slot]:>5}"
        )

    if unknown_slots:
        print()
        print(
            "WARNING: Unknown slot labels found:"
        )

        for slot in sorted(unknown_slots):
            print(f" - {slot}")

    # -----------------------------------------------------
    # Special flags
    # -----------------------------------------------------

    print_section("SPECIAL FLAGS — KEEP ROWS ONLY")

    flag_columns = [
        "ambiguous",
        "negated",
        "uncertain",
        "context_dependent",
    ]

    for column in flag_columns:

        if column not in keep_df.columns:
            print(
                f"{column:20} MISSING"
            )
            continue

        numeric = pd.to_numeric(
            keep_df[column],
            errors="coerce"
        )

        invalid_count = numeric.isna().sum()

        true_count = numeric.eq(1).sum()

        print(
            f"{column:20} "
            f"{true_count:>5}"
        )

        if invalid_count:
            print(
                f"  WARNING: "
                f"{invalid_count} invalid/"
                f"blank values"
            )

    # -----------------------------------------------------
    # Annotation source
    # -----------------------------------------------------

    print_section("ANNOTATION SOURCE")

    if "annotation_source" in df.columns:

        print(
            df["annotation_source"]
            .value_counts()
            .to_string()
        )

    else:
        print(
            "Missing column: annotation_source"
        )

    # -----------------------------------------------------
    # Protocol version
    # -----------------------------------------------------

    print_section("PROTOCOL VERSION")

    if "protocol_version" in df.columns:

        print(
            df["protocol_version"]
            .astype(str)
            .value_counts()
            .to_string()
        )

    else:
        print(
            "Missing column: protocol_version"
        )

    # -----------------------------------------------------
    # Context-independent vs dependent
    # -----------------------------------------------------

    print_section(
        "TRAINING-PHRASE READINESS"
    )

    if "context_dependent" in keep_df.columns:

        context_values = pd.to_numeric(
            keep_df["context_dependent"],
            errors="coerce"
        )

        independent = (
            context_values.eq(0).sum()
        )

        dependent = (
            context_values.eq(1).sum()
        )

        print(
            f"Self-contained keep rows: "
            f"{independent:,}"
        )

        print(
            f"Context-dependent keep rows: "
            f"{dependent:,}"
        )

    # -----------------------------------------------------
    # Multi-slot examples
    # -----------------------------------------------------

    print_section("MULTI-SLOT EXAMPLES")

    keep_df["slot_count"] = (
        keep_df["final_slots"]
        .apply(
            lambda value:
            len(parse_slots(value))
        )
    )

    print(
        keep_df["slot_count"]
        .value_counts()
        .sort_index()
        .rename_axis("slots_per_row")
        .to_string()
    )

    multi_slot_count = (
        keep_df["slot_count"] > 1
    ).sum()

    print()
    print(
        f"Rows containing multiple slots: "
        f"{multi_slot_count:,}"
    )

    # -----------------------------------------------------
    # Potentially underrepresented slots
    # -----------------------------------------------------

    print_section(
        "POTENTIALLY UNDERREPRESENTED SLOTS"
    )

    LOW_COUNT_THRESHOLD = 20

    low_slots = [
        slot
        for slot, count in slot_counts.items()
        if count < LOW_COUNT_THRESHOLD
    ]

    if low_slots:

        print(
            "These slots currently have fewer than "
            f"{LOW_COUNT_THRESHOLD} keep examples:"
        )

        for slot in low_slots:
            print(
                f" - {slot}: "
                f"{slot_counts[slot]}"
            )

        print()
        print(
            "These are good candidates for "
            "targeted Phase 4 gap-filling."
        )

    else:
        print(
            "No slot falls below the current "
            f"{LOW_COUNT_THRESHOLD}-example "
            "screening threshold."
        )

    # -----------------------------------------------------
    # Final validation
    # -----------------------------------------------------

    print_section("FINAL VALIDATION")

    expected_columns = [
        "annotation_id",
        "utterance",
        "review_status",
        "final_slots",
        "ambiguous",
        "negated",
        "uncertain",
        "context_dependent",
        "annotation_source",
        "protocol_version",
    ]

    missing_columns = [
        column
        for column in expected_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Final corpus is missing columns: "
            f"{missing_columns}"
        )

    if unknown_slots:
        raise ValueError(
            "Unknown slot labels are present."
        )

    print(
        "✓ Final corpus structure validated."
    )

    print(
        "✓ Slot distribution calculated."
    )

    print(
        "✓ Special flags summarized."
    )

    print(
        "✓ Phase 3 corpus analysis complete."
    )


if __name__ == "__main__":
    main()
