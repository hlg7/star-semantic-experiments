# CSFM 改写风格预览：六类各 5 条

加粗片段是未来 mask 目标。本次仅准备文本并检查 tokenizer，未生成图片。

这些是基于 caption 的改写，不是原图的人工标注；新增或修改的属性不能作为原图 ground truth。

## object

| ID | Prompt | 预期目标 |
|---|---|---|
| csfm_object_01 | A brown **dog** wearing a leather collar stands on a grassy field, with bare trees and a low stone wall in the background. | A dog is clearly present. |
| csfm_object_02 | A rusty brown **freight car** rests on railway tracks in a desert landscape, with dry shrubs nearby and distant mountains beneath a cloudy sky. | A freight car is clearly present. |
| csfm_object_03 | A white ceramic **mug** stands beside a silver coffee pot on a pink table, with empty chairs visible in the softly lit cafe behind them. | A mug is clearly present, distinct from the coffee pot. |
| csfm_object_04 | A yellow **water bottle** stands upright in a grassy field, with tall reeds and a distant line of trees beneath an overcast sky. | A water bottle is clearly present. |
| csfm_object_05 | A wooden **hourglass** stands beside a white coffee cup on a desk, with a computer monitor visible against the plain wall in the background. | An hourglass is clearly present, distinct from the cup. |

## color

| ID | Prompt | 预期目标 |
|---|---|---|
| csfm_color_01 | A **brown** dog wearing a leather collar stands on a grassy field, with bare trees and a low stone wall in the background. | The dog is brown. |
| csfm_color_02 | A **yellow** water bottle stands upright in a grassy field, with tall reeds and a distant line of trees beneath an overcast sky. | The water bottle is yellow. |
| csfm_color_03 | A **white** ceramic mug stands beside a silver coffee pot on a pink table, with empty chairs visible in the softly lit cafe behind them. | The mug is white. |
| csfm_color_04 | A gray hourglass containing **pink** sand rests on a white desk beside a closed notebook, with a plain wall behind it in soft daylight. | The sand inside the hourglass is pink. |
| csfm_color_05 | A **blue** toy car sits beside a silver coffee maker on a stone ledge, with both objects fully visible against a plain wall in daylight. | The toy car is blue. |

## shape

| ID | Prompt | 预期目标 |
|---|---|---|
| csfm_shape_01 | A white **rectangular** table stands in a quiet library, with wooden chairs nearby and bookshelves lining the walls beneath large windows that admit daylight. | The tabletop is rectangular. |
| csfm_shape_02 | A **round** badge rests beside a paintbrush on a dark cloth, with both objects clearly separated and viewed from above under soft indoor lighting. | The badge has a round outline. |
| csfm_shape_03 | An **oval** remote control rests beside a closed notebook on a tiled floor, with both objects clearly separated and viewed from directly above. | The remote control has an oval outline. |
| csfm_shape_04 | A stone sundial with a **triangular** upright fin stands on a concrete pedestal in a garden, with low shrubs behind it in daylight. | The upright fin has a triangular shape. |
| csfm_shape_05 | A wooden hourglass with a **square** base stands on a desk beside a closed book, with its lower frame clearly visible in soft daylight. | The hourglass base is square. |

## texture

| ID | Prompt | 预期目标 |
|---|---|---|
| csfm_texture_01 | A pair of **striped** socks lies on a dark wooden table beside a folded towel, with both items fully visible in soft window light. | The socks have a striped pattern. |
| csfm_texture_02 | A **checkered** cloth covers a kitchen table beneath a clear bag of cookies, with its uncovered surface visible in daylight from a nearby window. | The visible cloth has a checkered pattern. |
| csfm_texture_03 | A sundial hangs on a **rough** stone wall in a quiet garden, with the surrounding surface clearly visible beside a narrow path in daylight. | The stone wall has a visibly rough surface. |
| csfm_texture_04 | A ceramic mug with a **smooth** surface stands beside a metal coffee pot on a cafe table, with empty chairs in the background. | The mug has a visibly smooth surface. |
| csfm_texture_05 | A person wearing a **polka-dotted** sweater sits on a sofa holding a remote control, with a wooden side table nearby in a quiet living room. | The sweater has a polka-dot pattern. |

