from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "annotations"
    / "agreed_annotations.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "annotations"
    / "agreement_audit.csv"
)


def main():

    df = pd.read_csv(
        INPUT_PATH
    ).fillna("")

    sample_size = max(
        30,
        round(len(df) * 0.10)
    )

    sample_size = min(
        sample_size,
        len(df)
    )

    audit = df.sample(
        n=sample_size,
        random_state=42
    ).copy()

    audit["human_correct"] = ""
    audit["human_notes"] = ""

    audit.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8"
    )

    print(
        f"Audit sample created: "
        f"{len(audit)} rows"
    )

    print(
        f"Saved to: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
