from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "mts_patient_utterances.csv"
)


def main():
    df = pd.read_csv(DATA_PATH)

    print("MTS-Dialog Patient Utterance Summary")
    print("=" * 40)

    print(f"Total utterances: {len(df)}")
    print()

    print("Utterances by section:")
    print(
        df["section_header"]
        .value_counts()
        .head(20)
    )

    print()
    print("Average utterance length (words):")

    word_counts = (
        df["utterance"]
        .astype(str)
        .str.split()
        .str.len()
    )

    print(round(word_counts.mean(), 2))

    print()
    print("Shortest examples:")
    shortest = df.assign(
        word_count=word_counts
    ).sort_values("word_count").head(10)

    print(
        shortest[
            ["section_header", "utterance", "word_count"]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()