## count

| ID | Prompt | 预期目标 |
|---|---|---|
| csfm_count_01 | **Three** hourglasses stand in a row on a wooden shelf, each clearly separated from the others against a plain wall in soft daylight. | Exactly three hourglasses are present. |
| csfm_count_02 | **Two** glass measuring cups stand side by side on a wooden counter, with each fully visible against a plain kitchen wall in soft daylight. | Exactly two measuring cups are present. |
| csfm_count_03 | **Four** remote controls lie separately on a tiled floor beside a closed notebook, with every device fully visible in a view from above. | Exactly four remote controls are present. |
| csfm_count_04 | **Three** metal coffee pots stand in a row on a kitchen counter beside a ceramic cup, with all objects fully visible in daylight. | Exactly three coffee pots are present. |
| csfm_count_05 | **Two** orange fish swim in a glass aquarium above a gravel bed, with their bodies clearly separated and artificial plants lining the back. | Exactly two fish are present. |

## spatial_relation

| ID | Prompt | 预期目标 |
|---|---|---|
| csfm_spatial_relation_01 | A ceramic mug sits **to the left of** a metal coffee pot on a cafe table, with both objects fully visible from the front. | The mug is to the viewer's left of the coffee pot. |
| csfm_spatial_relation_02 | A ceramic mug sits **to the right of** a metal coffee pot on a cafe table, with both objects fully visible from the front. | The mug is to the viewer's right of the coffee pot. |
| csfm_spatial_relation_03 | A framed portrait hangs **above** a bookshelf in a quiet library, with both objects fully visible against a plain wall under soft indoor lighting. | The portrait is above the bookshelf. |
| csfm_spatial_relation_04 | A wooden hourglass stands **in front of** a coffee cup on a desk, with both objects visible from an angle in a softly lit room. | The hourglass is in front of the coffee cup. |
| csfm_spatial_relation_05 | A chocolate brownie rests **inside** a glass bowl on a wooden table, with the rim and dessert clearly visible against a plain kitchen background. | The brownie is inside the bowl. |

## 原始 caption 与改写记录

以下保留来源以便追溯；原图未检查。

### csfm_object_01
来源：`ILSVRC2012_val_00001434`，`n02099429/ILSVRC2012_val_00001434.JPEG`

A chocolate brown curly-coated dog with a weathered leather collar, standing in profile on a vibrant green grassy field, with a backdrop of bare trees and stone walls under soft daylight.

改写：简化毛发和姿态描述，保留项圈、草地及背景。

### csfm_object_02
来源：`ILSVRC2012_val_00002595`，`n03393912/ILSVRC2012_val_00002595.JPEG`

A rusty brown freight car sits abandoned on a dirt railway track in a vast desert landscape, with sparse dry brush and distant mountains under a bright blue sky with scattered white clouds.

改写：保留主体与沙漠环境，简化天空描述。

### csfm_object_03
来源：`ILSVRC2012_val_00002022`，`n03063689/ILSVRC2012_val_00002022.JPEG`

A white ceramic mug with a spoon inside, placed beside a reflective silver French press coffee pot with a floral pattern at its base, both resting on a glossy pink tabletop. In the background, a dimly lit café interior with warm ambient lighting, blurred patrons, and a poster with the text "AMBASSADORS" visible on the wall.

改写：删除勺子、花纹和招牌文字，将背景顾客改为空椅子。

### csfm_object_04
来源：`ILSVRC2012_val_00003429`，`n04557648/ILSVRC2012_val_00003429.JPEG`

A yellow water bottle with a black and yellow cap, featuring a printed map of Minnesota on its side, stands upright in a grassy field. The background shows a wide expanse of green grass, a line of tall reeds, and a distant treeline under an overcast sky.

改写：删除地图印花及重复颜色描述，保留场景。

