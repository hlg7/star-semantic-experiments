# Semantic evaluation v1 — draft protocol

This is an evaluation-only specification for the existing 300 prompts and 6,000 canonical images. No new STAR images, evaluator inference, or calibrated results are included. Grounding DINO and Qwen VLM are the chosen tool families; exact checkpoint revisions are now pinned in `calibration.json`; operating parameters are provisional pilot settings, not calibrated values. This is a custom protocol inspired by object-level evaluation and atomic visual questions, not an official GenEval, TIFA or DSG score.

## Files and regeneration

- `build.py`: rebuilds the specifications from the unchanged `../csfm50_v1/prompts.json`.
- `checks.json`: 300 checks, 50 per semantic; includes the source SHA-256.
- `review.md`: all questions and scorer-side expected answers for human review.
- `calibration.json`: pinned models and provisional parameters that must be validated before full evaluation.

Run `python data/semantic_eval_v1/build.py` from the repository root. This performs no inference.

## Input isolation

Only `evaluator_input` is sent to an evaluator. Never send `scoring_only`, the original generation prompt, mask condition, expected answer, or paired baseline image. The allowed answer list is fixed within each task subtype and includes alternatives. Each image is evaluated independently. Identical question templates, preprocessing, checkpoints and thresholds apply to every condition. For detector-primary tasks, Qwen is an independent audit, never an opportunistic replacement.

Detector queries retain explicit noun phrases; count plurals use the reviewed singular mapping in `build.py`. No automatic synonym expansion is currently enabled. Any future alias list must be reviewed and frozen before full scoring. Select checkpoints with documented category coverage and validate on the actual images.

## Instance selection

Object presence accepts any valid instance. Counting includes all physical target instances, including extras; exclude identifiable reflections and depictions. This distinction requires validation because a detector may not distinguish them.

Attribute and relation questions require a unique instance of each queried object. Multiple eligible instances are `ambiguous`; do not choose the most favorable or most confident instance. Duplicate boxes of the same instance are removed using a fixed, calibrated procedure. A vague category or inseparable instances must not be silently resolved using the target attribute. Full-image Qwen is the initial protocol; optional crops are not enabled. If crops are adopted during calibration, freeze their use and construction for all applicable images.

## Per-image outcomes

`correct` = 1. `incorrect`, `missing`, `ambiguous`, and `unclear` = 0 in the primary **confirmed semantic success rate**. Report each status separately: ambiguity or uncertainty does not establish that the generator failed. Qwen returns an allowed answer only with `status=ok`, otherwise null; the scorer compares the answer with the held-out expectation. For presence/count questions, confirmed absence is respectively false/zero, not missing.

Timeouts, unreadable images, malformed JSON and invalid answers are `evaluation_error`, not semantic zeros. Retry or resolve them before reporting a complete curve. Store raw responses, detector boxes/scores, preprocessing, checkpoint revisions, decoding settings and evaluator version for auditing. A model's verbal confidence is not a probability metric.

## Six scoring rules

| Semantic | Primary evaluator | Rule | Metric |
|---|---|---|---|
| Object | Grounding DINO | At least one retained target instance | Presence rate |
| Color | Qwen | Main target-object color equals expected category; ignore minor markings/highlights | Color accuracy |
| Shape | Qwen | Overall object outline category matches, allowing identifiable perspective foreshortening; printed patterns do not count | Shape accuracy |
| Texture: pattern | Qwen | Dominant pattern matches striped/checkered/polka-dotted; background does not count | Pattern accuracy |
| Texture: surface | Qwen | Visible rough/smooth surface matches, without relying on material stereotypes | Surface accuracy |
| Count | Grounding DINO | Deduplicated instance count equals expected integer | Exact-count accuracy; MAE |
| Spatial: left/right/above/below | Grounding DINO + geometry | Unique object centers satisfy signed-axis threshold | Relation accuracy |
| Spatial: front/behind/inside/outside | Qwen | Visible depth or containment relationship matches | Relation accuracy |

