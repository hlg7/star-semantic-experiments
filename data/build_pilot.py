"""Export the hand-authored pilot. Brackets mark only the intervention text."""
import json
from pathlib import Path

# Rows: marked prompt, target object, subtype, composition, expected target fact.
# These are hand-written examples, not sampled from a benchmark or selected on outputs.
ROWS = {
    "object": [
        ("A red [car].", "car", "identity", "single_object", "A car is present."),
        ("A blue [backpack].", "backpack", "identity", "single_object", "A backpack is present."),
        ("A green [chair].", "chair", "identity", "single_object", "A chair is present."),
        ("A yellow [umbrella].", "umbrella", "identity", "single_object", "An umbrella is present."),
        ("A purple [vase].", "vase", "identity", "single_object", "A vase is present."),
        ("A [cat] beside a bicycle.", "cat", "identity", "multiple_objects", "A cat is present, alongside the bicycle."),
        ("A [bicycle] beside a bench.", "bicycle", "identity", "multiple_objects", "A bicycle is present, alongside the bench."),
        ("A blue [cup] beside a white bowl.", "cup", "identity", "multiple_objects", "A cup is present, alongside the bowl."),
        ("A [book] beside a lamp.", "book", "identity", "multiple_objects", "A book is present, alongside the lamp."),
        ("A [dog] beside a suitcase.", "dog", "identity", "multiple_objects", "A dog is present, alongside the suitcase."),
    ],
    "color": [
        ("A [red] car.", "car", "color", "single_object", "The car is red."),
        ("A [blue] backpack.", "backpack", "color", "single_object", "The backpack is blue."),
        ("A [green] chair.", "chair", "color", "single_object", "The chair is green."),
        ("A [yellow] umbrella.", "umbrella", "color", "single_object", "The umbrella is yellow."),
        ("A [purple] vase.", "vase", "color", "single_object", "The vase is purple."),
        ("A [red] backpack beside a blue suitcase.", "backpack", "color_binding", "multiple_objects", "The backpack is red; the suitcase is blue."),
        ("A [blue] cup beside a white bowl.", "cup", "color_binding", "multiple_objects", "The cup is blue; the bowl is white."),
        ("A [green] car beside a yellow bicycle.", "car", "color_binding", "multiple_objects", "The car is green; the bicycle is yellow."),
        ("A [yellow] vase beside a purple lamp.", "vase", "color_binding", "multiple_objects", "The vase is yellow; the lamp is purple."),
        ("A [purple] chair beside a red table.", "chair", "color_binding", "multiple_objects", "The chair is purple; the table is red."),
    ],
    "shape": [
        ("A [square] plate.", "plate", "outline", "single_object", "The plate has a square outline."),
        ("A [round] mirror.", "mirror", "outline", "single_object", "The mirror has a round outline."),
        ("A [triangular] sign.", "sign", "outline", "single_object", "The sign has a triangular outline."),
        ("An [oval] rug.", "rug", "outline", "single_object", "The rug has an oval outline."),
        ("A [rectangular] table.", "table", "outline", "single_object", "The tabletop has a rectangular outline."),
        ("A [square] mirror beside a round clock.", "mirror", "shape_binding", "multiple_objects", "The mirror is square; the clock is round."),
        ("A [round] plate beside a square tray.", "plate", "shape_binding", "multiple_objects", "The plate is round; the tray is square."),
        ("A [triangular] flag beside a rectangular sign.", "flag", "shape_binding", "multiple_objects", "The flag is triangular; the sign is rectangular."),
        ("An [oval] tray beside a round bowl.", "tray", "shape_binding", "multiple_objects", "The tray has an oval outline; the bowl is round."),
        ("A [rectangular] rug beside a round stool.", "rug", "shape_binding", "multiple_objects", "The rug has a rectangular outline; the stool is round."),
    ],
    "texture": [
        ("A [striped] shirt.", "shirt", "pattern", "single_object", "The shirt has a striped pattern."),
        ("A [checkered] blanket.", "blanket", "pattern", "single_object", "The blanket has a checkered pattern."),
        ("A [polka-dotted] umbrella.", "umbrella", "pattern", "single_object", "The umbrella has a polka-dot pattern."),
        ("A [rough] stone.", "stone", "surface", "single_object", "The stone has a visibly rough surface."),
        ("A [smooth] vase.", "vase", "surface", "single_object", "The vase has a visibly smooth surface."),
        ("A [striped] blanket beside a checkered pillow.", "blanket", "pattern_binding", "multiple_objects", "The blanket is striped; the pillow is checkered."),
        ("A [checkered] shirt beside a striped scarf.", "shirt", "pattern_binding", "multiple_objects", "The shirt is checkered; the scarf is striped."),
        ("A [polka-dotted] bag beside a striped hat.", "bag", "pattern_binding", "multiple_objects", "The bag has polka dots; the hat is striped."),
        ("A [rough] vase beside a smooth bowl.", "vase", "surface_binding", "multiple_objects", "The vase has a rough surface; the bowl has a smooth surface."),
        ("A [smooth] stone beside a rough brick.", "stone", "surface_binding", "multiple_objects", "The stone has a smooth surface; the brick has a rough surface."),
    ],
    "count": [
        ("[Two] cups.", "cups", "single_category", "multiple_objects", "Exactly two cups are present."),
        ("[Three] bottles.", "bottles", "single_category", "multiple_objects", "Exactly three bottles are present."),
        ("[Four] apples.", "apples", "single_category", "multiple_objects", "Exactly four apples are present."),
        ("[Two] dogs.", "dogs", "single_category", "multiple_objects", "Exactly two dogs are present."),
        ("[Three] chairs.", "chairs", "single_category", "multiple_objects", "Exactly three chairs are present."),
        ("[Two] bottles beside one bowl.", "bottles", "count_binding", "multiple_objects", "Exactly two bottles and one bowl are present."),
        ("[Three] cups beside one plate.", "cups", "count_binding", "multiple_objects", "Exactly three cups and one plate are present."),
        ("[Four] oranges beside one apple.", "oranges", "count_binding", "multiple_objects", "Exactly four oranges and one apple are present."),
        ("[Two] cats beside one dog.", "cats", "count_binding", "multiple_objects", "Exactly two cats and one dog are present."),
        ("[Three] books beside one lamp.", "books", "count_binding", "multiple_objects", "Exactly three books and one lamp are present."),
    ],
    "spatial_relation": [
        ("A cup [to the left of] a bowl.", "cup", "left_right", "multiple_objects", "The cup is to the viewer's left of the bowl; both are present."),
        ("A cup [to the right of] a bowl.", "cup", "left_right", "multiple_objects", "The cup is to the viewer's right of the bowl; both are present."),
        ("A bicycle [to the left of] a bench.", "bicycle", "left_right", "multiple_objects", "The bicycle is to the viewer's left of the bench; both are present."),
        ("A bicycle [to the right of] a bench.", "bicycle", "left_right", "multiple_objects", "The bicycle is to the viewer's right of the bench; both are present."),
        ("A balloon [above] a box.", "balloon", "above_below", "multiple_objects", "The balloon is above the box; both are present."),
        ("A balloon [below] a box.", "balloon", "above_below", "multiple_objects", "The balloon is below the box; both are present."),
        ("A cat [in front of] a suitcase.", "cat", "front_behind", "multiple_objects", "The cat is in front of the suitcase; both are present."),
        ("A cat [behind] a suitcase.", "cat", "front_behind", "multiple_objects", "The cat is behind the suitcase; both are present."),
        ("A ball [inside] a basket.", "ball", "containment", "multiple_objects", "The ball is inside the basket; both are present."),
        ("A ball [outside] a basket.", "ball", "containment", "multiple_objects", "The ball is outside the basket; both are present."),
    ],
}


