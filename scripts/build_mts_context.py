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
    / "mts_context_candidates.csv"
)


ROLE_PATTERN = re.compile(
    r"(?P<speaker>Doctor|Patient|Guest_family):\s*"
    r"(?P<text>.*?)"
    r"(?=(?:Doctor|Patient|Guest_family):|$)",
    flags=re.DOTALL
)


def clean_text(text):
    return " ".join(str(text).split()).strip()


def parse_dialogue(dialogue):

    turns = []

    for match in ROLE_PATTERN.finditer(str(dialogue)):

        turns.append(
            {
                "speaker": match.group("speaker"),
                "text": clean_text(match.group("text"))
            }
        )

    return turns


def main():

    print("Loading MTS-Dialog...")

    df = pd.read_csv(INPUT_PATH)

    output_rows = []

    for _, row in df.iterrows():

        turns = parse_dialogue(row["dialogue"])

        patient_number = 0

        for index, turn in enumerate(turns):

            if turn["speaker"] != "Patient":
                continue

            patient_number += 1

            previous_doctor = ""

            if index > 0:

                previous_turn = turns[index - 1]

                if previous_turn["speaker"] == "Doctor":
                    previous_doctor = previous_turn["text"]

            output_rows.append(
                {
                    "source_dataset": "MTS-Dialog",
                    "source_split": "train",
                    "source_id": row["ID"],
                    "section_header": row["section_header"],
                    "patient_turn_number": patient_number,
                    "doctor_prompt": previous_doctor,
                    "utterance": turn["text"]
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
        f"Contextual patient turns created: "
        f"{len(output_df):,}"
    )

    print()
    print(f"Saved to:")
    print(OUTPUT_PATH)

    print()
    print("Example:")
    print("-" * 60)

    example = output_df.iloc[0]

    print("Doctor:")
    print(example["doctor_prompt"])

    print()
    print("Patient:")
    print(example["utterance"])

    print("-" * 60)


if __name__ == "__main__":
    main()
