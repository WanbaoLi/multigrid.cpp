#!/usr/bin/env python3
"""New warm producer publication boundary around unchanged raw benchmark v4.

CLI is identical to raw_benchmark_v4; expected-wrapper-sha pins THIS entry.
Only root's predeclared unpublished plan outputs use fresh publication v2.
Verify/gold/input/previously published outputs retain the frozen strict reader.
"""
import importlib.util
import json
import os
from pathlib import Path
import re
import sys

import file_integrity as integrity
import fresh_publication_v2 as fresh
from raw_scalar_helper import source_bytes

BASE_SHA='d006372cdd578e0d3b5694b5733483958b21c037f56df4efbedf996b4f3d3cec'
READER_SHA='34200de5efea2b362880886354c7436fdfb6300bb1c3730b57823aa8acebf427'
PUBLICATION_SHA='9ac768cc695f3a1fc7febe15d28798bd39ef8e925d973b8f07e04bb67e3ea01a'


def value(argv,flag):
    integrity.require(argv.count(flag)==1 and argv.index(flag)+1<len(argv),'Exactly one '+flag+' required')
    return argv[argv.index(flag)+1]


def declared_outputs(argv):
    """Only rank0 calls before frozen main can create any numerical output."""
    output=Path(value(argv,'--output'))
    integrity.require(output.is_absolute()and output==output.resolve(strict=False)and not os.path.lexists(output),
                      'Full benchmark output must be absent and canonical before frozen main')
    plan=Path(value(argv,'--plan')).resolve(strict=True)
    plan_sha=integrity.read_dual(plan)['openssl_sha256'];payload=source_bytes(plan,plan_sha)
    data=json.loads(payload);cases=data.get('cases',[])
    integrity.require(cases and all(isinstance(case,dict)and re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,63}',case.get('id',''))for case in cases),
                      'Startup plan must explicitly declare every safe output case')
    names=[case['id']for case in cases]
    integrity.require(len(names)==len(set(names)),'Duplicate startup output cases')
    declarations=[dict(relative=name+'/propagator.npy',kind='npy-propagator',expected_sha256=None,bytes=fresh.PROP_BYTES)for name in names]
    return output,declarations,dict(path=str(plan),sha256=plan_sha,cases=names)


def main():
    argv=sys.argv[1:];self_sha=value(argv,'--expected-wrapper-sha')
    integrity.known_vectors();integrity.read_dual(__file__,self_sha)
    integrity.read_dual(integrity.__file__,READER_SHA);integrity.read_dual(fresh.__file__,PUBLICATION_SHA)
    base=Path(__file__).with_name('raw_benchmark_v4.py');integrity.read_dual(base,BASE_SHA)
    rank_text=os.environ.get('OMPI_COMM_WORLD_RANK','0')
    integrity.require(rank_text.isdecimal()and int(rank_text)<1024,'OpenMPI rank identity required')
    rank=int(rank_text);verifying='--verify'in argv
    audit=Path(value(argv,'--audit-output')).resolve()
    rank_audit=audit if verifying else audit/('rank%05d'%rank)
    outer=audit.parent/(audit.name+'-fresh-publication-v2')/('rank%05d'%rank)
    strict=integrity.read_dual;publication=None;calls=[];success=False;saved=sys.argv
    plan=None
    if rank==0 and not verifying:
        output,declarations,plan=declared_outputs(argv)
        publication=fresh.FreshPublication(output,declarations,outer/'publications',reader=strict)
    # Slower non-root ranks never test output absence after root may create it.
    outer.mkdir(parents=True,mode=0o700,exist_ok=False)
    startup=dict(complete=True,protocol=fresh.PROTOCOL,entry_sha256=self_sha,base_wrapper_sha256=BASE_SHA,
        publication_module_sha256=PUBLICATION_SHA,reader_sha256=READER_SHA,rank=rank,mode='verification'if verifying else'benchmark',
        plan=plan,eligibility=publication.eligibility if publication else None,
        numeric_and_clock_bodies_unchanged=True,immutable_reader_unchanged=True)
    integrity.write_json_private(outer/'startup.json',startup)
    def patched(path,expected=None,expected_size=None,**kwargs):
        if publication is None or not publication.contains(path):return strict(path,expected,expected_size,**kwargs)
        key=str(Path(path).resolve(strict=True))
        if key in publication.published:
            integrity.require(expected in(None,publication.published[key]),'Published output expected digest changed')
            return strict(path,publication.published[key],fresh.PROP_BYTES,**kwargs)
        integrity.require(expected is None and expected_size==fresh.PROP_BYTES,'Fresh output must not already have an expected digest')
        strict(plan['path'],plan['sha256'])
        parent=rank_audit/'protocol.json'
        binding=dict(path=str(parent),sha256=strict(parent)['openssl_sha256'],
            startup_path=str(outer/'startup.json'),startup_sha256=strict(outer/'startup.json')['openssl_sha256'])
        row=publication.read(path,None,fresh.PROP_BYTES,parent_protocol=binding,**kwargs)
        calls.append(row['fresh_output_publication']);return row
    spec=importlib.util.spec_from_file_location('_frozen_publication_raw_benchmark',base)
    frozen=importlib.util.module_from_spec(spec);spec.loader.exec_module(frozen)
    forwarded=list(argv);forwarded[forwarded.index('--expected-wrapper-sha')+1]=BASE_SHA
    try:
        integrity.read_dual=patched;sys.argv=[str(base),*forwarded];frozen.main()
        integrity.require(publication is None or len(calls)==len(publication.tokens),'Not every declared fresh propagator was published')
        if plan is not None:strict(plan['path'],plan['sha256'])
        success=True
    finally:
        integrity.read_dual=strict;sys.argv=saved
        links={}
        for name in('protocol.json','manifest.json'):
            target=rank_audit/name
            if target.is_file():links[name]=dict(path=str(target),sha256=strict(target)['openssl_sha256'])
        terminal=success and len(links)==2
        manifest=dict(complete=terminal,passed=terminal,protocol=fresh.PROTOCOL,startup_sha256=strict(outer/'startup.json')['openssl_sha256'],
            entry_sha256=self_sha,base_wrapper_sha256=BASE_SHA,publication_module_sha256=PUBLICATION_SHA,
            parent_raw_artifacts=links,published_outputs=calls,rank=rank)
        integrity.write_json_private(outer/'manifest.json',manifest)
        print('FRESH_WARM_PUBLICATION '+json.dumps(dict(complete=terminal,rank=rank,path=str(outer/'manifest.json'),
            sha256=strict(outer/'manifest.json')['openssl_sha256'])),flush=True)
        if success:integrity.require(terminal,'Both completed frozen parent protocol/manifest links required')


if __name__=='__main__':main()
