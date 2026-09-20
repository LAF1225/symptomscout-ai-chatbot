Phase 9 Final Evaluation

1. Purpose

Phase 9 is the final evaluation and release-readiness stage for the SymptomScout AI Chatbot MVP. The goal of this phase is to evaluate the frozen system without further tuning against the held-out TEST split, document the measured behavior of both the Phase 7 backend safety-signal logic and the Dialogflow CX slot-collection layer, and record limitations that must remain visible in any MVP release.

The system remains a non-diagnostic symptom communication assistant. The evaluations in this phase measure structured symptom-information collection and selected language-signal handling. They do not establish clinical validity, diagnostic accuracy, or suitability for independent medical decision-making.

2. Frozen TEST Split

The final Phase 5 TEST split contains:

57 utterances

98 annotated symptom-slot pairs

19 multi-slot utterances

The ten canonical symptom fields represented in the TEST set are:

main_symptom

site

onset

character

radiation

associated

timing

exacerbating

relieving

severity

The slot distribution was:

Slot

Annotated examples

main_symptom

9

site

8

onset

13

character

13

radiation

8

associated

14

timing

9

exacerbating

7

relieving

6

severity

11

The TEST split was treated as frozen during Phase 9 evaluation. Results from this evaluation should therefore be preserved as the initial held-out TEST results. Any later engineering changes informed by these results must be documented as post-test changes and should not be presented as though they were evaluated on an untouched held-out set.

3. Evaluation Components

Phase 9 used two complementary evaluations.

3.1 Backend Safety-Signal Evaluation

The backend evaluator tested the Phase 7 webhook logic against all 57 frozen TEST utterances.

Each utterance was evaluated once. Because the corpus is multi-label, an utterance may contain several symptom attributes in final_slots. For the webhook request, the first annotated canonical slot was used as a deterministic target so that multi-slot utterances were not counted multiple times for row-level safety labels.

This evaluation measured detection of:

ambiguity

negation

uncertainty

It did not measure Dialogflow CX slot extraction or full conversation-level multi-slot extraction.

All 57/57 webhook requests completed successfully.

3.2 Dialogflow CX Slot-Collection Evaluation

The Dialogflow evaluator tested each annotated (utterance, slot) pair independently.

For each pair:

a fresh Dialogflow CX session was created;

the session was placed directly on the collection page corresponding to the annotated slot;

the frozen utterance was submitted;

webhook execution was disabled.

This isolated Dialogflow's form/entity capture behavior from Phase 7 backend logic.

A total of 98/98 Dialogflow API requests completed successfully.

Because several MVP fields use permissive free-text collection such as @sys.any, these results measure whether the expected collection page captures the utterance, not whether Dialogflow performs clinically meaningful semantic normalization.

4. Backend Safety-Signal Results

4.1 Ambiguity Detection

Metric

Result

Precision

100.00%

Recall

28.57%

F1

44.44%

Accuracy

91.23%

True positives

2

False positives

0

False negatives

5

True negatives

50

The ambiguity detector was highly conservative: when it marked an utterance ambiguous, it did so without false positives in this TEST set. However, recall was low, with five of seven ambiguous examples not detected.

This means the current backend is better at avoiding unnecessary ambiguity flags than at detecting all ambiguous phrasing.

4.2 Negation Detection

Metric

Result

Precision

58.33%

Recall

87.50%

F1

70.00%

Accuracy

89.47%

True positives

7

False positives

5

False negatives

1

True negatives

44

Negation detection achieved the strongest recall of the three tested signals, identifying seven of eight negated examples.

The main weakness was false positives. Five non-negated examples were classified as negated, reducing precision to 58.33%.

4.3 Uncertainty Detection

Metric

Result

Precision

20.00%

Recall

50.00%

F1

28.57%

Accuracy

91.23%

True positives

1

False positives

4

False negatives

1

True negatives

51

Uncertainty was the weakest of the three tested signal classes. Only one of the two uncertain examples was detected, while four non-uncertain examples were incorrectly flagged.

