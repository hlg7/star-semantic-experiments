# Final evaluator specification — v3

This is the consolidated specification for the **6,000-image semantic evaluation completed on September 9, 2026**. It includes all inherited rules and final clarifications; reading the v1/v2 documents is not necessary to understand the final evaluator.

The results are **exploratory automatic scores, not validated semantic accuracy**. Grounding DINO and Qwen3-VL are evaluation tools; the rules below turn their observations into scores. The earlier held-out audit informed v3, so it does not independently validate this version.

## 1. Six semantics and primary tools

| Semantic | Primary tool | Observation | Success condition | Full-set images |
|---|---|---|---|---:|
| Object | Grounding DINO | Whether a retained detection exists | At least one detected target instance | 1,000 |
| Color | Qwen3-VL | Dominant visible exterior color | Exact match to requested color | 1,000 |
| Shape | Qwen3-VL | Overall outline category | Exact match to requested shape | 1,000 |
| Texture | Qwen3-VL | Surface pattern or roughness category | Exact match to requested property | 1,000 |
| Count | Grounding DINO | Number of retained target detections | Exact match to requested count | 1,000 |
| Spatial relation | DINO for 2D position; Qwen for depth/containment | Relation between identified A and B | Exact match to requested relation | 1,000: 600 DINO + 400 Qwen |

Each image has **one predetermined primary evaluator**: 2,600 DINO and 3,400 Qwen evaluations in total. There is no voting, answer-based tool selection, or VLM override of DINO. Auxiliary predictions from earlier pilots are not substituted into final scores.

The workload contains 300 prompts, 50 per semantic, with 20 canonical conditions per prompt and seed 42. Shared prefix/suffix endpoints reuse the same image. The additional no-op and full-mask-repeat generation diagnostics are excluded. Original prompts, target spans and images are preserved.

## 2. Common observation rules

The model receives an image and the target category/task. Qwen also receives the allowed answer vocabulary and relevant category definitions. **The expected answer and generation condition are not included in model questions.** Reference answers are used by the scorer after observation; image IDs are join keys, not scoring rules.

The intended sequence is:

1. Establish object identity from visible evidence. Naming an object in a question does not establish that it exists.
2. Resolve the referent. Object existence accepts any instance; count considers all instances. Attribute and relation tasks require one identifiable instance of each named object. Multiple eligible instances are ambiguous even if their properties agree. The desired attribute or relation must not select the referent.
3. Observe the property or relation, using `unclear` when visual evidence is insufficient.
4. Compare the observation with the scorer-only reference answer.

The unique-instance requirement is an explicit operational convention, not a universal interpretation of singular language. Identity-first instructions do not guarantee correct perception. DINO uses retained detections to implement existence, count and uniqueness; it does not execute a separate reasoning-based identity check.

## 3. Category definitions

These definitions apply consistently by noun across tasks and conditions, without image-specific exceptions.

| Category | Final interpretation |
|---|---|
| Notebook | Bound paper pages for writing; excludes laptops/notebook computers. |
| Plate | Shallow individual eating or serving dish. Excludes loaf pans, deep bowls, cutting boards, tables and solid pyramids. A rectangular plate is possible; outline alone does not establish identity. |
| Tray | Separate portable flat serving carrier, usually with a rim or handles. A tabletop itself is excluded. |
| Bowl | Open, relatively deep dish for food or contents. Distinguish from flower vases and cooking/loaf pans using visible structure; unresolved identity is unclear. |
| Vase | Upright vessel intended to hold flowers, identified from vessel structure. Desired position relative to another object is not an identity cue. |
| Picture frame | Physical border intended to hold a picture; excludes monitors, window frames and clock bezels. |
| Mirror | Reflective surface; excludes open doorways, windows and empty architectural openings. Unresolved reflection versus opening is unclear. |
| Sign | Physical information-bearing signboard or plaque; excludes pillars and architectural openings. |
| Remote control | Handheld device for operating equipment at a distance; excludes gamepads/console controllers. Unresolved device identity is unclear. |
| Pencil case | Small container or pouch for writing implements; not a computer, binder or unidentified box. |

Qwen receives relevant definitions in its system message. DINO receives category queries, **not these prose rules**. Its notebook query is `paper notebook`, with accepted decoded labels `paper notebook` and `notebook`; other queries accept their configured category label. This alias does not verify identity. DINO may still detect excluded objects, reflections or depictions, and cannot be assumed to enforce every semantic distinction above.

## 4. Rules for each semantic

### Object

Run the target-category query and apply the fixed detection/label-filter/NMS procedure in Section 6. At least one retained box yields `true`; no retained box yields `false`. Object-task references request presence, so the score is one for `true` and zero for `false`.

Multiple instances are allowed. No detection is a negative detection estimate, not proof that the object is absent. The detector does not provide an explicit `unclear` result for this task.

### Color

Judge the dominant visible **exterior material** of the uniquely identified object. Include permanently attached frames/body. Ignore small decorations, highlights, shadows, reflections, empty openings and contents seen through transparent walls.

