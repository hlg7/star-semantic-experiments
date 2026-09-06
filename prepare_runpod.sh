#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/workspace/star-baseline-assets}"
mkdir -p "$ROOT"
if [[ ! -d "$ROOT/STAR-T2I/.git" ]]; then
  git clone https://github.com/Davinci-XLab/STAR-T2I.git "$ROOT/STAR-T2I"
fi
git -C "$ROOT/STAR-T2I" checkout --detach 4ae4492b45bfa1ac24eadcf83c8d474837bfc4b1
python -m pip install -r "$(dirname "$0")/requirements.txt"
python - "$ROOT" <<'PY'
import sys
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="taocrayon/STAR",
    revision="23fab671cb225c27a85321309129994498185338",
    local_dir=sys.argv[1] + "/weights",
    allow_patterns=["CLIP/*", "vae_ch160v4096z32.pth",
                    "star_rope_d30_256-ar-ckpt-ep3-iter20000.pth"],
    ignore_patterns=["*.fp16.bin"],
)
PY