### csfm_object_05
来源：`ILSVRC2012_val_00003951`，`n03544143/ILSVRC2012_val_00003951.JPEG`

A wooden hourglass with dark brown finish and ornate turned legs, mounted on a circular base, sits on a white desk next to a white disposable coffee cup with a cartoon face and a white lid. Behind them, a computer monitor with a bright white screen is partially visible, and a poster featuring a stylized armored figure with glowing green light in the background is affixed to the wall. A yellow sticky note is attached to the right edge of the frame.

改写：删除装饰、海报及便签，简化场景。

### csfm_color_01
来源：`ILSVRC2012_val_00001434`，`n02099429/ILSVRC2012_val_00001434.JPEG`

A chocolate brown curly-coated dog with a weathered leather collar, standing in profile on a vibrant green grassy field, with a backdrop of bare trees and stone walls under soft daylight.

改写：与 object_01 共用完整 prompt，仅目标不同。

### csfm_color_02
来源：`ILSVRC2012_val_00003429`，`n04557648/ILSVRC2012_val_00003429.JPEG`

A yellow water bottle with a black and yellow cap, featuring a printed map of Minnesota on its side, stands upright in a grassy field. The background shows a wide expanse of green grass, a line of tall reeds, and a distant treeline under an overcast sky.

改写：与 object_04 共用完整 prompt，仅目标不同。

### csfm_color_03
来源：`ILSVRC2012_val_00002022`，`n03063689/ILSVRC2012_val_00002022.JPEG`

A white ceramic mug with a spoon inside, placed beside a reflective silver French press coffee pot with a floral pattern at its base, both resting on a glossy pink tabletop. In the background, a dimly lit café interior with warm ambient lighting, blurred patrons, and a poster with the text "AMBASSADORS" visible on the wall.

改写：与 object_03 共用完整 prompt，仅目标不同。

### csfm_color_04
来源：`ILSVRC2012_val_00004082`，`n03544143/ILSVRC2012_val_00004082.JPEG`

A gray hourglass with a pink sand base, surrounded by scattered pink and black paper clips on a white surface.

改写：删除同色回形针，增加中性笔记本与背景，目标是沙子颜色。

### csfm_color_05
来源：`ILSVRC2012_val_00007862`，`n03063689/ILSVRC2012_val_00007862.JPEG`

A blue toy Volkswagen Beetle with chrome wheels sits beside two metal espresso makers on a stone ledge; one has a black-and-white cow print pattern, the other is polished stainless steel, both with black handles and domed knobs, under warm ambient lighting with a blurred background.

改写：简化品牌与车型，将两台咖啡机改为一台，删除图案。

### csfm_shape_01
来源：`ILSVRC2012_val_00000849`，`n03661043/ILSVRC2012_val_00000849.JPEG`

Rows of tall, light-colored bookshelves filled with books line the walls of a quiet library, featuring large windows with wooden frames letting in natural light, several white rectangular tables with matching chairs arranged in clusters, and overhead fluorescent lighting fixtures illuminating the beige carpeted floor.

改写：将多张桌子集中为一张，保留图书馆和椅子。

### csfm_shape_02
来源：`ILSVRC2012_val_00004509`，`n03871628/ILSVRC2012_val_00004509.JPEG`

A circular badge with a green and white striped background, featuring a black-and-white illustration of a bird perched on a branch, holding a speech bubble, enclosed in clear plastic packaging with a brown paper tag reading "mirror" in green cursive script, resting on a black fabric item alongside a paintbrush with a green handle.

改写：circular 改写为 round，删除图案、包装与文字，增加俯视视角。

### csfm_shape_03
来源：`ILSVRC2012_val_00002910`，`n04074963/ILSVRC2012_val_00002910.JPEG`

Four black remote controls arranged in a diamond pattern on a light beige tiled floor with dark grout lines; one central oval-shaped remote with a glossy finish and the brand name "SAMSUNG" visible, flanked by three rectangular remotes with various button layouts and some showing "SAMSUNG" branding; all remotes are positioned diagonally pointing inward toward the center.

