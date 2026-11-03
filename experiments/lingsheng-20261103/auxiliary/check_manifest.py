#!/usr/bin/env python3
"""Verify copied auxiliary bytes only; never execute jobs or alter evidence."""
import hashlib
import json
from pathlib import Path


def main():
    root=Path(__file__).resolve().parent
    path=root/'manifest.json'
    if not path.exists():path=root/'selection-manifest.json'
    manifest=json.loads(path.read_text(encoding='utf-8'))
    rows=manifest['files']+manifest.get('generated_files',[])
    seen=set()
    for row in rows:
        relative=Path(row['path'])
        if relative.is_absolute() or '..' in relative.parts or row['path'] in seen:
            raise RuntimeError('Unsafe/duplicate manifest path')
        seen.add(row['path']);file=root/relative
        if file.is_symlink() or not file.is_file():raise RuntimeError('Missing/nonregular copy: '+row['path'])
        data=file.read_bytes()
        if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:
            raise RuntimeError('Copied bytes changed: '+row['path'])
    print(json.dumps(dict(complete=True,verified_files=len(rows),
        scope='Auxiliary source bytes only; no new numerical/performance acceptance')))


if __name__=='__main__':main()
