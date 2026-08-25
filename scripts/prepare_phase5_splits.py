from pathlib import Path
import pandas as pd

from sklearn.model_selection import GroupShuffleSplit


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "augmented_corpus_v1.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "phase5"
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


def build_family_id(row):

    source_dataset = str(
        row.get("source_dataset", "")
    ).strip()

    source_id = str(
        row.get("source_id", "")
    ).strip()

    annotation_id = str(
        row["annotation_id"]
    ).strip()

    # Phase 4 seed + paraphrase stay together.
    if (
        source_dataset == "Phase4-Authored"
        and source_id
    ):

        return f"P4_{source_id}"

    # Original Phase 3 rows become individual families.
    return f"P3_{annotation_id}"


def add_features(df):

    df = df.copy()

    df["family_id"] = df.apply(
        build_family_id,
        axis=1
    )

    df["slot_count"] = (
        df["final_slots"]
        .apply(
            lambda value:
            len(parse_slots(value))
        )
    )

    return df


def make_split(df, random_state):

    # First split:
    # 70% train / 30% temporary

    first_split = GroupShuffleSplit(
        n_splits=1,
        train_size=0.70,
        random_state=random_state
    )

    train_index, temp_index = next(
        first_split.split(
            df,
            groups=df["family_id"]
        )
    )

    train = df.iloc[
        train_index
    ].copy()

    temp = df.iloc[
        temp_index
    ].copy()

    # Second split:
    # temporary 30% becomes:
    # 15% dev / 15% test

    second_split = GroupShuffleSplit(
        n_splits=1,
        train_size=0.50,
        random_state=random_state + 1
    )

    dev_index, test_index = next(
        second_split.split(
            temp,
            groups=temp["family_id"]
        )
    )

    dev = temp.iloc[
        dev_index
    ].copy()

    test = temp.iloc[
        test_index
    ].copy()

    return train, dev, test


def count_slot(df, slot):

    return df["final_slots"].apply(
        lambda value:
        slot in parse_slots(value)
    ).sum()


def acceptable_split(
    train,
    dev,
    test
):

    # We want every canonical slot represented
    # in every split.

    for slot in VALID_SLOTS:

        if count_slot(train, slot) < 5:
            return False

        if count_slot(dev, slot) < 2:
            return False

        if count_slot(test, slot) < 2:
            return False

    return True


def find_good_split(df):

    # Try multiple deterministic seeds so that
    # rare slots do not disappear from dev/test.

    for random_state in range(
        42,
        542
    ):

        train, dev, test = make_split(
            df,
            random_state
        )

        if acceptable_split(
            train,
            dev,
            test
        ):

            return (
                train,
                dev,
                test,
                random_state
            )

    raise RuntimeError(
        "Could not find a family-safe split "
        "with adequate slot coverage."
    )


def validate_no_family_leakage(
    train,
    dev,
    test
):

    train_families = set(
        train["family_id"]
    )

    dev_families = set(
        dev["family_id"]
    )

    test_families = set(
        test["family_id"]
    )

    if train_families & dev_families:
        raise ValueError(
            "Family leakage between train and dev."
        )

    if train_families & test_families:
        raise ValueError(
            "Family leakage between train and test."
        )

    if dev_families & test_families:
        raise ValueError(
            "Family leakage between dev and test."
        )


def print_split_summary(
    name,
    df
):

    print()
    print(name)
    print("-" * 40)

    print(
        f"Rows: {len(df):,}"
    )

    print(
        f"Families: "
        f"{df['family_id'].nunique():,}"
    )

    print(
        f"Self-contained: "
        f"{(df['context_dependent'] == 0).sum():,}"
    )

    print(
        f"Context-dependent: "
        f"{(df['context_dependent'] == 1).sum():,}"
    )

    print()

    print("Slot counts:")

    for slot in VALID_SLOTS:

        print(
            f"  {slot:15} "
            f"{count_slot(df, slot):>4}"
        )


def main():

    if not INPUT_PATH.exists():

        raise FileNotFoundError(
            f"Could not find:\n{INPUT_PATH}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    df = pd.read_csv(
        INPUT_PATH
    ).fillna("")

    print(
        f"Original augmented corpus: "
        f"{len(df):,}"
    )

    # -------------------------------------------------
    # Keep only usable examples
    # -------------------------------------------------

    df = df[
        df["review_status"]
        .astype(str)
        .str.lower()
        .eq("keep")
    ].copy()

    print(
        f"Keep examples: "
        f"{len(df):,}"
    )

    if len(df) == 0:

        raise ValueError(
            "No keep examples found."
        )

    # Convert flags to integers.

    flag_columns = [
        "ambiguous",
        "negated",
        "uncertain",
        "context_dependent"
    ]

    for column in flag_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="raise"
        ).astype(int)

    df = add_features(df)

    # -------------------------------------------------
    # Find family-safe split
    # -------------------------------------------------

    (
        train,
        dev,
        test,
        random_state
    ) = find_good_split(df)

    validate_no_family_leakage(
        train,
        dev,
        test
    )

    # -------------------------------------------------
    # Add split labels
    # -------------------------------------------------

    train["split"] = "train"
    dev["split"] = "dev"
    test["split"] = "test"

    # -------------------------------------------------
    # Save
    # -------------------------------------------------

    train.to_csv(
        OUTPUT_DIR / "train.csv",
        index=False,
        encoding="utf-8"
    )

    dev.to_csv(
        OUTPUT_DIR / "dev.csv",
        index=False,
        encoding="utf-8"
    )

    test.to_csv(
        OUTPUT_DIR / "test.csv",
        index=False,
        encoding="utf-8"
    )

    # -------------------------------------------------
    # Manifest
    # -------------------------------------------------

    manifest = pd.concat(
        [
            train[
                [
                    "annotation_id",
                    "family_id",
                    "split"
                ]
            ],
            dev[
                [
                    "annotation_id",
                    "family_id",
                    "split"
                ]
            ],
            test[
                [
                    "annotation_id",
                    "family_id",
                    "split"
                ]
            ]
        ],
        ignore_index=True
    )

    manifest.to_csv(
        OUTPUT_DIR
        / "split_manifest.csv",
        index=False,
        encoding="utf-8"
    )

    # -------------------------------------------------
    # Report
    # -------------------------------------------------

    print()
    print("=" * 60)
    print("PHASE 5 SPLIT COMPLETE")
    print("=" * 60)

    print(
        f"Chosen random seed: "
        f"{random_state}"
    )

    print_split_summary(
        "TRAIN",
        train
    )

    print_split_summary(
        "DEV",
        dev
    )

    print_split_summary(
        "TEST",
        test
    )

    print()
    print(
        "✓ No seed-family leakage."
    )

    print(
        "✓ Every slot represented "
        "in train/dev/test."
    )

    print(
        "✓ Train/dev/test files created."
    )


if __name__ == "__main__":
    main()
