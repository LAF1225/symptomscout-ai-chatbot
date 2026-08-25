# Phase 5 Dataset Preparation Methodology

## 1. Purpose

Phase 5 converted the completed augmented symptom-language corpus into fixed training, development, and test datasets for later chatbot development and evaluation.

The principal objective was to prepare the dataset for use in natural-language understanding and dialogue-system development while preventing data leakage between closely related examples.

The input to Phase 5 was:

`augmented_corpus_v1.csv`

This corpus contained:

- 634 total rows
- 377 retained (`keep`) examples
- 257 discarded examples

Only the 377 retained examples were used for Phase 5 splitting.

---

## 2. Dataset Freezing

Before splitting, `augmented_corpus_v1.csv` was treated as a frozen source artifact.

It was not manually edited during Phase 5.

All train, development, test, and evaluation files were generated as new derived datasets.

This preserved the data lineage:

`final_annotated_corpus.csv`

→ Phase 4 controlled augmentation

→ `augmented_corpus_v1.csv`

→ Phase 5 dataset splits and evaluation sets

The original Phase 3 and Phase 4 outputs therefore remained unchanged.

---

## 3. Split Strategy

The retained examples were divided into three main subsets:

- Training set
- Development set
- Test set

The intended split ratio was approximately:

- 70% training
- 15% development
- 15% test

Because related paraphrases had to remain together, the exact final percentages were allowed to vary slightly.

The final split was:

| Split | Rows |
|---|---:|
| Train | 268 |
| Development | 52 |
| Test | 57 |
| **Total** | **377** |

All 377 retained examples were successfully assigned to exactly one split.

---

## 4. Family-Aware Splitting

A major Phase 5 requirement was to prevent closely related examples from appearing in different dataset partitions.

Phase 4 contained manually authored seed examples and controlled paraphrases derived from those seeds.

For example, a sentence such as:

> The pain spreads down my arm.

and a paraphrase such as:

> The pain travels down my arm.

should not be placed in separate training and test sets, because the model could effectively be tested on wording that is extremely similar to material already seen during training.

To prevent this, a `family_id` was assigned to each example.

Phase 4 manual seeds and their corresponding paraphrases were grouped under the same family identifier.

Original Phase 3 examples that did not belong to a paraphrase family were treated as individual families.

A group-aware splitting process was then used so that an entire family could appear in only one of:

- train,
- development,
- test.

---

## 5. Leakage Validation

After splitting, the dataset was independently checked for two forms of leakage.

### 5.1 Annotation ID Leakage

No individual annotation identifier was allowed to appear in more than one split.

Validation produced:

`✓ No annotation ID leakage.`

### 5.2 Seed-Family Leakage

No seed family was allowed to appear in multiple splits.

Validation produced:

`✓ No seed-family leakage.`

### 5.3 Row Accounting

The total number of examples across all three splits was also checked.

Validation produced:

`✓ All 377 keep rows accounted for.`

These checks confirmed that the Phase 5 partition could be treated as the project's fixed train/dev/test split.

---

## 6. Slot Distribution Across Splits

The 10 canonical symptom-description slots were represented across the train, development, and test partitions.

The final distribution was:

| Slot | Train | Dev | Test |
|---|---:|---:|---:|
| `main_symptom` | 68 | 8 | 9 |
| `site` | 83 | 14 | 8 |
| `onset` | 75 | 17 | 13 |
| `character` | 56 | 6 | 13 |
| `radiation` | 30 | 4 | 8 |
| `associated` | 51 | 13 | 14 |
| `timing` | 47 | 14 | 9 |
| `exacerbating` | 44 | 5 | 7 |
| `relieving` | 27 | 9 | 6 |
| `severity` | 35 | 5 | 11 |

Every canonical slot was represented in all three splits.

This was important because it ensured that development and test evaluation would not completely omit a symptom-description category.

---

## 7. Special-Language Features

The dataset also retained several linguistic flags used to test difficult conversational behaviours.

### Ambiguity

Examples marked as ambiguous were distributed as:

| Split | Count |
|---|---:|
| Train | 19 |
| Dev | 3 |
| Test | 7 |

These examples represent vague or insufficiently specified patient descriptions that may require clarification.

### Negation

Negated expressions were distributed as:

| Split | Count |
|---|---:|
| Train | 39 |
| Dev | 9 |
| Test | 8 |

These examples are important for preventing the chatbot from confusing absence with presence.

### Uncertainty

Uncertain statements were distributed as:

| Split | Count |
|---|---:|
| Train | 19 |
| Dev | 6 |
| Test | 2 |

The test set contains only two uncertain examples. Therefore future uncertainty-specific performance should be interpreted descriptively rather than treated as a robust standalone evaluation metric.

### Context Dependence

Context-dependent utterances were distributed as:

| Split | Count |
|---|---:|
| Train | 111 |
| Dev | 27 |
| Test | 21 |

These examples require the immediately preceding clinician or chatbot question for correct interpretation.

---

## 8. Training Phrase Preparation

Not every retained utterance was suitable for direct use as an independent chatbot training phrase.

For example:

> Tuesday.

may be correctly labelled as `onset` only if it follows a question such as:

