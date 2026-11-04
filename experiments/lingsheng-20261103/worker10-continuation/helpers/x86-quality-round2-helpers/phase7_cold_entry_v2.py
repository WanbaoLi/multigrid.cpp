#!/usr/bin/env python3
"""Fresh-publication-v2 sha boundary around the unchanged frozen cold adapter."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys

import file_integrity as integrity
import fresh_publication_v2 as fresh


def value(argv,flag):
    integrity.require(argv.count(flag)==1 and argv.index(flag)+1<len(argv),'Exactly one '+flag+' required')
    return argv[argv.index(flag)+1]


def main():
    argv=sys.argv[1:];integrity.require('--'in argv,'Explicit -- before unchanged adapter arguments required')
    boundary=argv.index('--');parser=argparse.ArgumentParser(description=__doc__)
    for name in('adapter','publication-output'):parser.add_argument('--'+name,type=Path,required=True)
    for name in('expected-entry-sha','expected-adapter-sha','expected-publication-sha','expected-reader-sha'):parser.add_argument('--'+name,required=True)
    args=parser.parse_args(argv[:boundary]);remaining=argv[boundary+1:]
    split=remaining.index('--');cold_args=remaining[split+1:]
    output=Path(value(cold_args,'--output'));target=output/'propagator.npy'
    rank_text=os.environ.get('OMPI_COMM_WORLD_RANK','0')
    integrity.require(rank_text.isdecimal()and int(rank_text)<1024,'OpenMPI rank identity required')
    rank=int(rank_text);strict=integrity.read_dual;publication=None;published=[];success=False;saved=sys.argv
    directory=args.publication_output.resolve()/('rank%05d'%rank)
    integrity.require(not directory.is_relative_to(output.resolve())and not output.resolve().is_relative_to(directory),
                      'Publication proof must stay outside numerical output')
    if rank==0:
        publication=fresh.FreshPublication(output,[dict(relative='propagator.npy',kind='npy-propagator',
            expected_sha256=None,bytes=fresh.PROP_BYTES)],directory/'publications',reader=strict)
    integrity.known_vectors();strict(__file__,args.expected_entry_sha)
    strict(args.adapter,args.expected_adapter_sha);strict(fresh.__file__,args.expected_publication_sha)
    strict(integrity.__file__,args.expected_reader_sha)
    directory.mkdir(parents=True,mode=0o700,exist_ok=False)
    startup=dict(complete=True,protocol=fresh.PROTOCOL,entry_sha256=args.expected_entry_sha,
        publication_module_sha256=args.expected_publication_sha,frozen_adapter_sha256=args.expected_adapter_sha,
        reader_sha256=args.expected_reader_sha,rank=rank,eligibility=publication.eligibility if publication else None,
        cold_arguments=cold_args,frozen_cold_and_clocks_unchanged=True,immutable_reader_unchanged=True,
        scope='Fresh first output digest after cold/API clocks; frozen raw adapter final artifacts linked at terminal boundary')
    integrity.write_json_private(directory/'startup.json',startup)
    startup_sha=strict(directory/'startup.json')['openssl_sha256']
    def patched(path,expected=None,expected_size=None,**kwargs):
        if publication is None or not publication.contains(path):return strict(path,expected,expected_size,**kwargs)
        key=str(Path(path).resolve(strict=True))
        if key in publication.published:
            integrity.require(expected in(None,publication.published[key]),'Published cold output expected SHA changed')
            return strict(path,publication.published[key],fresh.PROP_BYTES,**kwargs)
        integrity.require(expected is None and expected_size==fresh.PROP_BYTES,'Only unpublished full-size cold propagator may publish')
        row=publication.read(path,None,fresh.PROP_BYTES,
            parent_protocol=dict(path=str(directory/'startup.json'),sha256=startup_sha),**kwargs)
        published.append(row['fresh_output_publication']);return row
    spec=importlib.util.spec_from_file_location('_fresh_v2_frozen_cold_adapter',args.adapter)
    frozen=importlib.util.module_from_spec(spec);spec.loader.exec_module(frozen)
    try:
        integrity.read_dual=patched;sys.argv=[str(args.adapter),*remaining];frozen.main()
        integrity.require(len(published)==(1 if rank==0 else 0),'Fresh cold publication boundary count differs')
        success=True
    finally:
        integrity.read_dual=strict;sys.argv=saved
        raw_directory=Path(value(remaining[:split],'--audit-output')).resolve()/('rank%05d'%rank)
        links={}
        for name in('protocol.json','manifest.json'):
            path=raw_directory/name
            if path.is_file():links[name]=dict(path=str(path),sha256=strict(path)['openssl_sha256'])
        terminal=success and len(links)==2
        protocol=dict(complete=True,passed=terminal,protocol=fresh.PROTOCOL,entry_sha256=args.expected_entry_sha,
            publication_module_sha256=args.expected_publication_sha,startup_sha256=startup_sha,
            rank=rank,publications=published,parent_raw_artifacts=links,
            publication_calls=len(published),frozen_cold_and_clocks_unchanged=True)
        integrity.write_json_private(directory/'protocol.json',protocol)
        print('PHASE7_PUBLICATION_V2 '+json.dumps(dict(rank=rank,passed=terminal,path=str(directory/'protocol.json'),
            sha256=strict(directory/'protocol.json')['openssl_sha256'])),flush=True)
        if success:integrity.require(terminal,'Both completed frozen raw cold protocol/manifest links required')


if __name__=='__main__':main()
