"""Controlled, hand-specified prompts inspired by recorded CSFM scene captions."""
import json
from pathlib import Path
P=Path(__file__).parent
pool=json.loads((P/'source_pool.json').read_text())
# Ten source-inspired scene families. Object substitutions are deliberate synthesis.
contexts=[
(10,'in a grassy garden, with a low stone wall and distant trees visible under soft daylight.'),
(56,'on a wooden cafe table, with empty chairs and a softly lit window visible in the background.'),
(66,'in a quiet library, with bookshelves along the walls and daylight entering through a large window.'),
(89,'beside a garden path, with tall reeds and distant trees beneath a lightly clouded sky.'),
(78,'on a tiled floor, with a plain wall behind the scene and soft light entering from a window.'),
(31,'on an office desk, with a dark computer monitor and a plain wall visible in the background.'),
(42,'on a wooden worktable, with a folded cloth nearby and soft daylight coming through a window.'),
(92,'on a kitchen counter, with a plain tiled wall and a closed cabinet visible in the background.'),
(64,'beside a desert road, with dry shrubs nearby and distant mountains under a pale cloudy sky.'),
(81,'in a quiet courtyard, with a stone wall and a narrow path visible in soft daylight.')]
# Context indices chosen for physical plausibility, not assigned at random.
objects=[
('dog',0),('cat',0),('bicycle',0),('bench',0),('wheelbarrow',0),
('mug',1),('teapot',1),('coffee pot',1),('sugar bowl',1),('tray',1),
('chair',2),('table',2),('bookcase',2),('ladder',2),('reading lamp',2),
('water bottle',3),('backpack',3),('umbrella',3),('watering can',3),('basket',3),
('remote control',4),('suitcase',4),('shoe',4),('helmet',4),('toy car',4),
('hourglass',5),('notebook',5),('stapler',5),('pencil case',5),('calculator',5),
('scarf',6),('hat',6),('shirt',6),('glove',6),('handbag',6),
('plate',7),('bowl',7),('glass jar',7),('kettle',7),('bread loaf',7),
('car',8),('truck',8),('motorcycle',8),('road sign',8),('barrel',8),
('vase',9),('flowerpot',9),('statue',9),('fountain',9),('stool',9)]
rows=[]
def add(sem,subject,target,obj,sub,c,expected,change,extra=''):
    # subject has literal target marked once; location comes from a documented family.
    idx,ctx=contexts[c]
    if sem == 'count' and obj == 'books':
        ctx='on a library reading table, with a plain wall and a closed storage cabinet visible in soft daylight.'
    marked=subject+' '+ctx
    if extra: marked=subject+' '+extra+' '+ctx
    a=marked.index('[');b=marked.index(']');t=marked[a+1:b]
    assert t==target and marked.count('[')==marked.count(']')==1
    prompt=marked.replace('[','').replace(']','')
    n=sum(x['semantic']==sem for x in rows)+1
    src=pool[idx]
    rows.append(dict(id=f'{sem}_{n:03d}',prompt=prompt,semantic=sem,spans=[[a,a+len(t)]],target_text=t,target_object=obj,subtype=sub,scene_family=f'scene_{c:02d}',expected=expected,baseline_status='not_evaluated',source=dict(dataset='junwann/CSFM-ImageNet1K-Caption',split='validation',id=src['id'],path=src['path']),adaptation_notes=change,word_count=len(prompt.split())))
def article(noun):return 'An' if noun[0].lower() in 'aeiou' else 'A'
for obj,c in objects:
    add('object',f'{article(obj)} [{obj}] is clearly visible',obj,obj,'identity',c,f'A {obj} is present.','保留来源场景，人工替换主体；不是原始图片标注。')
