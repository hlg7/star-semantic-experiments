# Frozen v3 exploratory full-set evaluation

The user authorized proceeding promptly to all 6,000 existing canonical STAR images after clarifying general ambiguity. This is **exploratory automated semantic scoring**, not a passed validation screen or human-validated accuracy. The held-out audit informed this revision and therefore does not independently validate v3.

## Fixed changes

- `notebook` means a bound paper notebook, excluding a laptop. Grounding DINO queries `paper notebook`; its decoded label may be `paper notebook` or `notebook`. This lexical alias does not prove correct detection, and Qwen definitions cannot enforce DINO category semantics.
- Plates are shallow eating/serving dishes, distinct from loaf pans, deep bowls, cutting boards, tables and solid pyramids. Shape alone is insufficient to identify a plate.
- Trays are separate portable serving carriers, not the tabletop itself. Bowls and vases require visible category structure; relative position is not an identity cue.
- Picture frames exclude monitors/windows/clock bezels; mirrors require a reflective surface rather than an architectural opening. Signs are information-bearing boards/plaques, not pillars or openings.
- Remote controls exclude gamepads; pencil cases require a writing-implement container rather than an arbitrary box.
- Color is the dominant visible **exterior material**, including permanently attached frames/body, excluding contents viewed through transparent walls. Colorless transparent material is `other`; genuinely mixed exterior colors are `multicolored`. This is an operational definition and may differ from ordinary whole-object color judgments.
- Surface texture uses dominant visible surface evidence; `mixed` requires substantial rough and smooth regions without a dominant one. Structural edges, lighting and image sharpness alone do not establish texture.

These definitions apply by noun/task across every prompt and condition, with no image-ID exception or expected-answer hint. Original prompts, target spans, scorer-only reference values, model revisions, detection thresholds and primary-tool assignments remain unchanged. Keep unique-referent requirements, containment convention and explicit unknown states from v2. Detector perception/identity mistakes remain possible; these definitions do not constitute validation.

## Workload

The 300 prompts each have 20 canonical conditions, totaling 6,000 existing images. Shared prefix/suffix endpoints are not duplicated. The earlier no-op and full-mask-repeat diagnostic images are not scored again.

- Grounding DINO: 2,600 primary evaluations (object, count and 2D position).
- Qwen: 3,400 primary evaluations (color, shape, texture, depth and containment).

Each image has exactly one primary evaluator. Auxiliary runs of the other tool over all images are omitted to avoid doubling the workload. Pilot audit results remain separate and are not substituted into v3. No v2 score is reused as a v3 full-set result.

A fixed 12-image smoke sample checks execution/schema only, not semantic performance. Both tools must finish smoke without evaluation errors before full scoring begins. Full outputs are saved atomically per image; restarting with identical inputs reuses completed records and retries evaluation errors. Any error remains an error, never a semantic zero.

## Reporting

Use **confirmed semantic success**, not true semantic accuracy: confirmed match is one, incorrect/missing/ambiguous/unclear is zero, with separate status frequencies and coverage. Exclude execution errors from means and report their denominator. Preserve all original images; do not discard difficult prompts to improve curves. Report texture pattern/surface and spatial subtypes separately, along with count MAE and numeric coverage. Compare masked and baseline scores on matched prompts/seeds, and keep the full-set result alongside any baseline-correct retention analysis.

## Files and run

- `build.py`: creates v3 checks and canonical workload from preserved v2 metadata and original metrics; never changes generation prompts.
- `checks.json`: 300 fixed evaluation specifications.
- `full_sample.json`: 6,000 unique image records.
- `smoke_sample.json`: 12 predefined execution checks.
- `freeze.json`: hashes of exact inference code, settings and metadata.
- Root `run_semantic_full.py`: primary-only CUDA runner, isolated from frozen pilot code.
- Root `run_semantic_v3_full.sh`: hash verification, smoke, then full stages.

RunPod outputs: `/workspace/star-semantic-full-v3`. The launch log is `/workspace/star-semantic-full-v3-launch.log`. Raw prompts/responses, model settings, source hashes and individual scores are retained. Full inference is launched on RunPod only.

## Completed result

The full run ended with 6,000 records: 5,999 valid scores and one out-of-vocabulary color response (`silver`). The error is preserved and excluded from its curve point and paired denominator. See the [September 9 report](../../reports/2026-09-09/README.md) for 31 figures, paired results and interpretation limits. The user stopped the Pod after inference.
