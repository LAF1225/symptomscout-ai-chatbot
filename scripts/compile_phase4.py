from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "phase4"
    / "phase4_candidates.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "phase4_approved_examples.csv"
)


def main():

    df = pd.read_csv(
        INPUT_PATH
    ).fillna("")

    approved = df[
        df["review_status"]
        .astype(str)
        .str.lower()
        .eq("keep")
    ].copy()

    approved.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8"
    )

    print(
        f"Total Phase 4 candidates: "
        f"{len(df):,}"
    )

    print(
        f"Approved Phase 4 examples: "
        f"{len(approved):,}"
    )

    print()

    print(
        f"Saved to:\n{OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
