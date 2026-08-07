from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CHV_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "oac-chv"
)


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
            "Could not find the CHV concepts/terms flat file."
        )

    return candidates[0]


def main():
    path = find_concepts_file()

    print("Found CHV file:")
    print(path)
    print()

    df = pd.read_csv(
        path,
        sep="\t",
        header=None,
        dtype=str,
        engine="python"
    )

    print("Shape:")
    print(df.shape)

    print()
    print("First five rows:")
    print(df.head().to_string())

    print()
    print("Number of columns:")
    print(len(df.columns))


if __name__ == "__main__":
    main()