The high overall accuracy is largely a consequence of the class imbalance in the TEST set and should not be interpreted as strong uncertainty-detection performance.

5. Dialogflow CX Slot-Collection Results

5.1 Overall Pair-Level Performance

Across the 98 annotated (utterance, slot) pairs:

88/98 slots were filled

Slot fill rate: 89.80%

77/98 preserved the exact utterance as the parameter value

Exact-text preservation rate: 78.57%

5.2 Row-Level Performance

Across the 57 frozen utterances:

49/57 utterances had every annotated slot capturable

All-slots-filled rate: 85.96%

39/57 utterances had every annotated slot preserve the exact utterance

All-slots-exact rate: 68.42%

5.3 Per-Slot Results

Slot

Pairs

Filled

Fill rate

Exact

Exact rate

main_symptom

9

8

88.89%

0

0.00%

site

8

8

100.00%

8

100.00%

onset

13

13

100.00%

13

100.00%

character

13

13

100.00%

13

100.00%

radiation

8

8

100.00%

8

100.00%

associated

14

13

92.86%

13

92.86%

timing

9

3

33.33%

0

0.00%

exacerbating

7

7

100.00%

7

100.00%

relieving

6

6

100.00%

6

100.00%

severity

11

9

81.82%

9

81.82%

No API-request errors occurred during the 98 pair-level evaluations.

6. Interpretation

6.1 Strongest Dialogflow Collection Areas

The following fields achieved 100% fill and 100% exact-text preservation on the frozen TEST pairs:

site

onset

character

radiation

exacerbating

relieving

These results show that, when the evaluator places a fresh session directly on the appropriate collection page, the current Dialogflow setup reliably captures the provided utterance for these fields.

associated also performed strongly, with a 92.86% fill and exact-text rate.

6.2 Timing Is the Main Dialogflow Collection Weakness

timing produced the weakest slot-collection result:

3/9 filled

33.33% fill rate

0/9 exact

0.00% exact-text preservation

This is the largest slot-specific weakness observed in the Dialogflow evaluation.

Because the TEST set has now been opened for final evaluation, this finding should be documented rather than immediately tuned against these same nine TEST examples if the project intends to preserve this as an unbiased held-out result.

6.3 Main Symptom Exact-Match Result Requires Careful Interpretation

main_symptom filled in 8/9 cases but had 0/9 exact-text preservation.

This does not necessarily mean that main-symptom collection failed. It indicates that the returned parameter value differed from the full frozen utterance according to the strict exact-text comparison used by the evaluator.

The JSON evaluation report should be consulted when analyzing the specific returned values. Any interpretation of why normalization occurred must be based on those recorded examples rather than assumed.

6.4 Safety-Signal Detection Is Uneven

The Phase 7 backend does not perform equally across ambiguity, negation, and uncertainty.

Negation had relatively strong recall but moderate precision.

Ambiguity was precise but missed most ambiguous examples.

Uncertainty had weak precision and moderate recall.

These findings matter because Phase 7 controls whether patient wording is treated as straightforward, negative, uncertain, or in need of clarification. The final MVP documentation should therefore describe these features as rule-based assistance with known limitations, not as complete or clinically validated language understanding.

7. What These Results Do Not Demonstrate

The Phase 9 evaluation does not demonstrate that the system:

diagnoses disease;

predicts disease probability;

determines the medical cause of symptoms;

is clinically validated;

reduces diagnostic error in real clinical practice;

understands arbitrary medical language;

performs medical entity normalization;

captures multiple symptom fields from a free-form sentence in a single pass;

replaces clinician history-taking;

is ready for unsupervised clinical deployment.

The Dialogflow slot evaluator deliberately places the agent on the correct collection page before submitting each utterance. It therefore measures collection behavior once the target field is already known, rather than general free-form symptom understanding.

8. Release-Readiness Assessment

8.1 Technical Execution

The evaluated release candidate successfully completed:

57/57 backend webhook requests

98/98 Dialogflow API requests

