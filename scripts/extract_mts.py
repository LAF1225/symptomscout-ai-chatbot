from pathlib import Path
import re

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "mts-dialog"
    / "MTS-Dialog-TrainingSet.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "mts_patient_utterances.csv"
)


ROLE_PATTERN = re.compile(
    r"(?P<speaker>Doctor|Patient|Guest_family):\s*"
    r"(?P<text>.*?)"
    r"(?=(?:Doctor|Patient|Guest_family):|$)",
    flags=re.DOTALL
)


def clean_text(text):
    """
    Replace repeated spaces, tabs and line breaks
    with single spaces.
    """
    return " ".join(str(text).split()).strip()


def extract_patient_turns(dialogue):
    """
    Find speaker-labelled turns and return
    only those spoken by the patient.
    """
    patient_turns = []

    for match in ROLE_PATTERN.finditer(str(dialogue)):
        speaker = match.group("speaker")
        text = clean_text(match.group("text"))

        if speaker == "Patient" and text:
            patient_turns.append(text)

    return patient_turns


def main():
    print("Loading MTS-Dialog training data...")

    df = pd.read_csv(INPUT_PATH)

    extracted_rows = []

    for _, row in df.iterrows():

        patient_turns = extract_patient_turns(
            row["dialogue"]
        )

        for turn_number, utterance in enumerate(
            patient_turns,
            start=1
        ):
            extracted_rows.append(
                {
                    "source_dataset": "MTS-Dialog",
                    "source_split": "train",
                    "source_id": row["ID"],
                    "section_header": row["section_header"],
                    "patient_turn_number": turn_number,
                    "utterance": utterance
                }
            )

    output_df = pd.DataFrame(extracted_rows)

    output_df.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8"
    )

    print()
    print("Extraction complete.")
    print(f"Conversations processed: {len(df)}")
    print(
        f"Patient utterances extracted: "
        f"{len(output_df)}"
    )
    print()
    print(f"Saved to:")
    print(OUTPUT_PATH)

    print()
    print("Example extracted utterances:")
    print(output_df["utterance"].head(10).to_string(index=False))


if __name__ == "__main__":
    main()