改写：从多只遥控器中提取目标，参照物改为笔记本，删除品牌并增加俯视。

### csfm_shape_04
来源：`ILSVRC2012_val_00004847`，`n04355338/ILSVRC2012_val_00004847.JPEG`

A weathered stone sundial with a triangular gnomon casting a shadow, featuring engraved hour markers and decorative carvings, set outdoors on a concrete base surrounded by green foliage.

改写：将 gnomon 通俗改写为 upright fin，简化刻字、雕饰及植被。

### csfm_shape_05
来源：`ILSVRC2012_val_00007277`，`n03544143/ILSVRC2012_val_00007277.JPEG`

A wooden hourglass with a polished brown finish, featuring a round top and base connected by four turned spindles, containing clear glass bulbs with light-colored sand flowing between them, set against a plain gradient background.

改写：将原始 round base 改为 square，增加书和桌面；属于属性修改，不代表原图。

### csfm_texture_01
来源：`ILSVRC2012_val_00007953`，`n04254777/ILSVRC2012_val_00007953.JPEG`

A pair of hand-knitted socks with vibrant horizontal stripes in blue, pink, orange, and teal, resting on a dark wooden surface with visible grain and a light-colored wooden board partially underneath.

改写：保留条纹袜子与木面，删除逐色列举，增加毛巾。

### csfm_texture_02
来源：`ILSVRC2012_val_00002169`，`n03871628/ILSVRC2012_val_00002169.JPEG`

Several chocolate chip cookies in clear plastic bags with yellow floral patterns, resting on a red, white, and blue plaid fabric.

改写：plaid 改写为 checkered，删除包装花纹与颜色列举，增加可见桌布区域。

### csfm_texture_03
来源：`ILSVRC2012_val_00002136`，`n04355338/ILSVRC2012_val_00002136.JPEG`

An octagonal sundial mounted on a rough stone wall, featuring golden Roman numerals I through XII, the year "1732" inscribed in the center, and the name "ROSS WILLIAMS" arched above a sunburst design, with a gnomon casting a sharp shadow across the dial.

改写：保留石墙质感，删除数字和人名，增加花园及小路背景。

### csfm_texture_04
来源：`ILSVRC2012_val_00002022`，`n03063689/ILSVRC2012_val_00002022.JPEG`

A white ceramic mug with a spoon inside, placed beside a reflective silver French press coffee pot with a floral pattern at its base, both resting on a glossy pink tabletop. In the background, a dimly lit café interior with warm ambient lighting, blurred patrons, and a poster with the text "AMBASSADORS" visible on the wall.

改写：明确添加 smooth 属性，简化颜色、装饰和背景。

### csfm_texture_05
来源：`ILSVRC2012_val_00000275`，`n04074963/ILSVRC2012_val_00000275.JPEG`

A person wearing a green and white striped sweater bent over, holding two remote controls, one gray and one silver, in a living room with wooden floors, a beige couch, a dark blue couch with a green pillow, and a small wooden side table.

改写：将 striped 改为 polka-dotted，改为坐姿和一只遥控器；属于属性修改。

### csfm_count_01
来源：`ILSVRC2012_val_00003986`，`n03544143/ILSVRC2012_val_00003986.JPEG`

Three hourglasses arranged in a row, each with glass bulbs connected by a narrow neck, containing sand that has partially flowed from the upper to the lower bulb, set against a dark background with warm sepia-toned lighting, and a signature in the bottom right corner reading "Patricia '09".

改写：保留精确数量，删除签名和重复部件描述，增加木架与清楚分隔。

### csfm_count_02
来源：`ILSVRC2012_val_00001912`，`n02815834/ILSVRC2012_val_00001912.JPEG`

Two clear glass measuring cups, one in foreground with embossed text "WESTERN MAN KODAK" and "ROCHESTER, N.Y.", the other slightly blurred in background, both resting on a light-colored wooden surface with soft, even lighting.