frozen TEST-set integrity checks

multi-label slot-pair evaluation

backend safety-signal evaluation

Dialogflow page discovery for all ten canonical symptom fields

There were no API or webhook execution failures in the final evaluation runs.

8.2 Functional Strengths

The release candidate demonstrates:

working end-to-end structured symptom collection architecture;

support for all ten canonical symptom fields;

reliable capture for several free-text collection pages;

functioning Phase 7 negation, uncertainty, and ambiguity logic;

deterministic Phase 8 review/confirmation architecture from the existing MVP implementation;

separation between Dialogflow collection evaluation and backend signal evaluation.

8.3 Remaining Measured Limitations

The final evaluation identified the following measurable limitations:

Ambiguity recall is low (28.57%).

Uncertainty F1 is low (28.57%).

Negation produces false positives, reducing precision to 58.33%.

Timing collection is weak, with a 33.33% fill rate.

Main-symptom exact-text preservation is 0% under the strict evaluator.

Overall exact-text preservation across slot pairs is 78.57%, not 100%.

Only 68.42% of TEST utterances had all annotated slots exactly preserved.

These limitations should remain in the final project documentation and should not be hidden by reporting only overall accuracy or overall fill rate.

9. Post-Test Engineering Rule

The frozen TEST set has now been used for final evaluation.

Therefore:

the current results should be preserved unchanged as the initial Phase 9 held-out TEST results;

the 57 TEST utterances should not be repeatedly used for tuning;

fixes motivated by the observed TEST failures should be documented as post-test engineering;

future claims of unbiased improvement should use another unseen evaluation set or a newly defined held-out benchmark.

This is particularly important for the timing, ambiguity, uncertainty, and main-symptom behaviors identified during Phase 9.

10. Reproducibility

The final evaluation is reproducible using the Phase 9 evaluation scripts and the frozen Phase 5 TEST split.

Expected source data:

data/processed/phase5/test.csv

Expected evaluation scripts:

evaluation/phase9/common.py
evaluation/phase9/run_backend_eval.py
evaluation/phase9/run_dialogflow_slot_eval.py

Generated reports:

reports/phase9/backend_eval.json
reports/phase9/backend_eval.md
reports/phase9/dialogflow_slot_eval.json
reports/phase9/dialogflow_slot_eval.md

The Dialogflow evaluation requires valid Google Cloud authentication and the environment variables for the SymptomScout agent:

$env:DIALOGFLOW_PROJECT_ID="symptomscout-ai-chatbot"
$env:DIALOGFLOW_LOCATION_ID="global"
$env:DIALOGFLOW_AGENT_ID="4f1cdda8-acb4-47d3-8f5c-450e6d1933cd"
$env:DIALOGFLOW_LANGUAGE_CODE="en"

Backend evaluation:

python evaluation\phase9\run_backend_eval.py

Dialogflow slot evaluation:

python evaluation\phase9\run_dialogflow_slot_eval.py

11. Final Phase 9 Result

Phase 9 successfully produced a held-out evaluation of both major runtime layers of the MVP.

The final measured results are:

Evaluation

Result

Backend webhook execution

57/57 successful

Dialogflow API execution

98/98 successful

Dialogflow slot fill

89.80%

Dialogflow exact-text preservation

78.57%

Rows with all annotated slots filled

85.96%

Rows with all annotated slots exact

68.42%

Ambiguity F1

44.44%

Negation F1

70.00%

Uncertainty F1

28.57%

The MVP is therefore documented as a functioning non-diagnostic symptom-communication prototype with measurable strengths and clear limitations. Phase 9 does not establish clinical validation. Its purpose is to provide a reproducible engineering evaluation and an honest baseline for future research and development.

12. Phase 9 Evaluation Freeze

The results recorded in this document constitute the initial final TEST-set evaluation for the current MVP release candidate.

No further changes should be made and then represented as part of this same untouched TEST evaluation. Any subsequent improvements should be versioned separately and evaluated against new unseen data when an unbiased comparison is required.