> When did it start?

Such examples are valuable for conversational-flow evaluation, but they are poor independent training phrases.

For this reason, Phase 5 created a separate training-phrase candidate dataset from the training split.

Only examples with:

`context_dependent = 0`

were selected as independent training-phrase candidates.

This created a cleaner pool of self-contained language for later Dialogflow or NLU configuration.

Context-dependent examples were retained elsewhere for dialogue testing rather than discarded.

---

## 9. Development Set Use

The development set was reserved for iterative system improvement.

It may be used to:

- test entity extraction changes,
- compare dialogue rules,
- tune clarification behaviour,
- evaluate slot extraction during development,
- and identify regressions before final testing.

Unlike the test set, development examples may be examined repeatedly while the chatbot is being improved.

---

## 10. Test Set Protection

The 57-example test set was frozen after Phase 5 validation.

Its purpose is to provide a final unseen evaluation set.

The test set should not be used to:

- design new training examples,
- tune slot rules,
- add synonyms,
- manually improve responses to specific test cases,
- or modify the chatbot based on individual test failures.

This protects the validity of later performance measurements.

---

## 11. Evaluation Subsets

To support more informative testing, Phase 5 generated several specialist views of the test set.

These subsets do not create new examples and do not change the train/dev/test split.

They are filtered views of the same frozen test set.

The evaluation subsets include:

- self-contained examples
- context-dependent examples
- ambiguous examples
- negated examples
- uncertain examples
- multi-slot examples

A single test utterance may appear in more than one specialist subset.

For example, one utterance may simultaneously be:

- multi-slot,
- negated,
- and context-dependent.

This overlap is intentional.

---

## 12. Slot-Specific Evaluation Sets

Phase 5 also generated a separate test file for each canonical slot:

- `main_symptom_test.csv`
- `site_test.csv`
- `onset_test.csv`
- `character_test.csv`
- `radiation_test.csv`
- `associated_test.csv`
- `timing_test.csv`
- `exacerbating_test.csv`
- `relieving_test.csv`
- `severity_test.csv`

These files make it possible to evaluate performance at the slot level rather than relying only on an overall accuracy score.

This is useful because a system may perform well overall while remaining weak on a specific feature such as radiation or relieving factors.

---

## 13. Multi-Slot Evaluation

Multi-slot utterances are particularly important for the SymptomScout system because patients may volunteer several symptom attributes in one sentence.

For example:

> I've had a sharp pain in my right shoulder since yesterday that gets worse when I lift my arm.

contains multiple independent attributes.

The chatbot should identify all information already provided before deciding what to ask next.

For this reason, a dedicated multi-slot evaluation subset was generated from the frozen test set.

This subset will later be used to test whether the system can extract several symptom-description slots from a single utterance without unnecessarily repeating questions.

---

## 14. Context-Dependent Evaluation

A dedicated context-dependent test subset was preserved because conversational systems must interpret short responses relative to the question that preceded them.

Examples such as:

> Tuesday.

> No.

> Mostly on the left.

cannot always be interpreted correctly in isolation.

These examples are therefore intended for later dialogue-state testing rather than simple standalone intent classification.

This distinction allows the project to separately evaluate:

- independent utterance understanding,
- and contextual conversational understanding.

---

## 15. Dataset Outputs

Phase 5 produced the following primary files:

`train.csv`

Contains the 268 training examples.

`dev.csv`

Contains the 52 development examples.

`test.csv`

Contains the 57 frozen evaluation examples.

`split_manifest.csv`

Records each annotation's assigned family and split.

`training_phrases.csv`

Contains self-contained training examples derived from the train split.

Additional evaluation files were generated for:

- ambiguity,
- negation,
- uncertainty,
- context dependence,
- self-contained language,
- multi-slot language,
- and each canonical symptom slot.

---

## 16. Reproducibility

The splitting pipeline was implemented through Python rather than manual spreadsheet assignment.

The process used deterministic random seeds and family-aware grouping.

This allows the split to be reproduced from the same source corpus and prevents accidental movement of paraphrases between datasets.

The split was frozen after validation.

Future project stages should use the existing Phase 5 files rather than repeatedly regenerating the partitions.

---

## 17. Safety and Scope Preservation

Phase 5 did not introduce new clinical interpretation.

The dataset continues to support only symptom-description communication.

The prepared data is not intended to teach the system to:

- diagnose disease,
- generate differential diagnoses,
- recommend treatment,
- infer urgency,
- determine disease causation,
- or replace professional clinical assessment.

The target outputs remain descriptive symptom attributes and clarification behaviour.

---

## 18. Phase 5 Outcome

Phase 5 successfully transformed the augmented symptom corpus into a leakage-controlled dataset suitable for chatbot development and later evaluation.

The final partition contains:

- **268 training examples**
- **52 development examples**
- **57 test examples**
- **377 total retained examples**
- **0 annotation ID leakage**
- **0 seed-family leakage**

All canonical symptom slots are represented in train, development, and test.

The dataset is now prepared for the next implementation stage, where the training resources can be connected to the chatbot's NLU and dialogue architecture while the development and test sets remain available for controlled evaluation.
