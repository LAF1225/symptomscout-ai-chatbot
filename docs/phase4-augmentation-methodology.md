# Phase 4 Augmentation Methodology

## 1. Purpose

Phase 4 was designed to improve the linguistic coverage of the SymptomScout AI chatbot corpus after completion of the Phase 3 annotation pipeline.

The Phase 3 corpus contained 500 reviewed examples, of which 243 were retained as usable symptom-language examples. Corpus analysis showed that most canonical symptom slots had adequate representation, but several weaknesses remained:

- `radiation` had only 18 retained examples.
- `relieving` had 20 examples.
- `exacerbating` had 26 examples.
- `main_symptom` had 31 examples.
- Only 7 retained examples were marked as ambiguous.
- Only 84 retained examples were self-contained, while 159 depended on the immediately preceding clinician prompt.

Phase 4 therefore focused on targeted gap-filling rather than broad or uncontrolled synthetic data generation.

---

## 2. Augmentation Strategy

A controlled augmentation approach was used.

Instead of generating a large synthetic dataset, manually authored seed examples were created to target weaknesses identified during Phase 3 analysis.

The augmentation process followed this structure:

1. Identify underrepresented slots and linguistic behaviours.
2. Create manually authored seed examples.
3. Generate one controlled paraphrase for each seed.
4. Preserve the annotation labels assigned to the original seed.
5. Human-review every Phase 4 candidate.
6. Reject any candidate that altered the intended semantic content.
7. Check for duplicate examples.
8. Merge approved Phase 4 examples with the original Phase 3 corpus.
9. Re-run corpus analysis to measure improvement.

A total of **67 manual seeds** were created.

Each seed received **one controlled paraphrase**, producing:

- 67 manually authored seed examples
- 67 controlled paraphrases
- 134 total Phase 4 candidates

All 134 candidates were approved after manual review.

---

## 3. Target Areas

Phase 4 concentrated on several specific areas.

### 3.1 Radiation

Radiation was the least represented canonical slot after Phase 3, with only 18 retained examples.

Additional examples therefore included statements describing symptoms that:

- spread from one location to another,
- travelled along a body region,
- moved toward another location,
- or explicitly remained in one place.

Both positive and negated radiation statements were included where appropriate.

---

### 3.2 Relieving Factors

Relieving-factor examples were added to increase coverage of statements in which a patient explicitly describes something that reduces or improves a symptom.

A factor was labelled as `relieving` only when the patient's statement explicitly indicated improvement.

For example, simply mentioning medication was not sufficient. A statement needed to communicate that the medication, rest, position, or other factor actually improved the symptom.

---

### 3.3 Exacerbating Factors

Additional examples were created for circumstances or activities that explicitly make a symptom worse.

The augmentation preserved the distinction between:

- something occurring while a symptom was first noticed, and
- something explicitly causing the symptom to worsen.

Only the latter was labelled as `exacerbating`.

---

### 3.4 Main Symptom

Additional self-contained examples explicitly naming the patient's complaint were created to strengthen coverage of the `main_symptom` slot.

These examples were particularly useful because many Phase 3 examples were short responses whose meaning depended on a preceding clinician question.

---

### 3.5 Ambiguous Symptom Language

Phase 3 contained only 7 retained examples marked as ambiguous.

Because one of the intended functions of SymptomScout is to recognise vague patient language and ask clarification questions, Phase 4 deliberately added examples containing expressions such as:

- unusual,
- strange,
- weird,
- off,
- funny,
- or otherwise poorly specified sensations.

These expressions were not automatically converted into clinical terminology.

Instead, ambiguity was preserved so that the chatbot can later identify when clarification is required.

---

### 3.6 Self-Contained Examples

A major objective of Phase 4 was to reduce dependence on preceding dialogue context.

The Phase 3 retained corpus contained:

- 84 self-contained examples
- 159 context-dependent examples

Phase 4 examples were therefore deliberately written so that the relevant symptom information could generally be interpreted from the utterance alone.

After augmentation, the retained corpus contained:

- **218 self-contained examples**
- **159 context-dependent examples**

This substantially increased the number of examples suitable for direct use as independent training phrases.

---

## 4. Seed Design

Each manually authored seed was assigned a unique identifier and a `seed_family_id`.

The seed-family structure was preserved so that paraphrases derived from the same underlying sentence can later be kept within the same dataset partition.

This is intended to reduce train-test leakage.

For example, a seed and a closely related paraphrase should not later be split between training and evaluation data, since doing so could artificially inflate performance.

Each seed contained the following metadata:

- unique seed identifier,
- seed family identifier,
- patient utterance,
- intended canonical slots,
- ambiguity flag,
- negation flag,
- uncertainty flag,
- context-dependence flag,
- source type,
- review notes.

---

## 5. Controlled Paraphrasing

One controlled paraphrase was generated for each of the 67 manual seeds.

The purpose of paraphrasing was to increase linguistic variation without changing the underlying semantic annotation.

A valid paraphrase was required to:

- preserve the intended symptom information,
- preserve the assigned canonical slots,
- avoid introducing new symptom attributes,
- avoid removing existing symptom attributes,
- sound reasonably natural as patient language,
- avoid diagnostic interpretation,
- avoid inferred disease causes,
- avoid treatment recommendations,
- avoid urgency assessment,
- and avoid adding clinical meaning that was not present in the original seed.

