from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "mts-dialog"
    / "MTS-Dialog-TrainingSet.csv"
)


def main():
    print("Reading MTS-Dialog...")
    print(f"Path: {DATA_PATH}")
    print()

    df = pd.read_csv(DATA_PATH)

    print("Dataset shape:")
    print(df.shape)
    print()

    print("Columns:")
    for column in df.columns:
        print(f" - {column}")

    print()
    print("First 5 section headers:")
    print(df["section_header"].head())

    print()
    print("Example dialogue:")
    print("-" * 60)
    print(df.iloc[0]["dialogue"])
    print("-" * 60)


if __name__ == "__main__":
    main()