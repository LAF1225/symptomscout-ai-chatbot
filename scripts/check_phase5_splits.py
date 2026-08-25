from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "phase5"
)


def load(name):

    return pd.read_csv(
        DATA_DIR / name
    ).fillna("")


def main():

    train = load("train.csv")
    dev = load("dev.csv")
    test = load("test.csv")

    print(
        f"Train rows: {len(train):,}"
    )

    print(
        f"Dev rows: {len(dev):,}"
    )

    print(
        f"Test rows: {len(test):,}"
    )

    print()

    # -------------------------------------------------
    # Annotation ID leakage
    # -------------------------------------------------

    train_ids = set(
        train["annotation_id"]
        .astype(str)
    )

    dev_ids = set(
        dev["annotation_id"]
        .astype(str)
    )

    test_ids = set(
        test["annotation_id"]
        .astype(str)
    )

    assert not (
        train_ids & dev_ids
    ), "ID leakage: train/dev"

    assert not (
        train_ids & test_ids
    ), "ID leakage: train/test"

    assert not (
        dev_ids & test_ids
    ), "ID leakage: dev/test"

    # -------------------------------------------------
    # Family leakage
    # -------------------------------------------------

    train_families = set(
        train["family_id"]
    )

    dev_families = set(
        dev["family_id"]
    )

    test_families = set(
        test["family_id"]
    )

    assert not (
        train_families & dev_families
    ), "Family leakage: train/dev"

    assert not (
        train_families & test_families
    ), "Family leakage: train/test"

    assert not (
        dev_families & test_families
    ), "Family leakage: dev/test"

    # -------------------------------------------------
    # Total rows
    # -------------------------------------------------

    total = (
        len(train)
        + len(dev)
        + len(test)
    )

    assert total == 377, (
        f"Expected 377 keep rows, "
        f"found {total}."
    )

    print(
        "✓ No annotation ID leakage."
    )

    print(
        "✓ No seed-family leakage."
    )

    print(
        "✓ All 377 keep rows accounted for."
    )

    print(
        "✓ Phase 5 split validation passed."
    )


if __name__ == "__main__":
    main()
