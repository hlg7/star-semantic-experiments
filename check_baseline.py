"""Run on RunPod only. Compare upstream and batch-corrected STAR inference."""
import argparse
import hashlib
import inspect
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import textwrap
import time

COMMIT = "4ae4492b45bfa1ac24eadcf83c8d474837bfc4b1"
WEIGHTS_REVISION = "23fab671cb225c27a85321309129994498185338"
PATCH_NUMS = (1, 2, 3, 4, 5, 6, 8, 10, 13, 16)


def arguments():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--assets", type=Path, default=Path("/workspace/star-baseline-assets"))
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--prompts", type=Path, help="Optional JSON list of prompt strings")
    p.add_argument("--seeds", type=int, nargs="+", default=[42])
    p.add_argument("--cfg", type=float, default=4.0)
    p.add_argument("--top-k", type=int, default=600)
    p.add_argument("--top-p", type=float, default=0.8)
    p.add_argument("--modes", nargs="+", choices=["upstream", "corrected"],
                   default=["upstream", "corrected"])
    return p.parse_args()


def main():
    args = arguments()
    if args.output.exists() and any(args.output.iterdir()):
        raise SystemExit("Output directory must be empty; use a new directory per diagnostic run.")
    if not 0 <= args.top_k <= 4096 or not 0 <= args.top_p <= 1 or args.cfg < 0:
        raise SystemExit("Invalid sampling settings")
    if any(seed < 0 or seed >= 2**32 for seed in args.seeds):
        raise SystemExit("Seeds must be in [0, 2**32).")
    prompts = json.loads(args.prompts.read_text()) if args.prompts else [
        "A red car.", "A blue car.", "A red car beside a green tree."]
    if not isinstance(prompts, list) or not prompts or any(
            not isinstance(p, str) or not p.strip() for p in prompts):
        raise SystemExit("Prompts must be a nonempty JSON list of nonempty strings.")

    repo = args.assets.resolve() / "STAR-T2I"
    revision = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain"], text=True).strip()
    if revision != COMMIT or dirty:
        raise SystemExit("Expected the clean, pinned upstream checkout. Do not patch its files.")
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    import numpy as np
    import torch
    from PIL import Image
    if not torch.cuda.is_available():
        raise SystemExit("CUDA required. Run this script on RunPod, not locally.")
    torch.cuda.set_device(0)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    torch.use_deterministic_algorithms(True)
    torch.backends.cuda.enable_flash_sdp(False)
    torch.backends.cuda.enable_mem_efficient_sdp(False)
    torch.backends.cuda.enable_math_sdp(True)
    sys.path.insert(0, str(repo))
    import models.basic_var as basic
    from models import build_vae_var
    from models.text_encoder import build_text

    # Compile only the pinned upstream block method, removing its two batch indices.
    # The source tree and checkpoint are never modified.
    original_forward = basic.AttnBlock.forward
    source = textwrap.dedent(inspect.getsource(original_forward))
    if source.count(")[0] + x") != 2:
        raise RuntimeError("Unexpected upstream block implementation; refusing automatic correction.")
    namespace = {}
    exec(compile(source.replace(")[0] + x", ") + x"), "<batch-corrected-AttnBlock>", "exec"),
         vars(basic), namespace)
    corrected_forward = namespace["forward"]

    # Upstream explicitly re-enables fused SDP in Attention.forward. Route its
    # existing SDP call through the math backend for both diagnostic modes.
    native_sdp = basic.F.scaled_dot_product_attention
    def diagnostic_sdp(*a, **kw):
        with torch.backends.cuda.sdp_kernel(enable_flash=False, enable_math=True,
                                             enable_mem_efficient=False):
            return native_sdp(*a, **kw)
    basic.F.scaled_dot_product_attention = diagnostic_sdp

    weights = args.assets.resolve() / "weights"
    model_path = weights / "star_rope_d30_256-ar-ckpt-ep3-iter20000.pth"
    vae, model = build_vae_var(
        device="cuda", patch_nums=PATCH_NUMS, depth=30,
        V=4096, Cvae=32, ch=160, share_quant_resi=4,
        shared_aln=False, attn_l2_norm=True, enable_cross=True, in_dim_cross=1024,
        flash_if_available=False, fused_if_available=False,
        rope_emb=True, lvl_emb=True, rope_theta=10000, rope_norm=64,
        enable_logit_norm=True, enable_adaptive_norm=False, train_mode="none",
    )
    # Official .pth is a training checkpoint, hence explicit legacy loading.
    checkpoint = torch.load(model_path, map_location="cpu", weights_only=False)
    model.load_state_dict(checkpoint["trainer"]["var_wo_ddp"], strict=True)
    del checkpoint
    vae.load_state_dict(torch.load(weights / "vae_ch160v4096z32.pth",
                                   map_location="cpu", weights_only=False), strict=True)
    text_encoder, _ = build_text(str(weights / "CLIP"), "cuda")
    for module in (model, vae, text_encoder):
        module.eval().requires_grad_(False)

    args.output.mkdir(parents=True, exist_ok=True)
    def digest(tensor):
        return hashlib.sha256(tensor.detach().contiguous().cpu().numpy().tobytes()).hexdigest()

    manifest = dict(source_commit=COMMIT, weights_revision=WEIGHTS_REVISION,
                    checkpoint=str(model_path), torch=torch.__version__,
                    cuda=torch.version.cuda, gpu=torch.cuda.get_device_name(0),
                    patch_nums=PATCH_NUMS, prompts=prompts, seeds=args.seeds,
                    cfg=args.cfg, top_k=args.top_k, top_p=args.top_p,
                    modes=args.modes, sampler=False, precision="fp16 autocast; fp32 weights",
                    attention_backend="math SDP", batch_size=1,
                    note="Diagnostic comparison, not a validated reproduction of paper metrics.")
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2))
    records = []
    failures = []
    try:
        for prompt_id, prompt in enumerate(prompts):
            tokens = text_encoder.tokenizer([prompt, ""], padding="max_length", truncation=True,
                                            return_tensors="pt")
            full_ids = text_encoder.tokenizer(prompt, truncation=False)["input_ids"]
            if len(full_ids) > text_encoder.tokenizer.model_max_length:
                raise ValueError(f"Prompt {prompt_id} would be truncated")
            with torch.inference_mode():
                hidden, mask, pooled = text_encoder.extract_text_features([prompt, ""])
            frozen = [digest(t) for t in (hidden, mask, pooled)]
            for seed in args.seeds:
                for mode in args.modes:
                    basic.AttnBlock.forward = original_forward if mode == "upstream" else corrected_forward
                    first_hash = None
                    for repeat in range(2):
                        random.seed(seed)
                        np.random.seed(seed)
                        torch.manual_seed(seed)
                        torch.cuda.manual_seed_all(seed)
                        trace = []
                        def probe(module, inputs, output):
                            if output.shape[0] != 2:
                                raise RuntimeError("Expected conditional + unconditional batch")
                            trace.append(dict(scale=len(trace) + 1,
                                token_count=output.shape[1],
                                raw_branch_rms=float((output[0].float()-output[1].float()).square().mean().sqrt()),
                                output_shape=list(output.shape)))
                        handle = model.blocks[0].cross_attn.register_forward_hook(probe)
                        torch.cuda.reset_peak_memory_stats()
                        started = time.monotonic()
                        try:
                            with torch.inference_mode(), torch.autocast("cuda", dtype=torch.float16):
                                result = model.autoregressive_infer_cfg(
                                    B=1, label_B=None, encoder_hidden_states=hidden,
                                    encoder_attention_mask=mask, encoder_pool_feat=pooled,
                                    g_seed=seed, cfg=args.cfg, top_k=args.top_k, top_p=args.top_p,
                                    more_smooth=False, w_mask=False, sample_version="new")
                            torch.cuda.synchronize()
                        finally:
                            handle.remove()
                            for block in model.blocks:
                                block.attn.kv_caching(False)
                        if not torch.isfinite(result).all():
                            raise RuntimeError("Nonfinite image output")
                        if len(trace) != len(PATCH_NUMS):
                            raise RuntimeError("Unexpected number of cross-attention calls")
                        if frozen != [digest(t) for t in (hidden, mask, pooled)]:
                            raise RuntimeError("Text conditions changed during inference")
                        image_hash = digest(result)
                        if repeat == 0:
                            first_hash = image_hash
                        elif image_hash != first_hash:
                            failures.append(f"Repeat mismatch: prompt={prompt_id}, seed={seed}, mode={mode}")
                        name = f"p{prompt_id:03d}_s{seed}_{mode}_r{repeat}"
                        pixels = result[0].permute(1, 2, 0).float().cpu().clamp(0, 1).mul(255).byte().numpy()
                        Image.fromarray(pixels).save(args.output / (name + ".png"))
                        record = dict(name=name, prompt_id=prompt_id, prompt=prompt, seed=seed,
                                      mode=mode, repeat=repeat, float_image_sha256=image_hash,
                                      repeat_matches=image_hash == first_hash,
                                      condition_sha256=frozen, input_ids=tokens.input_ids.tolist(),
                                      tokens=text_encoder.tokenizer.convert_ids_to_tokens(tokens.input_ids[0].tolist()),
                                      first_block_cross_attention=trace,
                                      elapsed_seconds=time.monotonic()-started,
                                      peak_cuda_allocated_bytes=torch.cuda.max_memory_allocated())
                        records.append(record)
                        with (args.output / "runs.jsonl").open("a") as f:
                            f.write(json.dumps(record) + "\n")
                        print(name, "saved", flush=True)
    finally:
        basic.AttnBlock.forward = original_forward
        basic.F.scaled_dot_product_attention = native_sdp
    (args.output / "summary.json").write_text(json.dumps(dict(
        completed_runs=len(records), repeat_failures=failures,
        interpretation="raw_branch_rms measures pre-index attention output, not applied residuals. "
                       "Upstream broadcasts branch 0; corrected preserves both branches. "
                       "Image quality and training-time compatibility require separate assessment."), indent=2))
    if failures:
        raise SystemExit("Reproducibility check failed; inspect summary.json")


if __name__ == "__main__":
    main()