改写：删除文字与前后虚焦，改为并排清晰呈现。

### csfm_count_03
来源：`ILSVRC2012_val_00002910`，`n04074963/ILSVRC2012_val_00002910.JPEG`

Four black remote controls arranged in a diamond pattern on a light beige tiled floor with dark grout lines; one central oval-shaped remote with a glossy finish and the brand name "SAMSUNG" visible, flanked by three rectangular remotes with various button layouts and some showing "SAMSUNG" branding; all remotes are positioned diagonally pointing inward toward the center.

改写：保留数量，删除品牌、形状及复杂排列，增加笔记本。

### csfm_count_04
来源：`ILSVRC2012_val_00002078`，`n03063689/ILSVRC2012_val_00002078.JPEG`

Three vintage aluminum Moka pots arranged in a row, featuring hexagonal bodies, domed lids with black handles, and spouts, captured in black and white with shallow depth of field, highlighting metallic textures and reflections against a softly blurred background.

改写：保留数量，简化为常见物体名称，增加杯子并删除黑白摄影描述。

### csfm_count_05
来源：`ILSVRC2012_val_00000994`，`n01443537/ILSVRC2012_val_00000994.JPEG`

A vibrant orange fish with flowing fins and a large, round eye, swimming in an aquarium with blurred green plants and colorful background decor.

改写：将原始单条鱼改为两条，保留水族箱并添加分隔和底部环境。

### csfm_spatial_relation_01
来源：`ILSVRC2012_val_00002022`，`n03063689/ILSVRC2012_val_00002022.JPEG`

A white ceramic mug with a spoon inside, placed beside a reflective silver French press coffee pot with a floral pattern at its base, both resting on a glossy pink tabletop. In the background, a dimly lit café interior with warm ambient lighting, blurred patrons, and a poster with the text "AMBASSADORS" visible on the wall.

改写：将 beside 明确为观察者左侧，删除无关细节并明确正面视角。

### csfm_spatial_relation_02
来源：`ILSVRC2012_val_00002022`，`n03063689/ILSVRC2012_val_00002022.JPEG`

A white ceramic mug with a spoon inside, placed beside a reflective silver French press coffee pot with a floral pattern at its base, both resting on a glossy pink tabletop. In the background, a dimly lit café interior with warm ambient lighting, blurred patrons, and a poster with the text "AMBASSADORS" visible on the wall.

改写：与上一条构成反向关系对，仅替换 left/right。

### csfm_spatial_relation_03
来源：`ILSVRC2012_val_00000715`，`n03661043/ILSVRC2012_val_00000715.JPEG`

Two framed portraits of men in red cardinal attire hang above a row of bookshelves filled with aged, leather-bound books. The portraits are set against an ornate, cream-colored ceiling with decorative moldings and sculpted elements. The bookshelves are made of light-colored wood with white-painted dividers, and the books show varied spine designs and colors, including gold, brown, and faded red.

改写：将多幅画像及书架简化为各一个，保留明确上下关系。

### csfm_spatial_relation_04
来源：`ILSVRC2012_val_00003951`，`n03544143/ILSVRC2012_val_00003951.JPEG`

A wooden hourglass with dark brown finish and ornate turned legs, mounted on a circular base, sits on a white desk next to a white disposable coffee cup with a cartoon face and a white lid. Behind them, a computer monitor with a bright white screen is partially visible, and a poster featuring a stylized armored figure with glowing green light in the background is affixed to the wall. A yellow sticky note is attached to the right edge of the frame.

改写：将 next to 改为 in front of，去除电脑和其他装饰，保留可见性。

### csfm_spatial_relation_05
来源：`ILSVRC2012_val_00001483`，`n07836838/ILSVRC2012_val_00001483.JPEG`

A scoop of vanilla ice cream with dark chocolate sauce drizzled over it, resting atop a chocolate brownie in a clear glass bowl, placed on a wooden surface.

改写：保留容纳关系，删除冰淇淋和酱料，明确碗沿与甜点可见。
