"""Scale-wise text masking with the unmodified STAR batch-broadcast behavior."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import time

from check_baseline import COMMIT, WEIGHTS_REVISION, PATCH_NUMS, source_changes


def schedules(count):
    """Unique schedules with aliases for both inclusive prefix/suffix endpoints."""
    groups = {}
    for direction in ("prefix", "suffix"):
        for boundary in range(count + 1):
            selected = tuple(range(1, boundary + 1) if direction == "prefix"
                             else range(boundary + 1, count + 1))
            groups.setdefault(selected, []).append(dict(direction=direction, boundary=boundary))
    return [(selected, aliases) for selected, aliases in groups.items()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=Path, default=Path("/workspace/star-baseline-assets"))
    parser.add_argument("--input", type=Path, default=Path(__file__).with_name("mask_smoke.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[42])
    parser.add_argument("--cfg", type=float, default=4.0)
    parser.add_argument("--top-k", type=int, default=600)
    parser.add_argument("--top-p", type=float, default=0.8)
    parser.add_argument("--weight-audit", choices=["all", "first-per-semantic"], default="all",
                        help="Audit actual QK probabilities on all inputs or the first input of each semantic; structural checks always run.")
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise SystemExit("Use an empty output directory for this verification run.")
    if not 0 <= args.top_k <= 4096 or not 0 <= args.top_p <= 1 or args.cfg < 0:
        raise SystemExit("Invalid sampling parameters")
    if any(s < 0 or s >= 2**32 for s in args.seeds):
        raise SystemExit("Seeds must be in [0, 2**32)")
    items = json.loads(args.input.read_text())
    if not isinstance(items, list) or not items:
        raise SystemExit("Input must be a nonempty list")
    seen = set()
    for item in items:
        if not isinstance(item, dict) or not all(k in item for k in ("id", "prompt", "semantic", "spans")):
            raise ValueError("Each input needs id, prompt, semantic and spans")
        if not isinstance(item["id"], str) or not item["id"] or item["id"] in seen:
            raise ValueError("Input IDs must be unique nonempty strings")
        seen.add(item["id"])
        if not isinstance(item["prompt"], str) or not item["prompt"].strip() or not item["spans"]:
            raise ValueError("Prompt and target spans must be nonempty")
        for span in item["spans"]:
            if (not isinstance(span, list) or len(span) != 2
                    or any(type(v) is not int for v in span)
                    or not 0 <= span[0] < span[1] <= len(item["prompt"])):
                raise ValueError(f"Invalid character span: {span}")

    repo = args.assets.resolve() / "STAR-T2I"
    if subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip() != COMMIT:
        raise RuntimeError("Wrong upstream source revision")
    if source_changes(repo):
        raise RuntimeError("Upstream checkout must remain clean")
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    import numpy as np
    import torch
    from PIL import Image
    from transformers import CLIPTokenizerFast
    if not torch.cuda.is_available():
        raise RuntimeError("Run on RunPod with CUDA")
    torch.cuda.set_device(0)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    torch.use_deterministic_algorithms(True)
    sys.path.insert(0, str(repo))
    import models.basic_var as basic
    from models import build_vae_var
    from models.text_encoder import build_text

    weights = args.assets.resolve() / "weights"
    print("Building model and loading checkpoint...", flush=True)
    vae, model = build_vae_var(
        device="cuda", patch_nums=PATCH_NUMS, depth=30,
        V=4096, Cvae=32, ch=160, share_quant_resi=4,
        shared_aln=False, attn_l2_norm=True, enable_cross=True, in_dim_cross=1024,
        flash_if_available=False, fused_if_available=False, rope_emb=True, lvl_emb=True,
        rope_theta=10000, rope_norm=64, enable_logit_norm=True,
        enable_adaptive_norm=False, train_mode="none")
    checkpoint = torch.load(weights / "star_rope_d30_256-ar-ckpt-ep3-iter20000.pth",
                            map_location="cpu", weights_only=False)
    model.load_state_dict(checkpoint["trainer"]["var_wo_ddp"], strict=True)
    del checkpoint
    vae.load_state_dict(torch.load(weights / "vae_ch160v4096z32.pth",
                                   map_location="cpu", weights_only=False), strict=True)
    text_encoder, _ = build_text(str(weights / "CLIP"), "cuda")
    locator = CLIPTokenizerFast.from_pretrained(str(weights / "CLIP"), subfolder="tokenizer")
    for module in (vae, model, text_encoder):
        module.eval().requires_grad_(False)
    args.output.mkdir(parents=True, exist_ok=True)

    def digest(t):
        return hashlib.sha256(t.detach().contiguous().cpu().numpy().tobytes()).hexdigest()

    manifest = dict(upstream_commit=COMMIT, weights_revision=WEIGHTS_REVISION,
                    implementation="upstream [0] broadcast; B=1", patch_nums=PATCH_NUMS,
                    config=dict(cfg=args.cfg, top_k=args.top_k, top_p=args.top_p,
                                seeds=args.seeds, sampler=False, backend="math SDP"),
                    inputs=items, weight_audit=args.weight_audit, torch=torch.__version__, cuda=torch.version.cuda,
                    gpu=torch.cuda.get_device_name(0),
                    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    intervention="Conditional text key positions only; empty-text mask unchanged. "
                                 "Upstream broadcasts the conditional attention output to both CFG branches.")
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2))
    native_sdp = basic.F.scaled_dot_product_attention
    quantizer = model.vae_quant_proxy[0]
    native_next = quantizer.get_next_autoregressive_input
    active = None
    all_records = []

    def audited_sdp(*a, **kw):
        # Audit the exact Q/K and bias passed to the existing attention kernel.
        if active is not None:
            if not active["audit_weights"]:
                active["audit"].append(dict(layer=active["layer"], scale=active["scale"],
                                            masked=active["masked"], audit_type="structural"))
                with torch.backends.cuda.sdp_kernel(enable_flash=False, enable_math=True, enable_mem_efficient=False):
                    return native_sdp(*a, **kw)
            bias = kw["attn_mask"]
            q, k = kw["query"], kw["key"]
            with torch.autocast("cuda", enabled=False):
                scores = (q[0].float() * kw["scale"]) @ k[0].float().transpose(-2, -1)
                probabilities = (scores + bias[0].float()).softmax(-1)
                maximum = float(probabilities[..., active["positions"]].max())
            if not torch.isfinite(probabilities).all():
                raise RuntimeError("Nonfinite audited attention probabilities")
            active["audit"].append(dict(layer=active["layer"], scale=active["scale"],
                                        masked=active["masked"], target_max_weight=maximum))
            if active["masked"] and maximum != 0:
                raise RuntimeError("Target attention weight is not zero")
        with torch.backends.cuda.sdp_kernel(enable_flash=False, enable_math=True, enable_mem_efficient=False):
            return native_sdp(*a, **kw)
    basic.F.scaled_dot_product_attention = audited_sdp

    audited_semantics = set()
    try:
        for item_index, item in enumerate(items):
            audit_weights = args.weight_audit == "all" or item["semantic"] not in audited_semantics
            audited_semantics.add(item["semantic"])
            prompt = item["prompt"]
            actual = text_encoder.tokenizer(prompt, truncation=False)["input_ids"]
            located = locator(prompt, truncation=False, return_offsets_mapping=True)
            if actual != located["input_ids"]:
                raise ValueError("Fast/official tokenizer IDs differ; manually resolve spans before running")
            if len(actual) > text_encoder.tokenizer.model_max_length:
                raise ValueError("Prompt exceeds text context; refusing truncation")
            positions = sorted({i for i, (a, b) in enumerate(located["offset_mapping"])
                                if b > a and any(a < end and b > start for start, end in item["spans"])})
            for start, end in item["spans"]:
                overlaps = [i for i in positions if located["offset_mapping"][i][0] < end
                            and located["offset_mapping"][i][1] > start]
                if not overlaps:
                    raise ValueError("Target span has no text tokens")
                if any(located["offset_mapping"][i][0] < start or located["offset_mapping"][i][1] > end for i in overlaps):
                    raise ValueError("Target span cuts a token; specify complete semantic text")
            with torch.inference_mode():
                hidden, padding, pooled = text_encoder.extract_text_features([prompt, ""])
            frozen = [digest(t) for t in (hidden, padding, pooled)]

            for seed in args.seeds:
                baseline_scales = None
                baseline_hash = None
                full_hash = None
                plan = [("reference", (), [], False)]
                for selected, aliases in schedules(len(PATCH_NUMS)):
                    tag = "baseline" if not selected else "full_mask" if len(selected) == len(PATCH_NUMS) else f"{aliases[0]['direction']}_{aliases[0]['boundary']:02d}"
                    plan.append((tag, selected, aliases, True))
                plan.append(("full_mask_repeat", tuple(range(1, len(PATCH_NUMS)+1)), [], True))
                for tag, selected, aliases, use_hooks in plan:
                    random.seed(seed)
                    np.random.seed(seed)
                    torch.manual_seed(seed)
                    torch.cuda.manual_seed_all(seed)
                    counts = [0] * len(model.blocks)
                    audit, scale_hashes, handles = [], [], []
                    def capture_next(si, sn, f_hat, h):
                        result = native_next(si, sn, f_hat, h)
                        scale_hashes.append(digest(result[0]))
                        return result
                    quantizer.get_next_autoregressive_input = capture_next
                    def make_pre(layer):
                        def pre(module, a, kw):
                            nonlocal active
                            counts[layer] += 1
                            scale = counts[layer]
                            if scale > len(PATCH_NUMS) or a[0].shape[1] != PATCH_NUMS[scale-1]**2:
                                raise RuntimeError("Scale/cross-attention call order mismatch")
                            bias = kw["attn_bias"]
                            expected = torch.where(padding == 1, 0., -torch.inf)[:, None, None, :]
                            if not torch.equal(bias, expected):
                                raise RuntimeError("Unexpected baseline padding mask")
                            modified = bias.clone()
                            masked = scale in selected
                            if masked:
                                modified[0, :, :, positions] = -torch.inf
                            # All other positions and the empty-text branch remain unchanged.
                            other = [i for i in range(bias.shape[-1]) if i not in positions]
                            if not torch.equal(modified[1], bias[1]) or not torch.equal(modified[0, :, :, other], bias[0, :, :, other]):
                                raise RuntimeError("Unintended mask modification")
                            kw["attn_bias"] = modified
                            active = dict(layer=layer, scale=scale, masked=masked,
                                          positions=positions, audit=audit, audit_weights=audit_weights)
                            return a, kw
                        return pre
                    def post(module, a, output):
                        nonlocal active
                        active = None
                    if use_hooks:
                        for layer, block in enumerate(model.blocks):
                            handles.append(block.cross_attn.register_forward_pre_hook(make_pre(layer), with_kwargs=True))
                            handles.append(block.cross_attn.register_forward_hook(post))
                    started = time.monotonic()
                    torch.cuda.reset_peak_memory_stats()
                    try:
                        with torch.inference_mode(), torch.autocast("cuda", dtype=torch.float16):
                            image = model.autoregressive_infer_cfg(
                                B=1, label_B=None, encoder_hidden_states=hidden,
                                encoder_attention_mask=padding, encoder_pool_feat=pooled,
                                g_seed=seed, cfg=args.cfg, top_k=args.top_k, top_p=args.top_p,
                                more_smooth=False, w_mask=False, sample_version="new")
                        torch.cuda.synchronize()
                    finally:
                        for handle in handles:
                            handle.remove()
                        active = None
                        quantizer.get_next_autoregressive_input = native_next
                        for block in model.blocks:
                            block.attn.kv_caching(False)
                    if not torch.isfinite(image).all() or len(scale_hashes) != len(PATCH_NUMS):
                        raise RuntimeError("Invalid image or scale trajectory")
                    if use_hooks and (counts != [len(PATCH_NUMS)]*len(model.blocks) or len(audit) != len(PATCH_NUMS)*len(model.blocks)):
                        raise RuntimeError("Incomplete mask audit")
                    if frozen != [digest(t) for t in (hidden, padding, pooled)]:
                        raise RuntimeError("Original text conditions mutated")
                    image_hash = digest(image)
                    if tag == "reference":
                        baseline_hash, baseline_scales = image_hash, scale_hashes
                    if tag == "baseline" and (image_hash != baseline_hash or scale_hashes != baseline_scales):
                        raise RuntimeError("No-op mask does not exactly reproduce reference")
                    prefix_length = min(selected)-1 if selected else len(PATCH_NUMS)
                    if scale_hashes[:prefix_length] != baseline_scales[:prefix_length]:
                        raise RuntimeError("Visual trajectory changed before intervention")
                    if tag == "full_mask":
                        full_hash = image_hash
                    if tag == "full_mask_repeat" and image_hash != full_hash:
                        raise RuntimeError("Full mask is not reproducible")
                    name = f"p{item_index:03d}_s{seed}_{tag}"
                    pixels = image[0].permute(1, 2, 0).float().cpu().clamp(0, 1).mul(255).byte().numpy()
                    Image.fromarray(pixels).save(args.output / f"{name}.png")
                    record = dict(name=name, input_id=item["id"], prompt=prompt, semantic=item["semantic"],
                                  spans=item["spans"], target_positions=positions,
                                  target_tokens=text_encoder.tokenizer.convert_ids_to_tokens([actual[i] for i in positions]),
                                  input_ids=actual, offsets=located["offset_mapping"],
                                  seed=seed, masked_scales=selected, aliases=aliases,
                                  condition_sha256=frozen, image_sha256=image_hash,
                                  scale_sha256=scale_hashes, unchanged_prefix_scales=prefix_length,
                                  attention_weight_audit=audit_weights, attention_audit=audit, elapsed_seconds=time.monotonic()-started,
                                  peak_cuda_allocated_bytes=torch.cuda.max_memory_allocated())
                    with (args.output / "runs.jsonl").open("a") as f:
                        f.write(json.dumps(record) + "\n")
                    all_records.append(record)
                    print(name, "PASS", flush=True)
    finally:
        basic.F.scaled_dot_product_attention = native_sdp
        quantizer.get_next_autoregressive_input = native_next
    (args.output / "summary.json").write_text(json.dumps(dict(
        status="passed", completed_runs=len(all_records),
        checks=["strict checkpoint load", "fast/slow tokenizer ID agreement", "all-layer mask audit",
                "zero masked target attention", "global and text features unchanged",
                "no-op matches unhooked reference", "pre-intervention visual prefix unchanged",
                "full-mask repeat matches"],
        note="Implementation verification only; no semantic metric or generalization conclusion."), indent=2))


if __name__ == "__main__":
    main()
