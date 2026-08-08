from pathlib import Path
import re

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "mts_context_candidates.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "mts_annotation_review.csv"
)


DOCTOR_PATTERNS = {

    "site": [
        r"\bwhere\b",
        r"\bwhich part\b",
        r"\blocation\b"
    ],

    "onset": [
        r"\bwhen did\b",
        r"\bwhen was\b",
        r"\bwhen have\b",
        r"\bwhen did it start\b"
    ],

    "character": [
        r"\bwhat does .* feel like\b",
        r"\bhow would you describe\b",
        r"\bwhat kind of pain\b",
        r"\bquality\b"
    ],

    "radiation": [
        r"\bspread\b",
        r"\bradiat",
        r"\bmove anywhere\b",
        r"\btravel\b"
    ],

    "associated": [
        r"\banything else\b",
        r"\bother symptoms\b",
        r"\bother problems\b",
        r"\bat the same time\b"
    ],

    "timing": [
        r"\bhow often\b",
        r"\bhow long does\b",
        r"\bconstant\b",
        r"\bcome and go\b",
        r"\bwhen does\b"
    ],

    "exacerbating": [
        r"\bmake.*worse\b",
        r"\bworse when\b",
        r"\baggravat",
        r"\bbring it on\b"
    ],

    "relieving": [
        r"\bmake.*better\b",
        r"\bbetter when\b",
        r"\breliev",
        r"\bwhat helps\b"
    ],

    "severity": [
        r"\b0.*10\b",
        r"\bzero.*ten\b",
        r"\bout of 10\b",
        r"\bhow severe\b",
        r"\bhow bad\b"
    ]
}


PATIENT_PATTERNS = {

    "onset": [
        r"\bstarted\b",
        r"\bbegan\b",
        r"\bsince\b",
        r"\byesterday\b",
        r"\blast night\b",
        r"\bago\b"
    ],

    "character": [
        r"\bburning\b",
        r"\baching\b",
        r"\bachy\b",
        r"\bsharp\b",
        r"\bstabbing\b",
        r"\bthrobbing\b",
        r"\bpulsing\b",
        r"\bdull\b",
        r"\bcramping\b",
        r"\bpressure\b"
    ],

    "radiation": [
        r"\bspreads?\b",
        r"\bradiates?\b",
        r"\bmoves? to\b",
        r"\btravels?\b",
        r"\bstays there\b"
    ],

    "timing": [
        r"\bconstant\b",
        r"\ball the time\b",
        r"\bcomes and goes\b",
        r"\bevery day\b",
        r"\bevery night\b",
        r"\boccasionally\b"
    ],

    "exacerbating": [
        r"\bmakes? it worse\b",
        r"\bworse when\b",
        r"\bhurts? more when\b"
    ],

    "relieving": [
        r"\bmakes? it better\b",
        r"\bfeels? better\b",
        r"\bhelps?\b",
        r"\brelieves?\b"
    ],

    "severity": [
        r"\b\d{1,2}\s*/\s*10\b",
        r"\b\d{1,2}\s+out of\s+10\b"
    ]
}


UNCERTAINTY_PATTERN = re.compile(
    r"\b("
    r"maybe|probably|possibly|"
    r"i think|i guess|"
    r"not sure|unsure|"
    r"around|approximately|about"
    r")\b",
    flags=re.IGNORECASE
)


NEGATION_PATTERN = re.compile(
    r"\b("
    r"no|not|never|none|"
    r"don't|doesn't|didn't|"
    r"haven't|hasn't|without"
    r")\b",
    flags=re.IGNORECASE
)


AMBIGUITY_PATTERN = re.compile(
    r"\b("
    r"weird|strange|odd|"
    r"off|funny|heavy|tight"
    r")\b",
    flags=re.IGNORECASE
)


def find_slots(text, pattern_dictionary):

    matches = []

    text = str(text).lower()

    for slot, patterns in pattern_dictionary.items():

        for pattern in patterns:

            if re.search(pattern, text):
                matches.append(slot)
                break

    return matches


def is_context_dependent(text):

    normalized = str(text).strip().lower()

    words = normalized.split()

    generic_answers = {
        "yes",
        "no",
        "yeah",
        "nope",
        "sometimes",
        "maybe",
        "not really"
    }

    if normalized in generic_answers:
        return True

    if len(words) <= 2:
        return True

    return False


def main():

    print("Loading contextual MTS data...")

    df = pd.read_csv(INPUT_PATH).fillna("")

    output_rows = []

    for row_id, row in df.iterrows():

        doctor_slots = find_slots(
            row["doctor_prompt"],
            DOCTOR_PATTERNS
        )

        patient_slots = find_slots(
            row["utterance"],
            PATIENT_PATTERNS
        )

        suggested_slots = sorted(
            set(doctor_slots + patient_slots)
        )

        suggested_by = []

        if doctor_slots:
            suggested_by.append("doctor_prompt")

        if patient_slots:
            suggested_by.append("patient_text")

        output_rows.append(
            {
                "annotation_id": row_id + 1,

                "source_dataset":
                    row["source_dataset"],

                "source_split":
                    row["source_split"],

                "source_id":
                    row["source_id"],

                "section_header":
                    row["section_header"],

                "patient_turn_number":
                    row["patient_turn_number"],

                "doctor_prompt":
                    row["doctor_prompt"],

                "utterance":
                    row["utterance"],

                "suggested_slots":
                    ";".join(suggested_slots),

                "suggested_by":
                    ";".join(suggested_by),

                "uncertain_hint":
                    int(
                        bool(
                            UNCERTAINTY_PATTERN.search(
                                row["utterance"]
                            )
                        )
                    ),

                "negated_hint":
                    int(
                        bool(
                            NEGATION_PATTERN.search(
                                row["utterance"]
                            )
                        )
                    ),

                "ambiguous_hint":
                    int(
                        bool(
                            AMBIGUITY_PATTERN.search(
                                row["utterance"]
                            )
                        )
                    ),

                "context_dependent_hint":
                    int(
                        is_context_dependent(
                            row["utterance"]
                        )
                    ),

                # Human annotation fields

                "review_status": "",
                "final_slots": "",
                "ambiguous_final": "",
                "negated_final": "",
                "uncertain_final": "",
                "context_dependent_final": "",
                "notes": ""
            }
        )

    output_df = pd.DataFrame(output_rows)

    output_df.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8"
    )

    print()
    print(
        f"Rows prepared for review: "
        f"{len(output_df):,}"
    )

    print()
    print("Rows receiving at least one suggestion:")

    count = (
        output_df["suggested_slots"]
        .astype(str)
        .ne("")
        .sum()
    )

    print(count)

    print()
    print("Saved to:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()