Color alternatives include other/multicolored; shape alternatives include other; uncertainty always remains available. Pattern and surface are separate tasks: striped objects can also be smooth. Texture overall success may be shown, but must retain the 30-pattern / 20-surface breakdown. At 256×256, imperceptible surface detail is unclear, not guessed.

For centers normalized by image width/height: left if x_B−x_A > epsilon_x; right if x_A−x_B > epsilon_x; above if y_B−y_A > epsilon_y; below if y_A−y_B > epsilon_y. Image y increases downward. Within tolerance returns aligned, hence fails a directional target. This is a center-based 2D operational definition, not a claim about full 3D relationships. Pilot epsilons are 0.02 of image width/height; these are starting points to validate, not established tolerances.

Front/behind require depth or occlusion evidence. Inside/outside refer to the container interior, not box overlap. A protruding handle alone is compatible with containment; genuinely partial insertion is partial and does not meet either strict inside or strict outside. Ambiguous depth/containment is unclear. Report all eight relation subtypes separately.

Count MAE uses numeric counts only. If a count is not ascertainable, do not invent a numeric error: report numeric coverage alongside MAE and unresolved status rates. Detector zero is a prediction, not proof of true absence. Qwen disagreement is logged separately and cannot override the primary per-image result.

## Aggregation and paired comparisons

For each semantic/condition, confirmed success is sum(success)/50 when evaluation is complete. Keep baseline, prefix, suffix and matched-mask-count views; deduplicate shared endpoints and exclude diagnostic generation repeats. Report absolute success, paired mean change (masked−baseline), and the proportions correct→failed and failed→correct, retaining reasons such as unclear.

Baseline-correct retention uses a fixed subset chosen from that semantic's baseline evaluations, with denominator shown at every point. If no baseline succeeds, retention is undefined, not zero. Always retain the full-sample curve; the selected subset is a secondary analysis. Do not compare raw scores from unrelated tools or infer that differences between semantic groups reflect only generator sensitivity. The single seed and shared scene templates remain limitations.

## Calibration before full evaluation

Proposed development sample: 10 prompts per semantic, balanced across target values and scene families, with baseline, full-mask, prefix(1), and suffix(9): 240 existing images. Blind condition labels and annotate with this same rubric. Include correct, incorrect and unclear labels; report evaluator agreement and positive/negative errors per semantic. Use a separate held-out prompt set to validate the frozen choices; do not treat tuning-set agreement as final evaluator quality. The metadata-only selection is now saved in `pilot/sample.json`: 240 development images and 240 held-out images from disjoint prompt sets. Image review has not been performed. Selection greedily improves target-value coverage then scene coverage; it does not guarantee exact balance.

Checkpoint revisions are pinned. Validate and freeze processor, box/text thresholds, NMS policy, geometry tolerance, Qwen checkpoint revision, full-image resolution and deterministic decoding configuration. Choose thresholds based on human labels, never on the desired mask-curve trend. Run evaluator inference in a separate environment from STAR. Full-image paths and hashes must be resolved from the saved generation manifests before running. No new generation is required.

## Review findings

- The source already provides target objects and expected statements; no automatic question-generation model is needed.
- Some noun phrases (coffee pot, sugar bowl, reading lamp, hourglass) need explicit category-coverage checks.
- Noncanonical colors such as red dog require visual evidence rather than common-object priors.
- Round versus oval can be ambiguous under perspective.
- `inside` examples include spoon/mug: the containment convention above is necessary.
- Existing text includes “a open box”; original prompts and generated images remain unchanged.
- Detector-primary object/count tasks may still confuse depictions, reflections or visually similar categories. Calibration must expose these errors rather than assume the detector is ground truth.

## Method references

