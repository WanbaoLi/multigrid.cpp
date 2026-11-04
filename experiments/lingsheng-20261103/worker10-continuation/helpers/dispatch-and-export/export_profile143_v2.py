"""Repair small-export reader boundary, preserving failed export as evidence."""
import ast
from pathlib import Path
import sys
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103');sys.path.insert(0,str(root/'aux-solve-profile-v7'))
import file_integrity as integrity
import os

def payload_bytes(path,expected):
    integrity.read_dual(path,expected)
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        before=integrity.metadata(os.fstat(fd));size=before['bytes'];offset=0;parts=[]
        integrity.require(size<=128*1024**2,'Bounded profile export payload required')
        while offset<size:
            part=os.pread(fd,min(1024**2,size-offset),offset)
            integrity.require(0<len(part)<=size-offset,'Exact profile export read count failure')
            parts.append(part);offset+=len(part)
        integrity.require(os.pread(fd,1,size)==b''and before==integrity.metadata(os.fstat(fd))==integrity.metadata(path.stat()),'Profile export changed during immutable read')
    finally:os.close(fd)
    value=b''.join(parts);integrity.require(integrity.small_dual(value)==expected,'Profile export payload differs');return value

path=root/'export_profile143.py';source=path.read_text()
source=source.replace("out=root/'exports/profile143-complete'","out=root/'exports/profile143-complete-v2'")
tree=ast.parse(source);changed=0
for node in ast.walk(tree):
    if isinstance(node,ast.Call)and isinstance(node.func,ast.Name)and node.func.id=='source_bytes':
        node.func.id='_profile_payload_bytes_v2';changed+=1
assert changed==2
ast.fix_missing_locations(tree)
scope={'__name__':'__main__','_profile_payload_bytes_v2':payload_bytes}
exec(compile(tree,str(path)+':bounded-read-v2','exec'),scope)
