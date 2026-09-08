# General semantic evaluation protocol v2

**Development and held-out screening completed; not validated.** Grounding DINO and Qwen VLM remain the tool families. This revision defines task-wide semantics and a structured identity check; it does not validate either model. The v1 pilot, AI review and original prompts remain unchanged. No RunPod inference is triggered by these files.

## What is general, what is dataset-specific

The evaluator operates on `(image, task type, target object(s), answer vocabulary)`. Only the scorer receives the expected answer. Neither receives the generation condition or baseline label. IDs are join keys, never scoring conditions. Rules below apply to unseen nouns, scenes, prompts and images.

Dataset metadata necessarily supplies the noun, requested property and reference value; e.g. which object to inspect and which color was requested. The current ten-color/five-shape vocabularies define this experiment's ontology, not universal coverage of all colors and shapes. `build.py` adapts the existing input schema (including its known plural nouns) to the common evaluator interface; these lexical mappings are not image-dependent exceptions. New datasets may supply explicit canonical nouns rather than extend a guess-based pluralizer.

The 240-image development set is used to expose systematic problems. Never insert an image-specific exception, choose a threshold per image/condition, overwrite model judgments with AI review labels, discard failures to improve a curve, or choose the tool whose answer matches the target. Keep evaluator revisions separate. The held-out set has not been inspected or scored.

## Shared decision sequence

1. **Identity:** the named object is a search request, not evidence that it exists. Establish its identity from visible evidence independently of the tested attribute. Do not substitute a different object with a convenient outline or color.
2. **Reference resolution:** object existence accepts any instance; count uses all recognizable physical instances. Singular attribute/relation tasks require a unique eligible instance of each noun. Multiple eligible instances are ambiguous even if all share an attribute. This strict convention measures a uniquely resolved referent and is reported explicitly; it is not a claim that natural-language singular references always require exactly one object. No target attribute is used to select the referent. Future plural/quantified tasks require an explicit quantifier policy before evaluation.
3. **Observation:** determine the requested property without knowing its expected value. Use unclear for insufficient visual evidence.
4. **Comparison:** compare the observed answer with scorer-only reference metadata. Identity missing/ambiguous/unclear cannot produce an attribute or relation success.

Qwen outputs `identity_status`, `status`, `answer`, and brief visual `evidence`. The v2 parser rejects contradictory status/answer pairs. This creates an auditable dependency, not guaranteed visual correctness: the VLM can still misidentify an object. DINO remains the primary detector for existence/count/2D position; its detections are predictions, not verified identity labels. Qwen remains an independent audit for these tasks. No unvalidated detector/VLM voting rule is introduced.

## Task definitions

| Task | General observation rule | Primary score |
|---|---|---|
| Object | At least one recognizable instance of the specified category | Existence success |
| Color | Main visible surface color of the identified object; ignore small markings, shadows and highlights; mixed/other when appropriate | Category match |
| Shape | Overall boundary of the identified object, excluding printed patterns, internal openings, shadows and convenient faces of another object | Category match |
| Texture pattern | Dominant repeated surface pattern on the object, not background; multiple patterns may be mixed | Pattern match |
| Texture surface | Visually observable rough/smooth surface; material stereotypes and image sharpness are insufficient | Surface-property match |
| Count | All recognizable physical instances in the whole image, including background and recognizable partially visible instances; exclude reflections and depictions | Exact match and numeric MAE |
| 2D position | Normalized centers of uniquely localized A and B; left/right from viewer perspective, above/below on image axes | Relation match |
| Depth | Relative depth established from visible scene/occlusion cues; screen vertical position alone is insufficient | Relation match |
| Containment | Relation to actual container interior; box overlap alone is insufficient | Relation match |

Shape vocabulary: round means circular, oval means elongated rounded, square and non-square rectangular are distinct, triangular requires a triangular overall boundary. Allow perspective only when shape is visually identifiable; otherwise abstain. A matching face on a different 3D object cannot satisfy the queried object's shape. These are category-level definitions, not per-example corrections.

Containment: **inside** means seated/contained in the interior, and does not require complete geometric enclosure below the opening; protrusion alone does not negate containment. **outside** means not occupying the interior. **partial** means crossing the opening without established settled containment. If support/interior cannot be inferred visually, use unclear. This replaces the earlier strict protrusion interpretation and the object-part-specific exception. It applies uniformly to all container/object pairs and is a stated operational convention, not a unique interpretation of natural language.