- [Grounding DINO](https://github.com/IDEA-Research/GroundingDINO)
- [Qwen3-VL](https://github.com/QwenLM/Qwen3-VL) — candidate family implementation, not a pinned checkpoint
- [GenEval](https://github.com/djghosh13/geneval)
- [TIFA](https://tifa-benchmark.github.io/)
- [DSG](https://github.com/j-min/DSG)

## Pilot implementation (prepared locally; GPU smoke test pending)

Selected models: `IDEA-Research/grounding-dino-base` (FP32) and `Qwen/Qwen3-VL-8B-Instruct` (BF16, SDPA, one image per call). Run them in separate processes. The 8B model's actual memory use and latency must be measured on the target GPU; no successful GPU inference is claimed here.

The pilot DINO settings are box threshold 0.30, text threshold 0.25, NMS IoU 0.50. Each noun is queried separately; the decoded label must match the complete normalized noun phrase. This conservative phrase filter can reject partial multiword matches, so its recall must be inspected during calibration. Raw pre-NMS boxes, scores and labels are retained. The detector cannot reliably exclude all reflections/depictions by itself: this remains a measured evaluator limitation, not an implemented visual filter.

Qwen uses full images, min_pixels=65536, max_pixels=262144 and greedy decoding with max_new_tokens=192. Processor resizing may round dimensions to its patch grid; upsampling does not add visual detail. Invalid JSON is an evaluation error and will be retried on rerun. Successful per-image results are cached only under an identical manifest including source/config hashes and package versions. Do not use one output directory concurrently.

From the repository root, inside a separate CUDA evaluation environment with a matching torch/torchvision pair:

```bash
python -m pip install -r requirements-semantic.txt
python run_semantic_pilot.py --images /workspace/star-csfm50-20260906 --sample data/semantic_eval_v1/pilot/sample.json --tool grounding_dino --output /workspace/star-semantic-pilot/dino --preflight
python run_semantic_pilot.py --images /workspace/star-csfm50-20260906 --sample data/semantic_eval_v1/pilot/sample.json --tool grounding_dino --output /workspace/star-semantic-pilot/dino
python run_semantic_pilot.py --images /workspace/star-csfm50-20260906 --sample data/semantic_eval_v1/pilot/sample.json --tool qwen_vlm --output /workspace/star-semantic-pilot/qwen
python export_semantic_review.py --images /workspace/star-csfm50-20260906 --sample data/semantic_eval_v1/pilot/sample.json --output /workspace/star-semantic-pilot/human-development
```

The default split is development. Do not run or inspect held-out outcomes while tuning; use `--split held_out` and new output directories after freezing the development choices. Human labels record observed answers, not expected answers; annotators receive blind images and labels.json, not sample.json or model outputs. No human agreement statistics or aggregate semantic curves exist yet.

Local verification: `python -m unittest discover -s tests -p 'test_semantic_scoring.py' -v` exercises invalid answers, count errors, coordinate directions/tolerance, missing/ambiguous instances and disjoint paired samples. It does not validate the GPU adapters or perceptual accuracy.

## Runtime verification — 2026-09-08

The original RTX 4090 Pod was restarted by the user. Its network volume is still `wen80cq46r`, mounted at `/workspace`. The separate environment `/workspace/star-semantic-env` has been installed. All 240 development image files decode as RGB 256×256 and match the input IDs, seed, condition and generation-tensor hashes in the original `runs.jsonl`.

Important provenance distinction: the historical `image_sha256` hashes the floating-point generation tensor before PNG quantization, not the PNG bytes. It cannot be recomputed from a saved PNG. The evaluator now checks it against the original run record and records separate PNG file hashes in the new evaluation manifest. These new hashes protect subsequent cache reuse; they do not independently prove historical PNG byte integrity. Both evaluators passed a two-image GPU smoke test after fixing Qwen system-message content to the multimodal list format. The 240-image development pipeline has been launched in the background; held-out and full evaluations have not started. Smoke success validates execution and parsing, not evaluator accuracy. Logs: `/workspace/star-semantic-pilot/development.log`. Current direct SSH port after restart: 14118 (rediscover on future restarts).


Development follow-up: all 240 images were processed and visually reviewed by AI. Sixteen numeric strings were normalized; sixteen invalid records were rerun with a schema reminder. See [September 8 review](../../reports/2026-09-08/README.md). AI review is not human ground truth. Protocol revisions remain necessary before held-out or full evaluation.