def main():
    output = Path(__file__).parent
    records, prompt_ids, review = [], {}, [
        "# 六类 semantic 试验 prompt v1", "",
        "手工构造，用于 baseline 能力和 token 定位检查；不是正式 benchmark，也未经生成结果筛选。",
        "加粗部分是唯一 mask 目标。预期描述用于人工核对，尚未指定 metric。", "",
    ]
    for semantic, rows in ROWS.items():
        assert len(rows) == 10
        review += [f"## {semantic}", "", "| ID | Prompt（加粗为 mask 目标） | 子类 | 对象配置 | 预期 |",
                   "|---|---|---|---|---|"]
        for index, (marked, target_object, subtype, composition, expected) in enumerate(rows, 1):
            assert marked.count("[") == marked.count("]") == 1
            start, stop = marked.index("["), marked.index("]")
            target = marked[start+1:stop]
            prompt = marked.replace("[", "").replace("]", "")
            end = start + len(target)
            assert prompt[start:end] == target
            if prompt not in prompt_ids:
                prompt_ids[prompt] = f"prompt_{len(prompt_ids)+1:03d}"
            record = dict(id=f"{semantic}_{index:02d}", prompt_id=prompt_ids[prompt],
                          prompt=prompt, semantic=semantic, spans=[[start, end]],
                          target_text=target, target_object=target_object, subtype=subtype,
                          composition=composition, expected=expected,
                          baseline_status="not_evaluated")
            records.append(record)
            shown = marked.replace("[", "**").replace("]", "**")
            review.append(f"| {record['id']} | {shown} | {subtype} | {composition} | {expected} |")
        review.append("")
    (output / "pilot_v1.json").write_text(json.dumps(records, ensure_ascii=False, indent=2)+"\n")
    (output / "pilot_v1_baseline_prompts.json").write_text(json.dumps(list(prompt_ids), indent=2)+"\n")
    review += [f"60 个干预样本，{len(prompt_ids)} 条不同 prompt。相同 prompt 共用 prompt_id，可复用 baseline；各干预目标分别保存。", ""]
    (output / "pilot_v1_review.md").write_text("\n".join(review))
    print(f"Exported {len(records)} targets, {len(prompt_ids)} unique prompts")


if __name__ == "__main__":
    main()