Paraphrases were treated as candidate examples rather than automatically accepted training data.

---

## 6. Human Review

All 134 Phase 4 candidates underwent manual review.

Each candidate was assessed for:

- semantic consistency with the seed,
- naturalness of patient wording,
- correctness of the intended slot labels,
- preservation of ambiguity,
- preservation of negation,
- preservation of uncertainty,
- context independence,
- absence of diagnostic inference,
- and absence of unintended clinical information.

Candidates could be labelled:

- `keep`
- `discard`

All 134 Phase 4 candidates were retained after review.

The final Phase 4 contribution therefore consisted of:

| Source | Examples |
|---|---:|
| Manual seeds | 67 |
| Controlled paraphrases | 67 |
| Total approved Phase 4 examples | 134 |

---

## 7. Duplicate Control

Before augmentation, Phase 4 candidates were checked against:

1. the existing Phase 3 corpus, and
2. other Phase 4 examples.

Text was normalized for exact-duplicate detection by standardizing capitalization and whitespace.

Closely related paraphrases were permitted when they represented deliberate linguistic variation, but exact repeated utterances were not intended to be added as separate examples.

The `seed_family_id` was retained to identify semantically related examples during future dataset splitting.

---

## 8. Corpus Integration

The original Phase 3 corpus was not overwritten.

Instead, approved Phase 4 examples were combined with the Phase 3 dataset to create:

`augmented_corpus_v1.csv`

This preserves two separate artifacts:

- `final_annotated_corpus.csv` — the original Phase 3 annotation output
- `augmented_corpus_v1.csv` — the Phase 3 corpus plus reviewed Phase 4 augmentation

This distinction preserves provenance between dataset-derived examples and manually/synthetically augmented material.

---

## 9. Provenance

The augmented corpus records the source of each annotation.

The final corpus contains:

| Annotation source | Rows |
|---|---:|
| LLM agreement | 322 |
| Human adjudication | 176 |
| Manual seed | 67 |
| Controlled paraphrase | 67 |
| Human audit correction | 2 |

Protocol version information is also preserved:

| Protocol version | Rows |
|---|---:|
| 0.1 | 322 |
| 0.2 | 312 |

The original dual-LLM agreement annotations remain associated with Protocol v0.1, while human-reviewed and Phase 4 examples use the revised Protocol v0.2 framework.

---

## 10. Final Augmented Corpus

Following Phase 4 augmentation, the corpus contained:

- **634 total rows**
- **377 retained (`keep`) rows**
- **257 discarded rows**
- **0 duplicate annotation IDs**

The 377 retained rows are considered eligible for later model or chatbot training workflows.

---

## 11. Final Slot Distribution

The retained augmented corpus produced the following canonical slot counts:

| Slot | Retained examples |
|---|---:|
| `main_symptom` | 85 |
| `site` | 105 |
| `onset` | 105 |
| `character` | 75 |
| `radiation` | 42 |
| `associated` | 78 |
| `timing` | 70 |
| `exacerbating` | 56 |
| `relieving` | 42 |
| `severity` | 51 |

No canonical slot remained below the project's current 20-example screening threshold.

Radiation increased from 18 examples after Phase 3 to 42 examples after Phase 4.

---

## 12. Special-Language Coverage

Among the 377 retained augmented examples:

- 29 were marked `ambiguous`
- 56 were marked `negated`
- 27 were marked `uncertain`
- 159 were marked `context_dependent`

The number of ambiguous examples increased substantially from the Phase 3 value of 7.

This is particularly important because ambiguity recognition is a central component of the chatbot's planned clarification behaviour.

---

## 13. Multi-Slot Coverage

The final augmented corpus contained:

- 230 one-slot examples
- 48 two-slot examples
- 44 three-slot examples
- 29 four-slot examples
- 21 five-slot examples
- 5 six-slot examples

In total, **147 retained examples contained more than one canonical slot**.

Multi-slot examples are important because patients may provide several clinically relevant descriptive details in a single utterance.

The chatbot should therefore be capable of extracting multiple volunteered attributes before deciding which follow-up questions remain necessary.

---

## 14. Safety and Scope Constraints

Phase 4 augmentation followed the same non-diagnostic scope as the broader SymptomScout project.

Examples were intended only to represent how patients describe symptoms.

The augmentation process prohibited:

- diagnosis generation,
- differential diagnosis,
- inferred disease causes,
- urgency classification,
- treatment recommendations,
- medication recommendations,
- clinical interpretation beyond the stated symptom attributes,
- and automatic conversion of vague patient wording into unsupported medical terminology.

The dataset is intended to support symptom-description extraction and clarification rather than clinical decision-making.

---

## 15. Phase 4 Outcome

Phase 4 successfully addressed the principal weaknesses identified after Phase 3.

The augmented corpus increased:

- total retained examples from 243 to 377,
- self-contained retained examples from 84 to 218,
- radiation coverage from 18 to 42,
- ambiguous-language coverage from 7 to 29,
- and overall multi-slot coverage to 147 retained examples.

No canonical symptom slot remained below the current screening threshold.

The resulting `augmented_corpus_v1.csv` therefore provides a stronger and more balanced foundation for the next stage of the SymptomScout pipeline while preserving annotation provenance and the project's non-diagnostic safety boundaries.
