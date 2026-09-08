#!/usr/bin/env bash
set -euo pipefail
cd /workspace/star-semantic-eval-v1
export HF_HOME=/workspace/star-semantic-assets
export TOKENIZERS_PARALLELISM=false
PYTHON=/workspace/star-semantic-env/bin/python
"$PYTHON" - <<'PY'
import json,hashlib
from pathlib import Path
m=json.loads(Path('data/semantic_eval_v2/validation/freeze.json').read_text())
for p,h in m['sha256'].items():
    assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h, p
print('Frozen validation inputs verified.',flush=True)
PY
COMMON=(--images /workspace/star-csfm50-20260906 --sample data/semantic_eval_v1/pilot/sample.json --checks data/semantic_eval_v2/checks.json --split held_out)
"$PYTHON" run_semantic_pilot.py "${COMMON[@]}" --tool qwen_vlm --output /workspace/star-semantic-pilot/v2-heldout/qwen --preflight
"$PYTHON" export_semantic_review.py --images /workspace/star-csfm50-20260906 --sample data/semantic_eval_v1/pilot/sample.json --split held_out --output /workspace/star-semantic-pilot/v2-heldout/ai-review
cp data/semantic_eval_v2/validation/ai_labels.template.json /workspace/star-semantic-pilot/v2-heldout/ai-review/labels.json
"$PYTHON" run_semantic_pilot.py "${COMMON[@]}" --tool grounding_dino --output /workspace/star-semantic-pilot/v2-heldout/dino > /workspace/star-semantic-pilot/v2-heldout/dino.log 2>&1
"$PYTHON" run_semantic_pilot.py "${COMMON[@]}" --tool qwen_vlm --output /workspace/star-semantic-pilot/v2-heldout/qwen > /workspace/star-semantic-pilot/v2-heldout/qwen.log 2>&1
printf 'Held-out inference complete. Review labels must be frozen before inspecting predictions.\n'