colors=['red','blue','green','yellow','purple','orange','pink','white','black','brown']
# Ten hues x five different subjects; reuse object scenes and retain clear attribute binding.
for i,(obj,c) in enumerate(objects):
    color=colors[(i%5)*2+i//25]
    add('color',f'{article(color)} [{color}] {obj} is clearly visible',color,obj,'color',c,f'The {obj} is {color}.','基于场景人工指定主体及颜色。')
shape_objects=[('plate',7),('mirror',9),('tray',1),('rug',2),('picture frame',5),('tabletop',2),('cushion',4),('wall clock',2),('sign',9),('floor mat',4)]
for shape in ['round','square','triangular','oval','rectangular']:
 for obj,c in shape_objects:
    add('shape',f'{article(shape)} [{shape}] {obj} is shown with its outer outline clearly visible',shape,obj,'outline',c,f'The {obj} has a {shape} outer outline.','保留场景，人工指定几何轮廓；不使用部件形状或同义形状提示。')
pattern_objs=[('shirt',6),('scarf',6),('hat',6),('handbag',6),('sock',6),('blanket',4),('cushion',4),('curtain',2),('tablecloth',1),('umbrella',3)]
surface_objs=[('vase',9),('bowl',7),('plate',7),('stone',0),('flowerpot',9),('wooden box',6),('ceramic tile',4),('sculpture',9),('tray',1),('statue',9)]
for texture in ['striped','checkered','polka-dotted','rough','smooth']:
 for obj,c in (pattern_objs if texture in ['striped','checkered','polka-dotted'] else surface_objs):
    add('texture',f'{article(texture)} [{texture}] {obj} is shown with its surface clearly visible',texture,obj,'pattern' if texture in ['striped','checkered','polka-dotted'] else 'surface',c,f'The {obj} is {texture}.','保留场景，人工指定图案或表面质感，避免在背景重复该目标。')
count_objs=[('mugs',1),('bottles',7),('books',2),('hourglasses',5),('remote controls',4),('toy cars',5),('hats',6),('bowls',7),('flowerpots',9),('baskets',3)]
for number in ['Two','Three','Four','Five','Six']:
 for obj,c in count_objs:
    add('count',f'[{number}] {obj} are arranged separately, with every item fully visible',number,obj,'single_category',c,f'Exactly {number.lower()} {obj} are present.','保留场景，人工指定精确数量2–6；名词复数和其余文本保留。')
pairs=[('mug','coffee pot',1),('vase','bowl',9),('toy car','wooden box',5),('notebook','pencil case',5),('hat','handbag',6)]
for rel in ['to the left of','to the right of']:
 for repeat in range(2):
  for x,y,c in pairs:
    if repeat:x,y=y,x
    add('spatial_relation',f'{article(x)} {x} is [{rel}] a {y}, with both objects separated and visible from the front',rel,x+' relative to '+y,'left_right',c,f'The {x} is {rel} the {y} from the viewer perspective.','来源场景中的两个主体为人工组合；左右按观察者视角。')
for rel in ['above','below']:
 for x,y,c in [('picture frame','wall clock',2),('shelf','mirror',9),('sign','picture frame',2),('wall lamp','shelf',2),('wall clock','sign',9)]:
    add('spatial_relation',f'{article(x)} {x} is mounted [{rel}] a {y}, with both objects fully visible',rel,x+' relative to '+y,'above_below',c,f'The {x} is {rel} the {y}.','人工构造可悬挂对象的上下关系，避免不自然的悬浮物体。')
for rel in ['in front of','behind']:
 for x,y,c in pairs:
    add('spatial_relation',f'{article(x)} {x} is [{rel}] a {y}, with both objects visible from an oblique viewing angle',rel,x+' relative to '+y,'front_behind',c,f'The {x} is {rel} the {y}.','人工构造前后关系；遮挡歧义需保留并在局限中报告。')
for rel in ['inside','outside']:
 for x,y,c in [('ball','basket',3),('apple','bowl',7),('toy car','open box',5),('spoon','mug',1),('hat','basket',6)]:
    add('spatial_relation',f'{article(x)} {x} is [{rel}] a {y}, with the object and container clearly visible',rel,x+' relative to '+y,'containment',c,f'The {x} is {rel} the {y}.','人工指定容纳关系，保留来源场景。')
from collections import Counter
assert Counter(x['semantic'] for x in rows)==dict.fromkeys(['object','color','shape','texture','count','spatial_relation'],50)
assert len({x['prompt'] for x in rows})==300
ids={}
for r in rows:
 ids.setdefault(r['prompt'],f'prompt_{len(ids)+1:03d}');r['prompt_id']=ids[r['prompt']]
 assert 20<=r['word_count']<=50,(r['id'],r['word_count'])
(P/'prompts.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
for sem in Counter(x['semantic'] for x in rows):
 (P/f'{sem}.json').write_text(json.dumps([x for x in rows if x['semantic']==sem],ensure_ascii=False,indent=2)+'\n')
review=['# 今日实验：六类各50条','','基于 CSFM 的10个场景主题人工构造，不是随机抽取的300条原始caption。属性及对象均可能被修改。加粗为唯一干预目标；完整来源与改写见 JSON。','']
for sem in Counter(x['semantic'] for x in rows):
 review += [f'## {sem}','','|ID|Prompt|子类|','|---|---|---|']
 for r in rows:
  if r['semantic']!=sem:continue
  a,b=r['spans'][0];p=r['prompt'];review.append(f"|{r['id']}|{p[:a]}**{p[a:b]}**{p[b:]}|{r['subtype']}|")
 review.append('')
(P/'review.md').write_text('\n'.join(review))
print('Counts',dict(Counter(x['semantic'] for x in rows)))
print('Color',dict(Counter(x['target_text'] for x in rows if x['semantic']=='color')))
print('Words',min(x['word_count'] for x in rows),max(x['word_count'] for x in rows))
