from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

BASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "final_annotated_corpus.csv"
)

PHASE4_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "phase4_approved_examples.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "augmented_corpus_v1.csv"
)


def main():

    base = pd.read_csv(
        BASE_PATH
    ).fillna("")

    phase4 = pd.read_csv(
        PHASE4_PATH
    ).fillna("")

    phase4_final = pd.DataFrame()

    phase4_final[
        "annotation_id"
    ] = (
        "P4-"
        + phase4["example_id"]
        .astype(str)
    )

    phase4_final[
        "source_dataset"
    ] = "Phase4-Authored"

    phase4_final[
        "source_id"
    ] = phase4["seed_family_id"]

    phase4_final[
        "section_header"
    ] = ""

    phase4_final[
        "doctor_prompt"
    ] = ""

    phase4_final[
        "utterance"
    ] = phase4["utterance"]

    phase4_final[
        "review_status"
    ] = "keep"

    phase4_final[
        "final_slots"
    ] = phase4["intended_slots"]

    phase4_final[
        "ambiguous"
    ] = phase4["ambiguous"]

    phase4_final[
        "negated"
    ] = phase4["negated"]

    phase4_final[
        "uncertain"
    ] = phase4["uncertain"]

    phase4_final[
        "context_dependent"
    ] = phase4[
        "context_dependent"
    ]

    phase4_final[
        "annotation_source"
    ] = phase4["source_type"]

    phase4_final[
        "protocol_version"
    ] = "0.2"

    augmented = pd.concat(
        [
            base,
            phase4_final
        ],
        ignore_index=True
    )

    augmented.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8"
    )

    print(
        f"Phase 3 rows: "
        f"{len(base):,}"
    )

    print(
        f"Phase 4 rows added: "
        f"{len(phase4_final):,}"
    )

    print(
        f"Augmented corpus rows: "
        f"{len(augmented):,}"
    )

    print()

    print(
        f"Saved to:\n{OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
