from pathlib import Path
import json

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

MTS_REVIEW_PATH = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "mts_annotation_review.csv"
)

CHV_REVIEW_PATH = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "chv_review.csv"
)

SLOTS_PATH = (
    PROJECT_ROOT
    / "frameworks"
    / "slots.json"
)

OUTPUT_MTS = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "mts_labeled_examples.csv"
)

OUTPUT_PHRASES = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "dialogflow_phrase_candidates.csv"
)

OUTPUT_CONTEXT = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "contextual_examples.csv"
)

OUTPUT_ENTITIES = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "entity_terms.csv"
)


def load_valid_slots():

    with SLOTS_PATH.open(
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    return set(
        data["slots"].keys()
    )


def parse_slots(value):

    if not isinstance(value, str):
        return []

    return [
        slot.strip()
        for slot in value.split(";")
        if slot.strip()
    ]


def validate_mts_slots(df, valid_slots):

    errors = []

    for _, row in df.iterrows():

        for slot in parse_slots(
            row["final_slots"]
        ):

            if slot not in valid_slots:

                errors.append(
                    (
                        row["annotation_id"],
                        slot
                    )
                )

    if errors:

        raise ValueError(
            f"Invalid final slot labels found: {errors[:10]}"
        )


def main():

    valid_slots = load_valid_slots()

    mts = pd.read_csv(
        MTS_REVIEW_PATH
    ).fillna("")

    reviewed_mts = mts[
        mts["review_status"]
        .str.lower()
        .eq("keep")
    ].copy()

    if reviewed_mts.empty:

        raise ValueError(
            "No MTS rows have review_status=keep."
        )

    validate_mts_slots(
        reviewed_mts,
        valid_slots
    )

    reviewed_mts.to_csv(
        OUTPUT_MTS,
        index=False,
        encoding="utf-8"
    )

    context_numeric = pd.to_numeric(
        reviewed_mts[
            "context_dependent_final"
        ],
        errors="coerce"
    ).fillna(0)

    self_contained = reviewed_mts[
        context_numeric.eq(0)
    ].copy()

    contextual = reviewed_mts[
        context_numeric.eq(1)
    ].copy()

    self_contained.to_csv(
        OUTPUT_PHRASES,
        index=False,
        encoding="utf-8"
    )

    contextual.to_csv(
        OUTPUT_CONTEXT,
        index=False,
        encoding="utf-8"
    )

    chv = pd.read_csv(
        CHV_REVIEW_PATH
    ).fillna("")

    approved_entities = chv[
        chv["decision"]
        .str.lower()
        .eq("keep")
    ].copy()

    approved_entities.to_csv(
        OUTPUT_ENTITIES,
        index=False,
        encoding="utf-8"
    )

    print("Phase Three compilation complete.")
    print()

    print(
        f"Approved MTS examples: "
        f"{len(reviewed_mts):,}"
    )

    print(
        f"Self-contained phrase candidates: "
        f"{len(self_contained):,}"
    )

    print(
        f"Context-dependent examples: "
        f"{len(contextual):,}"
    )

    print(
        f"Approved vocabulary terms: "
        f"{len(approved_entities):,}"
    )


if __name__ == "__main__":
    main()