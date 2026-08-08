from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "mts_annotation_review.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "llm_annotation_batch.csv"
)


TARGET_ROWS = 500


def main():

    df = pd.read_csv(INPUT_PATH).fillna("")

    # Prefer rows where our rule-based system
    # already found something potentially relevant.
    useful = df[
        df["suggested_slots"].astype(str).ne("")
    ].copy()

    # Shuffle reproducibly.
    useful = useful.sample(
        frac=1,
        random_state=42
    )

    batch = useful.head(TARGET_ROWS).copy()

    # Keep only the information annotators need.
    batch = batch[
        [
            "annotation_id",
            "source_dataset",
            "source_id",
            "section_header",
            "doctor_prompt",
            "utterance"
        ]
    ]

    batch.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8"
    )

    print(
        f"Annotation batch created: {len(batch)} rows"
    )

    print(f"Saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
