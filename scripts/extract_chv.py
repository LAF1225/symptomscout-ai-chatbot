from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CHV_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "oac-chv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "chv_symptom_candidates.csv"
)


SEED_PATTERNS = {
    "pain": "pain",
    "ache": "ache",
    "burn": "burn",
    "tingle": "tingl",
    "numb": "numb",
    "throb": "throb",
    "stab": "stab",
    "sharp": "sharp",
    "dull": "dull",
    "cramp": "cramp",
    "pressure": "pressure",
    "tight": "tight",
    "heavy": "heavy",
    "dizzy": "dizz",
    "weak": "weak",
    "nausea": "nause"
}


def find_concepts_file():
    candidates = []

    for path in CHV_DIR.rglob("*"):
        if not path.is_file():
            continue

        name = path.name.lower()

        if "concept" in name and "term" in name:
            candidates.append(path)

    if not candidates:
        raise FileNotFoundError(
            "Could not locate the CHV concepts/terms file."
        )

    return candidates[0]


def normalize_text(text):
    return " ".join(str(text).lower().split())


def find_seed_match(term):
    normalized = normalize_text(term)

    for label, pattern in SEED_PATTERNS.items():
        if pattern in normalized:
            return label

    return None


def main():
    input_path = find_concepts_file()

    print("Reading:")
    print(input_path)
    print()

    raw_df = pd.read_csv(
        input_path,
        sep="\t",
        header=None,
        dtype=str,
        engine="python"
    )

    # Keep only the first two documented fields.
    working_df = raw_df.iloc[:, [0, 1]].copy()

    working_df.columns = [
        "cui",
        "term"
    ]

    # If the source happens to contain a header row,
    # remove it.
    working_df = working_df[
        working_df["cui"]
        .astype(str)
        .str.upper()
        .ne("CUI")
    ]

    working_df["candidate_group"] = (
        working_df["term"]
        .apply(find_seed_match)
    )

    candidates = working_df[
        working_df["candidate_group"].notna()
    ].copy()

    candidates["normalized_term"] = (
        candidates["term"]
        .apply(normalize_text)
    )

    candidates = candidates.drop_duplicates(
        subset=["cui", "normalized_term"]
    )

    candidates["source_dataset"] = "OAC-CHV"

    candidates = candidates[
        [
            "source_dataset",
            "cui",
            "term",
            "normalized_term",
            "candidate_group"
        ]
    ]

    candidates.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8"
    )

    print(
        f"Candidate terms extracted: {len(candidates)}"
    )

    print()
    print("Candidate counts:")
    print(
        candidates["candidate_group"]
        .value_counts()
        .to_string()
    )

    print()
    print("Saved to:")
    print(OUTPUT_PATH)

    print()
    print("Examples:")
    print(
        candidates[
            ["term", "candidate_group"]
        ]
        .head(30)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()