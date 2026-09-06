# 六类 semantic 试验 prompt v1

手工构造，用于 baseline 能力和 token 定位检查；不是正式 benchmark，也未经生成结果筛选。
加粗部分是唯一 mask 目标。预期描述用于人工核对，尚未指定 metric。

## object

| ID | Prompt（加粗为 mask 目标） | 子类 | 对象配置 | 预期 |
|---|---|---|---|---|
| object_01 | A red **car**. | identity | single_object | A car is present. |
| object_02 | A blue **backpack**. | identity | single_object | A backpack is present. |
| object_03 | A green **chair**. | identity | single_object | A chair is present. |
| object_04 | A yellow **umbrella**. | identity | single_object | An umbrella is present. |
| object_05 | A purple **vase**. | identity | single_object | A vase is present. |
| object_06 | A **cat** beside a bicycle. | identity | multiple_objects | A cat is present, alongside the bicycle. |
| object_07 | A **bicycle** beside a bench. | identity | multiple_objects | A bicycle is present, alongside the bench. |
| object_08 | A blue **cup** beside a white bowl. | identity | multiple_objects | A cup is present, alongside the bowl. |
| object_09 | A **book** beside a lamp. | identity | multiple_objects | A book is present, alongside the lamp. |
| object_10 | A **dog** beside a suitcase. | identity | multiple_objects | A dog is present, alongside the suitcase. |

## color

| ID | Prompt（加粗为 mask 目标） | 子类 | 对象配置 | 预期 |
|---|---|---|---|---|
| color_01 | A **red** car. | color | single_object | The car is red. |
| color_02 | A **blue** backpack. | color | single_object | The backpack is blue. |
| color_03 | A **green** chair. | color | single_object | The chair is green. |
| color_04 | A **yellow** umbrella. | color | single_object | The umbrella is yellow. |
| color_05 | A **purple** vase. | color | single_object | The vase is purple. |
| color_06 | A **red** backpack beside a blue suitcase. | color_binding | multiple_objects | The backpack is red; the suitcase is blue. |
| color_07 | A **blue** cup beside a white bowl. | color_binding | multiple_objects | The cup is blue; the bowl is white. |
| color_08 | A **green** car beside a yellow bicycle. | color_binding | multiple_objects | The car is green; the bicycle is yellow. |
| color_09 | A **yellow** vase beside a purple lamp. | color_binding | multiple_objects | The vase is yellow; the lamp is purple. |
| color_10 | A **purple** chair beside a red table. | color_binding | multiple_objects | The chair is purple; the table is red. |

## shape

| ID | Prompt（加粗为 mask 目标） | 子类 | 对象配置 | 预期 |
|---|---|---|---|---|
| shape_01 | A **square** plate. | outline | single_object | The plate has a square outline. |
| shape_02 | A **round** mirror. | outline | single_object | The mirror has a round outline. |
| shape_03 | A **triangular** sign. | outline | single_object | The sign has a triangular outline. |
| shape_04 | An **oval** rug. | outline | single_object | The rug has an oval outline. |
| shape_05 | A **rectangular** table. | outline | single_object | The tabletop has a rectangular outline. |
| shape_06 | A **square** mirror beside a round clock. | shape_binding | multiple_objects | The mirror is square; the clock is round. |
| shape_07 | A **round** plate beside a square tray. | shape_binding | multiple_objects | The plate is round; the tray is square. |
| shape_08 | A **triangular** flag beside a rectangular sign. | shape_binding | multiple_objects | The flag is triangular; the sign is rectangular. |
| shape_09 | An **oval** tray beside a round bowl. | shape_binding | multiple_objects | The tray has an oval outline; the bowl is round. |
| shape_10 | A **rectangular** rug beside a round stool. | shape_binding | multiple_objects | The rug has a rectangular outline; the stool is round. |

## texture

