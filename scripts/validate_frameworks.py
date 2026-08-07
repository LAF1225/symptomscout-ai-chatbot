from pathlib import Path
import json


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK_DIR = PROJECT_ROOT / "frameworks"


def load_json(filename):
    path = FRAMEWORK_DIR / filename

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    print(f"✓ Loaded {filename}")
    return data


def validate_framework(framework_data, valid_slots):
    framework_name = framework_data["framework"]

    slot_order = framework_data.get("slot_order", [])
    optional_slots = framework_data.get("optional_slots", [])

    all_framework_slots = slot_order + optional_slots

    missing_slots = [
        slot
        for slot in all_framework_slots
        if slot not in valid_slots
    ]

    if missing_slots:
        raise ValueError(
            f"{framework_name} contains unknown slots: "
            f"{missing_slots}"
        )

    if len(slot_order) != len(set(slot_order)):
        raise ValueError(
            f"{framework_name} contains duplicate slots "
            "in slot_order."
        )

    question_slots = set(
        framework_data.get("questions", {}).keys()
    )

    missing_questions = [
        slot
        for slot in slot_order
        if slot not in question_slots
    ]

    if missing_questions:
        raise ValueError(
            f"{framework_name} has no question for: "
            f"{missing_questions}"
        )

    print(
        f"✓ {framework_name}: "
        f"{len(slot_order)} core slots validated"
    )


def main():
    slots_data = load_json("slots.json")
    socrates_data = load_json("socrates.json")
    opqrst_data = load_json("opqrst.json")

    valid_slots = set(slots_data["slots"].keys())

    if "main_symptom" not in valid_slots:
        raise ValueError(
            "Canonical schema must include main_symptom."
        )

    validate_framework(
        socrates_data,
        valid_slots
    )

    validate_framework(
        opqrst_data,
        valid_slots
    )

    print()
    print("✓ Phase One framework validation passed.")


if __name__ == "__main__":
    main()