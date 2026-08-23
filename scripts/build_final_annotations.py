from pathlib import Path
import pandas as pd


# ---------------------------------------------------------
# File locations
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

ANNOTATION_DIR = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "annotations"
)

AGREED_PATH = (
    ANNOTATION_DIR
    / "agreed_annotations.csv"
)

DISAGREEMENT_PATH = (
    ANNOTATION_DIR
    / "disagreements_to_review.csv"
)

AUDIT_PATH = (
    ANNOTATION_DIR
    / "agreement_audit.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "final_annotated_corpus.csv"
)


# ---------------------------------------------------------
# Allowed values
# ---------------------------------------------------------

VALID_STATUSES = {
    "keep",
    "discard",
    "needs_review"
}

VALID_SLOTS = {
    "main_symptom",
    "site",
    "onset",
    "character",
    "radiation",
    "associated",
    "timing",
    "exacerbating",
    "relieving",
    "severity"
}

CANONICAL_SLOT_ORDER = [
    "main_symptom",
    "site",
    "onset",
    "character",
    "radiation",
    "associated",
    "timing",
    "exacerbating",
    "relieving",
    "severity"
]


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def clean_status(value):
    return str(value).strip().lower()


def clean_binary(value, field_name, annotation_id):
    """
    Convert a value into integer 0 or 1.
    """

    try:
        value = int(float(value))
    except (TypeError, ValueError):
        raise ValueError(
            f"Annotation {annotation_id}: "
            f"{field_name} must be 0 or 1, "
            f"but found '{value}'."
        )

    if value not in {0, 1}:
        raise ValueError(
            f"Annotation {annotation_id}: "
            f"{field_name} must be 0 or 1."
        )

    return value


def clean_slots(value, annotation_id):
    """
    Validate slot labels and put them in canonical order.
    """

    if pd.isna(value):
        return ""

    raw_slots = [
        slot.strip()
        for slot in str(value).split(";")
        if slot.strip()
    ]

    invalid = [
        slot
        for slot in raw_slots
        if slot not in VALID_SLOTS
    ]

    if invalid:
        raise ValueError(
            f"Annotation {annotation_id}: "
            f"invalid slots found: {invalid}"
        )

    unique_slots = set(raw_slots)

    ordered = [
        slot
        for slot in CANONICAL_SLOT_ORDER
        if slot in unique_slots
    ]

    return ";".join(ordered)


# ---------------------------------------------------------
# Convert an agreed AI row
# ---------------------------------------------------------

def agreed_row_to_final(row):

    annotation_id = row["annotation_id"]

    status = clean_status(
        row["review_status_gpt"]
    )

    if status not in VALID_STATUSES:
        raise ValueError(
            f"Annotation {annotation_id}: "
            f"invalid AI review status '{status}'."
        )

    return {
        "annotation_id": annotation_id,
        "source_dataset": row["source_dataset"],
        "source_id": row["source_id"],
        "section_header": row["section_header"],
        "doctor_prompt": row["doctor_prompt"],
        "utterance": row["utterance"],

        "review_status": status,

        "final_slots": clean_slots(
            row["final_slots_gpt"],
            annotation_id
        ),

        "ambiguous": clean_binary(
            row["ambiguous_gpt"],
            "ambiguous",
            annotation_id
        ),

        "negated": clean_binary(
            row["negated_gpt"],
            "negated",
            annotation_id
        ),

        "uncertain": clean_binary(
            row["uncertain_gpt"],
            "uncertain",
            annotation_id
        ),

        "context_dependent": clean_binary(
            row["context_dependent_gpt"],
            "context_dependent",
            annotation_id
        ),

        "annotation_source": "llm_agreement",
        "protocol_version": "0.1"
    }


# ---------------------------------------------------------
# Convert a human-adjudicated disagreement
# ---------------------------------------------------------

def disagreement_row_to_final(row):

    annotation_id = row["annotation_id"]

    status = clean_status(
        row["human_final_status"]
    )

    if status not in VALID_STATUSES:
        raise ValueError(
            f"Annotation {annotation_id}: "
            f"invalid human_final_status "
            f"'{status}'."
        )

    return {
        "annotation_id": annotation_id,
        "source_dataset": row["source_dataset"],
        "source_id": row["source_id"],
        "section_header": row["section_header"],
        "doctor_prompt": row["doctor_prompt"],
        "utterance": row["utterance"],

        "review_status": status,

        "final_slots": clean_slots(
            row["human_final_slots"],
            annotation_id
        ),

        "ambiguous": clean_binary(
            row["human_ambiguous"],
            "human_ambiguous",
            annotation_id
        ),

        "negated": clean_binary(
            row["human_negated"],
            "human_negated",
            annotation_id
        ),

        "uncertain": clean_binary(
            row["human_uncertain"],
            "human_uncertain",
            annotation_id
        ),

        "context_dependent": clean_binary(
            row["human_context_dependent"],
            "human_context_dependent",
            annotation_id
        ),

        "annotation_source": "human_adjudication",
        "protocol_version": "0.2"
    }


# ---------------------------------------------------------
# Apply human audit corrections
# ---------------------------------------------------------

