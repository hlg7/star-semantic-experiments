"""Copy hash-verified pilot images to blind filenames, without model inference."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sample',type=Path,required=True)
    p.add_argument('--images',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--split',choices=['development','held_out'],default='development')
    a=p.parse_args()
    rows=[r for r in json.loads(a.sample.read_text())['rows'] if r['split']==a.split]
    original={r['name']:r for r in (json.loads(line) for line in (a.images/'runs.jsonl').read_text().splitlines())}
    for r in rows:
        source=a.images/(r['name']+'.png')
        if source.parent.resolve()!=a.images.resolve():raise ValueError('Invalid path')
        if original[r['name']]['image_sha256']!=r['image_sha256']:raise ValueError('Generation provenance mismatch')
        from PIL import Image
        with Image.open(source) as im: im.verify()
    a.output.mkdir(parents=True,exist_ok=True)
    for r in rows:shutil.copyfile(a.images/(r['name']+'.png'),a.output/(r['blind_id']+'.png'))
    ids={r['blind_id'] for r in rows}
    labels=json.loads((a.sample.parent/'human_labels.template.json').read_text())
    dest=a.output/'labels.json'
    if dest.exists():raise FileExistsError('Preserve existing human annotations; choose another output directory')
    dest.write_text(json.dumps([r for r in labels if r['blind_id'] in ids],indent=2)+'\n')
    print(f'Exported {len(rows)} blind images and blank labels. Keep sample.json away from annotators.')

if __name__=='__main__':main()
