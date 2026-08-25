from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PHASE5_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "phase5"
)

TEST_PATH = (
    PHASE5_DIR
    / "test.csv"
)


SLOTS = [
    "main_symptom",
    "site",
    "onset",
    "character",
    "radiation",
    "associated",
    "timing",
    "exacerbating",
    "relieving",
    "severity"
]


def parse_slots(value):

    if pd.isna(value):
        return []

    return [
        slot.strip()
        for slot in str(value).split(";")
        if slot.strip()
    ]


def main():

    test = pd.read_csv(
        TEST_PATH
    ).fillna("")

    slot_dir = (
        PHASE5_DIR
        / "slots"
    )

    slot_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    print("Slot-specific test examples:")
    print()

    for slot in SLOTS:

        subset = test[
            test["final_slots"]
            .apply(
                lambda value:
                slot in parse_slots(value)
            )
        ].copy()

        output = (
            slot_dir
            / f"{slot}_test.csv"
        )

        subset.to_csv(
            output,
            index=False,
            encoding="utf-8"
        )

        print(
            f"{slot:15} "
            f"{len(subset):>4}"
        )

    print()

    print(
        "✓ Slot-specific evaluation sets created."
    )


if __name__ == "__main__":
    main()