def apply_audit_corrections(final_df, audit):

    corrected_count = 0

    for _, row in audit.iterrows():

        annotation_id = row["annotation_id"]

        try:
            human_correct = int(
                float(row["human_correct"])
            )
        except (TypeError, ValueError):
            raise ValueError(
                f"Audit annotation {annotation_id}: "
                "human_correct must be 0 or 1."
            )

        if human_correct not in {0, 1}:
            raise ValueError(
                f"Audit annotation {annotation_id}: "
                "human_correct must be 0 or 1."
            )

        # Correct rows require no changes.
        if human_correct == 1:
            continue

        # Find this annotation in the final dataframe.
        matches = final_df[
            final_df["annotation_id"]
            == annotation_id
        ]

        if len(matches) != 1:
            raise ValueError(
                f"Audit annotation {annotation_id}: "
                "could not find exactly one matching "
                "final annotation."
            )

        status = clean_status(
            row["corrected_status"]
        )

        if status not in VALID_STATUSES:
            raise ValueError(
                f"Audit annotation {annotation_id}: "
                "corrected_status is missing or invalid."
            )

        index = matches.index[0]

        final_df.at[
            index,
            "review_status"
        ] = status

        final_df.at[
            index,
            "final_slots"
        ] = clean_slots(
            row["corrected_slots"],
            annotation_id
        )

        final_df.at[
            index,
            "ambiguous"
        ] = clean_binary(
            row["corrected_ambiguous"],
            "corrected_ambiguous",
            annotation_id
        )

        final_df.at[
            index,
            "negated"
        ] = clean_binary(
            row["corrected_negated"],
            "corrected_negated",
            annotation_id
        )

        final_df.at[
            index,
            "uncertain"
        ] = clean_binary(
            row["corrected_uncertain"],
            "corrected_uncertain",
            annotation_id
        )

        final_df.at[
            index,
            "context_dependent"
        ] = clean_binary(
            row["corrected_context_dependent"],
            "corrected_context_dependent",
            annotation_id
        )

        final_df.at[
            index,
            "annotation_source"
        ] = "human_audit_correction"

        final_df.at[
            index,
            "protocol_version"
        ] = "0.2"

        corrected_count += 1

    return final_df, corrected_count


# ---------------------------------------------------------
# Main program
# ---------------------------------------------------------

def main():

    print("Loading Phase 3.5 annotation files...")
    print()

    # Check that all required files exist.

    required_files = [
        AGREED_PATH,
        DISAGREEMENT_PATH,
        AUDIT_PATH
    ]

    for path in required_files:

        if not path.exists():
            raise FileNotFoundError(
                f"Missing required file: {path}"
            )

    agreed = pd.read_csv(
        AGREED_PATH
    ).fillna("")

    disagreements = pd.read_csv(
        DISAGREEMENT_PATH
    ).fillna("")

    audit = pd.read_csv(
        AUDIT_PATH
    ).fillna("")

    print(
        f"Agreed rows: {len(agreed):,}"
    )

    print(
        f"Disagreement rows: "
        f"{len(disagreements):,}"
    )

    print(
        f"Audit rows: {len(audit):,}"
    )

    print()

    # -----------------------------------------------------
    # Check human adjudication columns
    # -----------------------------------------------------

    required_disagreement_columns = [
        "human_final_status",
        "human_final_slots",
        "human_ambiguous",
        "human_negated",
        "human_uncertain",
        "human_context_dependent"
    ]

    missing = [
        column
        for column in required_disagreement_columns
        if column not in disagreements.columns
    ]

    if missing:
        raise ValueError(
            "Disagreement file is missing "
            f"human columns: {missing}"
        )

    # -----------------------------------------------------
    # Check audit columns
    # -----------------------------------------------------

    required_audit_columns = [
        "human_correct",
        "corrected_status",
        "corrected_slots",
        "corrected_ambiguous",
        "corrected_negated",
        "corrected_uncertain",
        "corrected_context_dependent"
    ]

    missing = [
        column
        for column in required_audit_columns
        if column not in audit.columns
    ]

    if missing:
        raise ValueError(
            "Audit file is missing correction "
            f"columns: {missing}"
        )

    # -----------------------------------------------------
    # Build agreed rows
    # -----------------------------------------------------

    agreed_final_rows = []

    for _, row in agreed.iterrows():

        agreed_final_rows.append(
            agreed_row_to_final(row)
        )

    # -----------------------------------------------------
    # Build disagreement rows
    # -----------------------------------------------------

    adjudicated_rows = []

    for _, row in disagreements.iterrows():

        adjudicated_rows.append(
            disagreement_row_to_final(row)
        )

    # -----------------------------------------------------
    # Combine
    # -----------------------------------------------------

    final_df = pd.DataFrame(
        agreed_final_rows
        + adjudicated_rows
    )

    # -----------------------------------------------------
    # Check duplicates
    # -----------------------------------------------------

    duplicated = final_df[
        final_df["annotation_id"].duplicated()
    ]

    if not duplicated.empty:

        raise ValueError(
            "Duplicate annotation IDs found: "
            f"{duplicated['annotation_id'].tolist()}"
        )

    # -----------------------------------------------------
    # Apply audit corrections
    # -----------------------------------------------------

    final_df, corrected_count = (
        apply_audit_corrections(
            final_df,
            audit
        )
    )

    # -----------------------------------------------------
    # Sort by annotation ID
    # -----------------------------------------------------

    final_df = final_df.sort_values(
        "annotation_id"
    ).reset_index(drop=True)

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    final_df.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8"
    )

    # -----------------------------------------------------
    # Final report
    # -----------------------------------------------------

    print(
        f"Audit corrections applied: "
        f"{corrected_count:,}"
    )

    print()

    print(
        f"Final corpus rows: "
        f"{len(final_df):,}"
    )

    print()

    print("Review status counts:")

    print(
        final_df[
            "review_status"
        ].value_counts().to_string()
    )

    print()

    print("Annotation source counts:")

    print(
        final_df[
            "annotation_source"
        ].value_counts().to_string()
    )

    print()

    print("Saved final corpus to:")

    print(OUTPUT_PATH)

    print()

    print(
        "✓ Final annotated corpus "
        "created successfully."
    )


if __name__ == "__main__":
    main()
    