For transparent material, use its tint only when the tint itself is visible; colorless transparent material is `other`. If no single exterior color dominates, use `multicolored`. Do not choose a part because its color matches the target.

Allowed answers: `black`, `blue`, `brown`, `green`, `orange`, `pink`, `purple`, `red`, `white`, `yellow`, `other`, `multicolored`.

Score by exact category match. This exterior-material convention can differ from ordinary whole-object appearance: sand inside an hourglass or liquid inside a clear jar does not determine its exterior color. An out-of-vocabulary answer is an evaluation error, not an automatically mapped synonym.

### Shape

Judge the overall boundary of the identified object, excluding printed patterns, holes, shadows, isolated parts and convenient faces of a different 3D object. Account for perspective only when the shape remains visually identifiable; otherwise use `unclear`.

Allowed answers:

- `round`: circular, rather than merely curved.
- `oval`: elongated rounded outline.
- `square`: square outline.
- `rectangular`: non-square rectangular outline.
- `triangular`: triangular overall boundary.
- `other`: a clearly observed shape outside these categories.

Score by exact category match. A triangular face on a pyramid does not establish a triangular plate. Missing or ambiguous object identity cannot produce confirmed shape success.

### Texture

Two subtypes are evaluated and reported separately:

| Subtype | Observation rule | Allowed answers |
|---|---|---|
| Pattern | Dominant repeated pattern on the object, not the background | `striped`, `checkered`, `polka-dotted`, `plain`, `mixed`, `other` |
| Surface | Roughness of the dominant visible surface area | `rough`, `smooth`, `mixed`, `other` |

For surface texture, rough requires visible grain, pits or irregularities; smooth requires a visibly even surface. Use `mixed` when substantial rough and smooth areas coexist without a dominant one. Material stereotypes, structural edges, lighting, blur and image sharpness alone are insufficient evidence. Use `unclear` if the surface cannot be judged.

Score by exact category match. The dataset has 30 pattern prompts and 20 surface prompts; the combined curve must not hide this distinction.

### Count

The intended target is all recognizable physical instances in the whole image, including background and recognizable partially visible instances, excluding reflections and depictions. **The implemented estimate is the number of retained DINO boxes after label filtering and NMS.** There is no additional mechanism guaranteeing that every retained box is physical or every instance is detected.

The output is a nonnegative integer, including zero, with no restriction to the prompt's requested range of two through six. Multiple instances are the subject of this task and do not trigger ambiguity. DINO always returns a numeric estimate; it does not abstain on uncertain counts.

- Primary score: one if the estimated count equals the requested count, otherwise zero.
- Additional metric: `abs(estimated count - requested count)`, averaged with numeric coverage.

This additional metric is deviation from the requested count, **not counting error against independently annotated image ground truth**.

### Spatial relation

Identify both A and B before judging the relation. Missing either produces `missing`; multiple eligible instances produce `ambiguous` under the fixed unique-referent convention.

**2D position — Grounding DINO.** Query A and B separately. If either has no retained boxes, return `missing`; otherwise, if either has more than one, return `ambiguous`. For exactly one box each:

- Compute the difference between box centers, normalized by image width for horizontal relations or height for vertical relations.
- If the absolute difference is **less than 0.02**, return `aligned`.
- Otherwise, negative horizontal difference means `left`, positive means `right`; negative vertical difference means `above`, positive means `below`.

Coordinates are from the viewer's perspective, with image y increasing downward. Allowed answers are `left/right/aligned` or `above/below/aligned`, according to the task. This is a center-position rule, not a physical-depth or containment test.

**Depth — Qwen.** Use visible depth and occlusion evidence. Vertical image position alone is insufficient. Allowed answers: `front`, `behind`, `same_depth`.

**Containment — Qwen.** Judge the actual interior of the container:

- `inside`: seated or contained in the interior; protrusion above the opening does not by itself negate containment.
- `outside`: not occupying the interior.
- `partial`: crossing the opening without established settled containment.
- Use `unclear` when interior/support cannot be inferred. Box overlap alone is insufficient.

All relation subtypes use exact answer matching. Report left/right, above/below, depth and containment separately as well as the aggregate spatial curve.

## 5. Response states, scores and aggregation

Qwen is instructed to return JSON fields `identity_status`, `status`, `answer`, and brief visual `evidence`. For the final Qwen attribute/relation tasks, identity is `present`, `missing`, `ambiguous` or `unclear`. A non-present identity requires the same observation status and a null answer. Present identity can still have an unclear property. The parser checks allowed identity/status/answer combinations and answer categories; it does **not** verify the truth of the evidence text.

| Observation/result | Score | Aggregation |
|---|---:|---|
| `ok` and exact reference match → `correct` | 1 | Included |
| `ok` and valid nonmatching answer → `incorrect` | 0 | Included |
| `missing` | 0 | Included; missing frequency retained |
| `ambiguous` | 0 | Included; uncertainty frequency retained |
| `unclear` | 0 | Included; uncertainty frequency retained |
| Invalid JSON/category/status combination or execution failure → `evaluation_error` | No score | Excluded from means; error count and denominator retained |

