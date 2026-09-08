#!/usr/bin/env bash
set -euo pipefail
cd /workspace/star-semantic-eval-v1
export HF_HOME=/workspace/star-semantic-assets
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1
PYTHON=/workspace/star-semantic-env/bin/python
OUT=/workspace/star-semantic-full-v3
mkdir -p "$OUT"
"$PYTHON" - <<'PY'
import json,hashlib
from pathlib import Path
for p,h in json.loads(Path('data/semantic_eval_v3/freeze.json').read_text())['sha256'].items():
    assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
print('Frozen v3 full-set inputs verified.',flush=True)
PY
BASE=(--images /workspace/star-csfm50-20260906 --checks data/semantic_eval_v3/checks.json)
for TOOL in grounding_dino qwen_vlm; do
  "$PYTHON" run_semantic_full.py "${BASE[@]}" --sample data/semantic_eval_v3/smoke_sample.json --split smoke --tool "$TOOL" --output "$OUT/smoke/$TOOL" > "$OUT/smoke-$TOOL.log" 2>&1
done
printf 'Smoke checks passed; starting 6000 primary evaluations.\n'
FAILED=0
for TOOL in grounding_dino qwen_vlm; do
  if "$PYTHON" run_semantic_full.py "${BASE[@]}" --sample data/semantic_eval_v3/full_sample.json --split full --tool "$TOOL" --output "$OUT/$TOOL" > "$OUT/$TOOL.log" 2>&1; then
    printf '%s completed.\n' "$TOOL"
  else
    printf '%s exited with an error; inspect its log and preserve partial results.\n' "$TOOL"
    FAILED=1
  fi
done
printf 'Full inference stages ended; error flag=%s.\n' "$FAILED"
exit "$FAILED"