| ID | Prompt（加粗为 mask 目标） | 子类 | 对象配置 | 预期 |
|---|---|---|---|---|
| texture_01 | A **striped** shirt. | pattern | single_object | The shirt has a striped pattern. |
| texture_02 | A **checkered** blanket. | pattern | single_object | The blanket has a checkered pattern. |
| texture_03 | A **polka-dotted** umbrella. | pattern | single_object | The umbrella has a polka-dot pattern. |
| texture_04 | A **rough** stone. | surface | single_object | The stone has a visibly rough surface. |
| texture_05 | A **smooth** vase. | surface | single_object | The vase has a visibly smooth surface. |
| texture_06 | A **striped** blanket beside a checkered pillow. | pattern_binding | multiple_objects | The blanket is striped; the pillow is checkered. |
| texture_07 | A **checkered** shirt beside a striped scarf. | pattern_binding | multiple_objects | The shirt is checkered; the scarf is striped. |
| texture_08 | A **polka-dotted** bag beside a striped hat. | pattern_binding | multiple_objects | The bag has polka dots; the hat is striped. |
| texture_09 | A **rough** vase beside a smooth bowl. | surface_binding | multiple_objects | The vase has a rough surface; the bowl has a smooth surface. |
| texture_10 | A **smooth** stone beside a rough brick. | surface_binding | multiple_objects | The stone has a smooth surface; the brick has a rough surface. |

## count

| ID | Prompt（加粗为 mask 目标） | 子类 | 对象配置 | 预期 |
|---|---|---|---|---|
| count_01 | **Two** cups. | single_category | multiple_objects | Exactly two cups are present. |
| count_02 | **Three** bottles. | single_category | multiple_objects | Exactly three bottles are present. |
| count_03 | **Four** apples. | single_category | multiple_objects | Exactly four apples are present. |
| count_04 | **Two** dogs. | single_category | multiple_objects | Exactly two dogs are present. |
| count_05 | **Three** chairs. | single_category | multiple_objects | Exactly three chairs are present. |
| count_06 | **Two** bottles beside one bowl. | count_binding | multiple_objects | Exactly two bottles and one bowl are present. |
| count_07 | **Three** cups beside one plate. | count_binding | multiple_objects | Exactly three cups and one plate are present. |
| count_08 | **Four** oranges beside one apple. | count_binding | multiple_objects | Exactly four oranges and one apple are present. |
| count_09 | **Two** cats beside one dog. | count_binding | multiple_objects | Exactly two cats and one dog are present. |
| count_10 | **Three** books beside one lamp. | count_binding | multiple_objects | Exactly three books and one lamp are present. |

## spatial_relation

| ID | Prompt（加粗为 mask 目标） | 子类 | 对象配置 | 预期 |
|---|---|---|---|---|
| spatial_relation_01 | A cup **to the left of** a bowl. | left_right | multiple_objects | The cup is to the viewer's left of the bowl; both are present. |
| spatial_relation_02 | A cup **to the right of** a bowl. | left_right | multiple_objects | The cup is to the viewer's right of the bowl; both are present. |
| spatial_relation_03 | A bicycle **to the left of** a bench. | left_right | multiple_objects | The bicycle is to the viewer's left of the bench; both are present. |
| spatial_relation_04 | A bicycle **to the right of** a bench. | left_right | multiple_objects | The bicycle is to the viewer's right of the bench; both are present. |
| spatial_relation_05 | A balloon **above** a box. | above_below | multiple_objects | The balloon is above the box; both are present. |
| spatial_relation_06 | A balloon **below** a box. | above_below | multiple_objects | The balloon is below the box; both are present. |
| spatial_relation_07 | A cat **in front of** a suitcase. | front_behind | multiple_objects | The cat is in front of the suitcase; both are present. |
| spatial_relation_08 | A cat **behind** a suitcase. | front_behind | multiple_objects | The cat is behind the suitcase; both are present. |
| spatial_relation_09 | A ball **inside** a basket. | containment | multiple_objects | The ball is inside the basket; both are present. |
| spatial_relation_10 | A ball **outside** a basket. | containment | multiple_objects | The ball is outside the basket; both are present. |

60 个干预样本，54 条不同 prompt。相同 prompt 共用 prompt_id，可复用 baseline；各干预目标分别保存。