For non-`ok` observations, the answer must be null. Comparison is type-sensitive; arbitrary prose answers are not guessed. The shared parser supports lossless unsigned numeric-string conversion for Qwen count audits, but Qwen count audits are not part of the final primary-only workload.

An invalid Qwen response gets **one fixed schema-reminder retry**. Both raw attempts are retained. If the retry is invalid, the record remains an error. There is no target-informed retry or post-hoc color mapping.

Final curves report:

1. **Confirmed semantic success:** mean score over valid records; not true generator accuracy.
2. **Paired change:** mean `(masked score - baseline score)` on the same prompt/seed with both scores valid, in percentage points.
3. **Uncertain rate:** fraction of valid records marked ambiguous or unclear. Missing rate is also retained in CSV/JSON. Zero uncertainty is not evidence of reliable perception, especially for non-abstaining DINO tasks.
4. **Baseline-correct retention:** success among valid pairs whose baseline score is one, with its denominator.
5. **Count deviation and numeric coverage**, plus texture/spatial subtype curves.

All images remain represented in the saved results. Difficult prompts are not dropped to improve curves. The plots use descriptive means, not confidence intervals; one seed and shared scene templates limit inference.

## 6. Fixed models and implementation parameters

| Setting | Value used |
|---|---|
| DINO checkpoint | `IDEA-Research/grounding-dino-base` |
| DINO model/processor revision | `12bdfa3120f3e7ec7b434d90674b3396eccf88eb` |
| Box / text thresholds | `0.30` / `0.25` |
| Per-query NMS IoU | `0.50` |
| Spatial center tolerance | `0.02` of width/height |
| Qwen checkpoint | `Qwen/Qwen3-VL-8B-Instruct` |
| Qwen model/processor revision | `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b` |
| Qwen image pixel limits | Minimum `65,536`; maximum `262,144` |
| Qwen decoding | Greedy (`do_sample=false`), maximum 192 new tokens |
| Inference | RunPod CUDA; DINO FP32, Qwen BF16 with SDPA |

DINO queries each noun independently as lowercase text with a final period. After processor postprocessing, decoded text labels must match the configured query/alias after lowercasing and word/whitespace normalization. NMS then removes overlapping retained candidates **within each query**, using detection scores. Boxes are not jointly deduplicated across different object categories. These fixed settings were not validated as optimal thresholds and do not vary by image or mask condition.

A 12-image execution/schema check passed before the full run. Each result is saved atomically. Resuming with identical inputs reuses successful records and retries error records; manifests reject changed configurations in an existing output directory.

## 7. Completed result and limitations

The run produced **6,000 records: 5,999 valid scores and one error**. For `p052_s42_suffix_08`, Qwen returned `silver`, which is not in the fixed color vocabulary. The raw response remains unchanged; color suffix k=8 uses 49 valid observations/pairs, while other main curve points use 50. See the [full report and 31 figures](../../reports/2026-09-09/README.md).

Known limitations include category confusion, fine-texture visibility, dense counting, perspective-dependent shapes and unreliable referent identity. The earlier review used AI labels rather than human ground truth, and no semantic passed every prior screening gate. V3 was revised after that review and used for exploratory full scoring. Neither fixed rules nor error-free execution establishes evaluator accuracy.

## 8. Source of truth and reproduction

| File | Role |
|---|---|
| [checks.json](checks.json) | Exact 300 per-prompt questions, allowed answers, definitions, tool assignments and scorer-only references actually used |
| [build.py](build.py) | Rebuilds v3 specifications and workload from preserved metadata; does not alter generation prompts |
| [full_sample.json](full_sample.json) | 6,000 canonical image records and condition aliases |
| [smoke_sample.json](smoke_sample.json) | 12 predefined execution checks |
| [freeze.json](freeze.json) | Hashes of the exact inference code, configuration and metadata |
| [Configuration](../semantic_eval_v1/calibration.json) | Pinned model revisions and parameters; historical filename retained |
| [run_semantic_full.py](../../run_semantic_full.py) | Actual primary-only CUDA adapter |
| [semantic_scoring.py](../../semantic_scoring.py) | Response parsing, exact matching and geometry rules |
| [run_semantic_v3_full.sh](../../run_semantic_v3_full.sh) | Hash verification, execution check and full inference stages |
| [summarize_semantic_full.py](../../summarize_semantic_full.py) | Provenance checks and paired aggregation |
| [plot_semantic_full.py](../../plot_semantic_full.py) | PNG/PDF curves and denominator annotations |

RunPod output directory: `/workspace/star-semantic-full-v3`; launch log: `/workspace/star-semantic-full-v3-launch.log`. The Pod was stopped after inference. Local aggregation and plotting need no GPU. Historical v1/v2 documents describe earlier versions; this document is the final unified entry point.
