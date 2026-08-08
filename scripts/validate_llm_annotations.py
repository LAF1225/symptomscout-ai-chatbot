from pathlib import Path
import json

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

ANNOTATION_DIR = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "annotations"
)

SCHEMA_PATH = (
    PROJECT_ROOT
    / "frameworks"
    / "annotation_schema.json"
)


FILES = [
    "chatgpt_annotations.csv",
    "claude_annotations.csv"
]


REQUIRED_COLUMNS = [
    "annotation_id",
    "review_status",
    "final_slots",
    "ambiguous",
    "negated",
    "uncertain",
    "context_dependent",
    "confidence",
    "reason"
]


def load_valid_slots():

    with SCHEMA_PATH.open(
        "r",
        encoding="utf-8"
    ) as file:

        schema = json.load(file)

    return set(schema["valid_slots"])


def validate_file(filename, valid_slots):

    path = ANNOTATION_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Missing annotation file: {filename}"
        )

    df = pd.read_csv(path).fillna("")

    missing = [
        col
        for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"{filename} missing columns: {missing}"
        )

    allowed_status = {
        "keep",
        "discard",
        "needs_review"
    }

    allowed_confidence = {
        "high",
        "medium",
        "low"
    }

    allowed_binary = {
        "0",
        "1",
        0,
        1
    }

    for _, row in df.iterrows():

        status = str(
            row["review_status"]
        ).strip().lower()

        if status not in allowed_status:
            raise ValueError(
                f"Invalid review_status in "
                f"{filename}: {status}"
            )

        confidence = str(
            row["confidence"]
        ).strip().lower()

        if confidence not in allowed_confidence:
            raise ValueError(
                f"Invalid confidence in "
                f"{filename}: {confidence}"
            )

        for flag in [
            "ambiguous",
            "negated",
            "uncertain",
            "context_dependent"
        ]:

            value = row[flag]

            try:
                value = int(value)
            except (TypeError, ValueError):
                raise ValueError(
                    f"Invalid {flag} value "
                    f"in {filename}: {value}"
                )

            if value not in {0, 1}:
                raise ValueError(
                    f"{flag} must be 0 or 1."
                )

        slots = [
            slot.strip()
            for slot in str(
                row["final_slots"]
            ).split(";")
            if slot.strip()
        ]

        for slot in slots:

            if slot not in valid_slots:
                raise ValueError(
                    f"Unknown slot '{slot}' "
                    f"in {filename}"
                )

    print(
        f"✓ {filename}: "
        f"{len(df):,} valid rows"
    )


def main():

    valid_slots = load_valid_slots()

    for filename in FILES:
        validate_file(
            filename,
            valid_slots
        )

    print()
    print(
        "✓ LLM annotation files are structurally valid."
    )


if __name__ == "__main__":
    main()
