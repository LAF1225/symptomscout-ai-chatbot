from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "phase4"
    / "phase4_seeds.csv"
)


VALID_SLOTS = {
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
}


REQUIRED_COLUMNS = [
    "seed_id",
    "seed_family_id",
    "utterance",
    "intended_slots",
    "ambiguous",
    "negated",
    "uncertain",
    "context_dependent",
    "source_type",
    "notes",
]


def parse_slots(value):

    return [
        slot.strip()
        for slot in str(value).split(";")
        if slot.strip()
    ]


def main():

    if not INPUT_PATH.exists():

        raise FileNotFoundError(
            f"Could not find:\n{INPUT_PATH}"
        )

    df = pd.read_csv(INPUT_PATH).fillna("")

    print(
        f"Seed rows: {len(df):,}"
    )

    missing = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            f"Missing columns: {missing}"
        )

    if df["seed_id"].duplicated().any():

        raise ValueError(
            "Duplicate seed_id values found."
        )

    invalid_slots = []

    for _, row in df.iterrows():

        for slot in parse_slots(
            row["intended_slots"]
        ):

            if slot not in VALID_SLOTS:

                invalid_slots.append(
                    (
                        row["seed_id"],
                        slot
                    )
                )

    if invalid_slots:

        raise ValueError(
            f"Invalid slot labels: "
            f"{invalid_slots[:10]}"
        )

    for column in [
        "ambiguous",
        "negated",
        "uncertain",
        "context_dependent"
    ]:

        numeric = pd.to_numeric(
            df[column],
            errors="coerce"
        )

        invalid = ~numeric.isin(
            [0, 1]
        )

        if invalid.any():

            bad_rows = df.loc[
                invalid,
                "seed_id"
            ].tolist()

            raise ValueError(
                f"{column} must contain "
                f"only 0 or 1. "
                f"Problem rows: {bad_rows}"
            )

    print(
        "✓ Phase 4 seed structure valid."
    )

    print()

    print("Intended slot counts:")

    counts = {
        slot: 0
        for slot in VALID_SLOTS
    }

    for value in df[
        "intended_slots"
    ]:

        for slot in parse_slots(value):

            counts[slot] += 1

    for slot in sorted(counts):

        if counts[slot] > 0:

            print(
                f" - {slot}: "
                f"{counts[slot]}"
            )


if __name__ == "__main__":
    main()
