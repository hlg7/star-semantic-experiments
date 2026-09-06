"""Check hand-marked spans against STAR's tokenizer without loading a model."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from transformers import CLIPTokenizer, CLIPTokenizerFast


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--tokenizer", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    slow = CLIPTokenizer.from_pretrained(str(args.tokenizer), local_files_only=True)
    fast = CLIPTokenizerFast.from_pretrained(str(args.tokenizer), local_files_only=True)
    raw = args.input.read_bytes()
    items = json.loads(raw)
    seen, records = set(), []
    for item in items:
        identity, prompt = item["id"], item["prompt"]
        if identity in seen:
            raise ValueError(f"Duplicate ID: {identity}")
        seen.add(identity)
        actual = slow(prompt, truncation=False)["input_ids"]
        located = fast(prompt, truncation=False, return_offsets_mapping=True)
        if actual != located["input_ids"] or len(actual) > slow.model_max_length:
            raise ValueError(f"Tokenizer mismatch or context overflow: {identity}")
        positions = set()
        for start, end in item["spans"]:
            if not 0 <= start < end <= len(prompt):
                raise ValueError(f"Invalid span: {identity}")
            matched = []
            for index, (a, b) in enumerate(located["offset_mapping"]):
                if a < b and a < end and b > start:
                    if a < start or b > end:
                        raise ValueError(f"Partial token span: {identity}")
                    matched.append(index)
            if not matched:
                raise ValueError(f"Empty target: {identity}")
            positions.update(matched)
        target = " ".join(prompt[a:b] for a, b in item["spans"])
        if target != item["target_text"]:
            raise ValueError(f"Target text mismatch: {identity}")
        positions = sorted(positions)
        records.append(dict(id=identity, target_text=target, positions=positions,
                            tokens=slow.convert_ids_to_tokens([actual[i] for i in positions]),
                            input_ids=actual, offsets=located["offset_mapping"],
                            sequence_length=len(actual)))
    report = dict(input_sha256=hashlib.sha256(raw).hexdigest(),
                  samples=len(items), unique_prompts=len({x["prompt"] for x in items}),
                  semantic_counts=dict(Counter(x["semantic"] for x in items)),
                  max_sequence_length=max(x["sequence_length"] for x in records),
                  model_max_length=slow.model_max_length,
                  all_tokenizer_ids_match=True, all_spans_valid=True, records=records)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps({k: v for k, v in report.items() if k != "records"}, indent=2))


if __name__ == "__main__":
    main()
