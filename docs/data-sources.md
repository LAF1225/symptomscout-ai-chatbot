# Data Sources

This document records external datasets used during development of the
SymptomScout AI Chatbot.

Raw source datasets are stored locally in `data/raw/` and are not
redistributed through this repository unless their licences explicitly
permit redistribution and redistribution is required.

---

## MTS-Dialog

Purpose:
Patient-language extraction and conversational examples.

Original source:
https://github.com/abachaa/MTS-Dialog

Paper:
Ben Abacha, A., Yim, W., Fan, Y., & Lin, T. (2023).
An Empirical Study of Clinical Note Generation from Doctor-Patient Encounters.

Licence:
Creative Commons Attribution 4.0 International (CC BY 4.0).

Use in this project:
Only selected patient utterances from the training split are used as
candidate language examples. Diagnostic and treatment behaviour is not
used as chatbot guidance.

Redistribution decision:
Raw dataset is kept out of the repository. Derived material will be
reviewed before public release.

Downloaded:
2026-08-08

---

## OAC Consumer Health Vocabulary

Purpose:
Candidate consumer symptom terms, synonyms, vague expressions, slang and
terminology research.

Original source:
https://biomedinfo.smhs.gwu.edu/chv-files

Licence/source conditions:
See official OAC CHV download page and included licence.

Use in this project:
Candidate symptom-language terms are extracted and manually reviewed
before use as Dialogflow entities or clarification vocabulary.

Redistribution decision:
Raw files remain local. Any derived vocabulary intended for public
release will be checked against the applicable licence first.

Downloaded:
2026-08-08