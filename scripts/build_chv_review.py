from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "chv_symptom_candidates.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "chv_review.csv"
)


PAIN_RELATED_GROUPS = {
    "pain",
    "ache",
    "burn",
    "tingle",
    "numb",
    "throb",
    "stab",
    "sharp",
    "dull",
    "cramp",
    "pressure",
    "tight",
    "heavy"
}


def main():

    df = pd.read_csv(INPUT_PATH).fillna("")

    df["review_priority"] = df[
        "candidate_group"
    ].apply(
        lambda value:
        "high"
        if value in PAIN_RELATED_GROUPS
        else "future"
    )

    df["decision"] = ""
    df["entity_type"] = ""
    df["canonical_value"] = ""
    df["ambiguous_final"] = ""
    df["notes"] = ""

    df = df.sort_values(
        [
            "review_priority",
            "candidate_group",
            "normalized_term"
        ]
    )

    df.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8"
    )

    print(
        f"CHV review rows prepared: {len(df):,}"
    )

    print()
    print("High-priority pain-language rows:")

    print(
        (
            df["review_priority"]
            == "high"
        ).sum()
    )

    print()
    print("Saved to:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()