Counting answers are unrestricted nonnegative integers, not limited to the prompt's 2–6 range. If exact enumeration is visually unresolved, Qwen must abstain. A detector still returns a numeric estimate; its omission of instances must be measured rather than hidden.

## Scores, unknowns and coverage

Preserve the v1 metric definitions: confirmed correct = 1; incorrect, missing, ambiguous and unclear = 0 in the **confirmed semantic success rate**, with their separate frequencies always reported. This rate is not the same as true generator accuracy. Also report uncertain fraction and, if useful, descriptive possible-success bounds `[confirmed/n, (confirmed+ambiguous+unclear)/n]`; these are not confidence intervals and do not account for evaluator mistakes. Do not call a rise in uncertainty a proven semantic loss.

Invalid JSON, contradictory status and failures to run are evaluation errors, not semantic zero. Unsigned numeric strings can be normalized losslessly to integers; no prose-derived answer guessing. Numeric MAE requires a numeric answer and must include coverage. Compare masked and baseline outcomes on the same prompts/seeds. Keep full-set results alongside baseline-correct subset retention and its denominator. No cross-semantic comparison of raw detector confidence is used.

## Parameters and validation

Checkpoint revisions remain pinned by the v1 pilot configuration. Box/text thresholds, deduplication IoU and normalized spatial tolerance are implementation parameters, not semantic definitions. The existing pilot values remain provisional. Tune only on development evidence with a predeclared small search, assess false positives and missed detections, and freeze parameters across conditions. No per-image or mask-dependent parameters.

Before additional inference, use the same v2 questions for **all development records of affected tasks**, including previously successful cases. Do not combine v1 scores with v2 scores into a curve. If retries are needed, use the same fixed schema reminder policy for all invalid outputs and retain attempts. Freeze the complete protocol and parameters before held-out evaluation. If held-out findings trigger further revisions, that set is no longer an untouched validation set; obtain another validation sample before claiming independent evaluation.

Current limitations: the AI review is not human ground truth; identity-first instructions do not guarantee perception; low-resolution fine texture and count ambiguity can remain unresolved. If an evaluator does not meet a predeclared acceptable error/coverage level, report that task as not validated rather than adding example-specific rules. No acceptance threshold has yet been claimed or passed.

## Files and checks

- `build.py` regenerates `checks.json` and the 300-row `review.md` from original prompts.
- `checks.json` includes `protocol_version=semantic_eval_v2` and requires the identity field.
- `semantic_scoring.py` keeps v1 parsing compatible and enforces v2 identity consistency only for v2 records.
- `tests/test_semantic_v2.py` checks missing identity, unseen nouns, count values beyond the prompt range, answer isolation and v2 schema requirements.

Run `python data/semantic_eval_v2/build.py` and `python -m unittest discover -s tests -p 'test_semantic*.py'`. No models are loaded. The general rules are now recorded; GPU adapter validation for the v2 response schema and held-out validation remain outstanding.

## Development run status (2026-09-08)

The first v2 Qwen run completed all 240 development records: 115 correct, 69 incorrect, 25 missing, 11 ambiguous, and 20 evaluation errors. These are Qwen outputs, not combined primary scores or accuracy. All 20 errors were invalid identity-status vocabulary for presence/count tasks despite a generic retry. They remain evaluation errors; no answers were silently converted.

A task-specific schema clarification is now appended uniformly to every question and to schema retries. Presence/count uses present/absent/unclear; attribute/relation uses present/missing/ambiguous/unclear. No image-specific exceptions, target answers or threshold changes were added. All 240 development images are rerun in a separate `v2-schema2/qwen-development` directory; the first run is preserved. Held-out evaluation remains pending.

The schema-clarified development run has now completed: 240 outputs, zero evaluation errors, zero retries. Source hashes, split membership and recomputed scores were verified. See [v2 audit](../../reports/2026-09-08/v2_audit.md). Visual validity remains limited; held-out inference has not started.

The held-out screen has completed, with all 240 images reviewed before prediction comparison. No semantic met every frozen screening gate; see [held-out results](../../reports/2026-09-08/heldout/README.md). Earlier run-status notes above are historical. No full-set scoring was launched.
