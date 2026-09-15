# Phase 6 — Dialogflow CX / Conversational Agents Implementation

## Project Information

**Project:** SymptomScout AI Chatbot  
**Phase:** 6  
**Platform:** Google Cloud Conversational Agents / Dialogflow CX  
**Implementation style:** Deterministic flow-based conversational agent  
**Primary language:** English  
**Status:** Complete  

---

# 1. Phase Objective

Phase 6 converted the dataset, annotation framework, and symptom-information schema developed during Phases 1–5 into a functioning conversational interface using Google Cloud Conversational Agents / Dialogflow CX.

The purpose of this phase was to establish the conversational shell of SymptomScout.

The resulting agent can:

- accept a patient's initial natural-language symptom description;
- extract multiple pieces of symptom information from the same utterance;
- preserve information already volunteered by the patient;
- ask follow-up questions for missing symptom attributes;
- collect structured and free-form patient responses;
- progress through a deterministic symptom-clarification flow;
- preserve patient wording where interpretation would otherwise be unsafe;
- terminate the normal collection sequence at a review stage.

SymptomScout remains explicitly non-diagnostic.

Phase 6 does not attempt to:

- diagnose a condition;
- generate a differential diagnosis;
- determine the medical cause of a symptom;
- recommend medication;
- recommend treatment;
- make emergency or urgency decisions;
- predict disease;
- replace a healthcare professional.

More advanced dialogue-state management and linguistic processing are intentionally deferred to the Phase 7 Python/FastAPI backend.

---

# 2. Relationship to Previous Phases

Phase 6 builds directly on the work completed during Phases 1–5.

Earlier phases established:

- the canonical symptom-slot schema;
- SOCRATES- and OPQRST-informed conversational structure;
- annotation guidelines;
- a manually and LLM-assisted annotated corpus;
- controlled corpus augmentation;
- a final augmented corpus;
- train, development, and test splits;
- linguistic rules for ambiguity, uncertainty, negation, and context dependence.

The final Phase 5 dataset contained:

- **377 keep rows**
- **268 training rows**
- **52 development rows**
- **57 test rows**

The Phase 5 split was verified to contain:

- no annotation-ID leakage;
- no seed-family leakage;
- all 377 keep rows accounted for.

Phase 6 does not retrain a standalone custom NLP model from this corpus. Instead, the linguistic work from the earlier phases informs Dialogflow entity design, intent design, training phrases, slot naming, prompts, and conversation structure.

---

# 3. Core Design Principle

SymptomScout is designed to help patients communicate symptoms more clearly to healthcare professionals.

The system therefore focuses on:

> extracting, organizing, clarifying, and preserving patient-reported symptom information.

It intentionally avoids clinical reasoning.

A key design principle is:

> **The chatbot should not ask for information the patient has already clearly provided.**

For example, if the patient says:

```text
I've had a sharp pain in my left shoulder since Tuesday.