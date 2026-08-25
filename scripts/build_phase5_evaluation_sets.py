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


def parse_slots(value):

    if pd.isna(value):
        return []

    return [
        slot.strip()
        for slot in str(value).split(";")
        if slot.strip()
    ]


def save_subset(
    df,
    filename,
    description
):

    path = (
        PHASE5_DIR
        / filename
    )

    df.to_csv(
        path,
        index=False,
        encoding="utf-8"
    )

    print(
        f"{description:25} "
        f"{len(df):>4}"
    )


def main():

    test = pd.read_csv(
        TEST_PATH
    ).fillna("")

    test["slot_count"] = (
        test["final_slots"]
        .apply(
            lambda value:
            len(parse_slots(value))
        )
    )

    contextual = test[
        test["context_dependent"] == 1
    ].copy()

    ambiguity = test[
        test["ambiguous"] == 1
    ].copy()

    negation = test[
        test["negated"] == 1
    ].copy()

    uncertainty = test[
        test["uncertain"] == 1
    ].copy()

    multislot = test[
        test["slot_count"] > 1
    ].copy()

    self_contained = test[
        test["context_dependent"] == 0
    ].copy()

    print(
        f"Full test set: {len(test):,}"
    )

    print()

    save_subset(
        self_contained,
        "self_contained_test.csv",
        "Self-contained"
    )

    save_subset(
        contextual,
        "contextual_test.csv",
        "Context-dependent"
    )

    save_subset(
        ambiguity,
        "ambiguity_test.csv",
        "Ambiguity"
    )

    save_subset(
        negation,
        "negation_test.csv",
        "Negation"
    )

    save_subset(
        uncertainty,
        "uncertainty_test.csv",
        "Uncertainty"
    )

    save_subset(
        multislot,
        "multislot_test.csv",
        "Multi-slot"
    )

    print()

    print(
        "✓ Phase 5 evaluation subsets created."
    )


if __name__ == "__main__":
    main()
