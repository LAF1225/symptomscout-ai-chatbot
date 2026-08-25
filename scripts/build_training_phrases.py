from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PHASE5_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "phase5"
)

INPUT_PATH = (
    PHASE5_DIR
    / "train.csv"
)

OUTPUT_PATH = (
    PHASE5_DIR
    / "training_phrases.csv"
)


def main():

    train = pd.read_csv(
        INPUT_PATH
    ).fillna("")

    training = train[
        train["context_dependent"] == 0
    ].copy()

    columns = [
        "annotation_id",
        "family_id",
        "utterance",
        "final_slots",
        "ambiguous",
        "negated",
        "uncertain",
        "annotation_source",
        "protocol_version"
    ]

    training = training[
        columns
    ]

    training.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8"
    )

    print(
        f"Total train rows: "
        f"{len(train):,}"
    )

    print(
        f"Self-contained training phrases: "
        f"{len(training):,}"
    )

    print()

    print(
        f"Saved to:\n{OUTPUT_PATH}"
    )

    print()

    print(
        "✓ Training phrase candidate "
        "dataset created."
    )


if __name__ == "__main__":
    main()
