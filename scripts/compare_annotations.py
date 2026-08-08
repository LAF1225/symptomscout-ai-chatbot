from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

ANNOTATION_DIR = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "annotations"
)

BATCH_PATH = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "llm_annotation_batch.csv"
)

GPT_PATH = (
    ANNOTATION_DIR
    / "chatgpt_annotations.csv"
)

CLAUDE_PATH = (
    ANNOTATION_DIR
    / "claude_annotations.csv"
)

AGREED_PATH = (
    ANNOTATION_DIR
    / "agreed_annotations.csv"
)

DISAGREEMENT_PATH = (
    ANNOTATION_DIR
    / "disagreements_to_review.csv"
)


def normalize_slots(value):

    slots = [
        slot.strip()
        for slot in str(value).split(";")
        if slot.strip()
    ]

    return ";".join(sorted(set(slots)))


def normalize_text(value):
    return str(value).strip().lower()


def normalize_binary(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return value


def main():

    batch = pd.read_csv(
        BATCH_PATH
    ).fillna("")

    gpt = pd.read_csv(
        GPT_PATH
    ).fillna("")

    claude = pd.read_csv(
        CLAUDE_PATH
    ).fillna("")

    gpt["normalized_slots"] = (
        gpt["final_slots"]
        .apply(normalize_slots)
    )

    claude["normalized_slots"] = (
        claude["final_slots"]
        .apply(normalize_slots)
    )

    merged = batch.merge(
        gpt,
        on="annotation_id",
        how="inner",
        suffixes=("", "_gpt")
    )

    merged = merged.merge(
        claude,
        on="annotation_id",
        how="inner",
        suffixes=("_gpt", "_claude")
    )

    comparison_fields = [
        "review_status",
        "normalized_slots",
        "ambiguous",
        "negated",
        "uncertain",
        "context_dependent"
    ]

    agreement_columns = []

    for field in comparison_fields:

        gpt_col = f"{field}_gpt"
        claude_col = f"{field}_claude"

        if field in {
            "ambiguous",
            "negated",
            "uncertain",
            "context_dependent"
        }:

            left = merged[gpt_col].apply(
                normalize_binary
            )

            right = merged[claude_col].apply(
                normalize_binary
            )

        else:

            left = merged[gpt_col].apply(
                normalize_text
            )

            right = merged[claude_col].apply(
                normalize_text
            )

        agreement_col = (
            f"{field}_agreement"
        )

        merged[agreement_col] = (
            left == right
        )

        agreement_columns.append(
            agreement_col
        )

    merged["full_agreement"] = (
        merged[agreement_columns]
        .all(axis=1)
    )

    agreed = merged[
        merged["full_agreement"]
    ].copy()

    disagreements = merged[
        ~merged["full_agreement"]
    ].copy()

    agreed.to_csv(
        AGREED_PATH,
        index=False,
        encoding="utf-8"
    )

    disagreements.to_csv(
        DISAGREEMENT_PATH,
        index=False,
        encoding="utf-8"
    )

    total = len(merged)

    print(
        f"Rows compared: {total:,}"
    )

    print()

    print("Agreement by field:")

    for column in agreement_columns:

        rate = (
            merged[column].mean() * 100
        )

        print(
            f" - {column}: "
            f"{rate:.1f}%"
        )

    print()

    full_rate = (
        merged["full_agreement"].mean()
        * 100
    )

    print(
        f"Full-row agreement: "
        f"{full_rate:.1f}%"
    )

    print(
        f"Agreed rows: "
        f"{len(agreed):,}"
    )

    print(
        f"Rows needing review: "
        f"{len(disagreements):,}"
    )


if __name__ == "__main__":
    main()
