from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

EXISTING_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "final_annotated_corpus.csv"
)

PHASE4_PATH = (
    PROJECT_ROOT
    / "data"
    / "phase4"
    / "phase4_candidates.csv"
)


def normalize(text):

    return " ".join(
        str(text)
        .lower()
        .strip()
        .split()
    )


def main():

    existing = pd.read_csv(
        EXISTING_PATH
    ).fillna("")

    phase4 = pd.read_csv(
        PHASE4_PATH
    ).fillna("")

    existing_text = set(
        existing["utterance"]
        .apply(normalize)
    )

    phase4[
        "normalized_utterance"
    ] = (
        phase4["utterance"]
        .apply(normalize)
    )

    duplicate_existing = (
        phase4[
            "normalized_utterance"
        ].isin(existing_text)
    )

    duplicate_internal = (
        phase4[
            "normalized_utterance"
        ].duplicated(
            keep=False
        )
    )

    print(
        "Duplicates matching "
        "Phase 3 corpus:",
        duplicate_existing.sum()
    )

    print(
        "Duplicate Phase 4 rows:",
        duplicate_internal.sum()
    )

    if duplicate_existing.any():

        print()
        print(
            "Examples already present "
            "in Phase 3:"
        )

        print(
            phase4.loc[
                duplicate_existing,
                [
                    "example_id",
                    "utterance"
                ]
            ].to_string(
                index=False
            )
        )

    if duplicate_internal.any():

        print()
        print(
            "Repeated Phase 4 examples:"
        )

        print(
            phase4.loc[
                duplicate_internal,
                [
                    "example_id",
                    "utterance"
                ]
            ].to_string(
                index=False
            )
        )


if __name__ == "__main__":
    main()
