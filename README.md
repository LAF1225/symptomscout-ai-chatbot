## Project Status

- Phase 1: Project and clinical framework setup — complete.
- Phase 2: Dataset acquisition and patient-language extraction — complete.

## Dataset Processing

External datasets are stored locally under `data/raw/` and are not
committed to this repository.

Current data sources:

- MTS-Dialog: used to extract candidate patient-language utterances.
- OAC Consumer Health Vocabulary: used to identify candidate consumer
  symptom terminology.

Processing scripts are stored under `scripts/`.

Derived interim datasets are generated locally under `data/interim/`.