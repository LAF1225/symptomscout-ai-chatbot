from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "phase5"
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


def count_slot(df, slot):

    return df["final_slots"].apply(
        lambda x:
        slot in parse_slots(x)
    ).sum()


def main():

    datasets = {
        "train": pd.read_csv(
            DATA_DIR / "train.csv"
        ).fillna(""),

        "dev": pd.read_csv(
            DATA_DIR / "dev.csv"
        ).fillna(""),

        "test": pd.read_csv(
            DATA_DIR / "test.csv"
        ).fillna("")
    }

    print(
        "=" * 70
    )

    print(
        "PHASE 5 DATASET SUMMARY"
    )

    print(
        "=" * 70
    )

    print()

    for name, df in datasets.items():

        print(
            f"{name.upper()}: "
            f"{len(df):,} rows"
        )

    print()

    print(
        "SLOT DISTRIBUTION"
    )

    print(
        "-" * 70
    )

    print(
        f"{'Slot':15}"
        f"{'Train':>10}"
        f"{'Dev':>10}"
        f"{'Test':>10}"
    )

    for slot in SLOTS:

        print(
            f"{slot:15}"
            f"{count_slot(datasets['train'], slot):>10}"
            f"{count_slot(datasets['dev'], slot):>10}"
            f"{count_slot(datasets['test'], slot):>10}"
        )

    print()

    print(
        "SPECIAL FLAGS"
    )

    print(
        "-" * 70
    )

    for flag in [
        "ambiguous",
        "negated",
        "uncertain",
        "context_dependent"
    ]:

        print(flag)

        for name, df in datasets.items():

            count = (
                pd.to_numeric(
                    df[flag],
                    errors="coerce"
                )
                .eq(1)
                .sum()
            )

            print(
                f"  {name:8} {count}"
            )

    print()

    print(
        "✓ Phase 5 summary complete."
    )


if __name__ == "__main__":
    main()
