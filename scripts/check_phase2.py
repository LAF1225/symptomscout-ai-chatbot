from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

MTS_PATH = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "mts_patient_utterances.csv"
)

CHV_PATH = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "chv_symptom_candidates.csv"
)


def check_file(path, required_columns):
    if not path.exists():
        raise FileNotFoundError(
            f"Missing required Phase Two file: {path}"
        )

    df = pd.read_csv(path)

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{path.name} is missing columns: "
            f"{missing_columns}"
        )

    if df.empty:
        raise ValueError(
            f"{path.name} contains no rows."
        )

    print(
        f"✓ {path.name}: "
        f"{len(df):,} rows"
    )


def main():

    check_file(
        MTS_PATH,
        [
            "source_dataset",
            "source_split",
            "source_id",
            "section_header",
            "patient_turn_number",
            "utterance"
        ]
    )

    check_file(
        CHV_PATH,
        [
            "source_dataset",
            "cui",
            "term",
            "normalized_term",
            "candidate_group"
        ]
    )

    print()
    print("✓ Phase Two data pipeline validation passed.")


if __name__ == "__main__":
    main()