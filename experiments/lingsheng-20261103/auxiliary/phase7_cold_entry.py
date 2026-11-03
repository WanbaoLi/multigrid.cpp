#!/usr/bin/env python3
"""External NEW-output publication boundary around frozen raw_cold_adapter.

The frozen cold main, clock, numerical source and strict immutable verification
are untouched. Only a new prop's first, post-clock, unpublished digest can use
the bounded publication protocol. Inputs and every declared expected SHA stay
on the original strict reader.
"""
import argparse
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys

import file_integrity as integrity
import phase7_publication as publication


def load(path):
    spec=importlib.util.spec_from_file_location('_phase7_frozen_cold_adapter',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def main():
    require=integrity.require;argv=sys.argv[1:];require('--' in argv,'Explicit -- before unchanged cold-adapter arguments required')
    split=argv.index('--');parser=argparse.ArgumentParser(description=__doc__)
    for name in ('adapter','publication-output'):parser.add_argument('--'+name,type=Path,required=True)
    for name in ('expected-entry-sha','expected-adapter-sha','expected-publication-sha','expected-reader-sha'):parser.add_argument('--'+name,required=True)
    args=parser.parse_args(argv[:split]);remaining=argv[split+1:]
    boundary=remaining.index('--');cold_args=remaining[boundary+1:]
    require(cold_args.count('--output')==1,'Exactly one new output directory required')
    raw_output=Path(cold_args[cold_args.index('--output')+1])
    require(not os.path.lexists(raw_output) and not raw_output.is_symlink() and
        raw_output.absolute()==raw_output.resolve(strict=False),'Publication wrapper requires a NEW absent output path without symlink components')
    output=raw_output.resolve()
    target=output/'propagator.npy'
    integrity.known_vectors();integrity.read_dual(__file__,args.expected_entry_sha)
    integrity.read_dual(args.adapter,args.expected_adapter_sha);integrity.read_dual(publication.__file__,args.expected_publication_sha)
    integrity.read_dual(integrity.__file__,args.expected_reader_sha)
    directory=args.publication_output.resolve();require(not directory.is_relative_to(output) and not output.is_relative_to(directory),'Publication receipts must stay outside numerical output')
    directory.mkdir(parents=True,exist_ok=True,mode=0o700)
    rank_text=os.environ.get('OMPI_COMM_WORLD_RANK','0');require(rank_text.isdecimal(),'OpenMPI rank identity required')
    rank=int(rank_text);rank_dir=directory/('rank%05d'%rank);rank_dir.mkdir(mode=0o700,exist_ok=False)
    frozen=load(args.adapter);strict=integrity.read_dual;calls=[];saved=sys.argv;success=False
    protocol=dict(complete=False,passed=False,entry_sha256=args.expected_entry_sha,publication_sha256=args.expected_publication_sha,
        frozen_adapter_sha256=args.expected_adapter_sha,reader_sha256=args.expected_reader_sha,rank=rank,
        target=str(target),output_absent_at_launch=True,scope='New self-produced propagator, after cold/API clocks, before expected SHA publication',
        immutable_input_gold_and_verification_policy='Original strict read only',frozen_cold_and_clocks_unchanged=True)
    def patched(path,expected=None,expected_size=None,**kwargs):
        if Path(path).resolve()!=target:return strict(path,expected,expected_size,**kwargs)
        require(rank==0 and not calls,'Only one root-rank initial output publication is permitted')
        require(expected is None,'An existing expected SHA cannot use publication quiescence')
        calls.append(str(path));snapshots=[]
        def receipt_writer(value):
            # Persist each rejected/progress event BEFORE a subsequent full
            # read. SIGKILL cannot erase the already closed/fsynced receipt.
            receipt_path=rank_dir/('receipt-progress-%03d.json'%len(snapshots))
            integrity.write_json_private(receipt_path,value)
            snapshots.append(dict(path=receipt_path.name,sha256=strict(receipt_path)['openssl_sha256']))
        try:
            result,receipt=publication.publish(path,strict,integrity.IntegrityError,expected=expected,expected_size=expected_size,
                read_options=kwargs,receipt_writer=receipt_writer)
        except publication.PublicationFailure as error:
            integrity.write_json_private(rank_dir/'receipt.json',error.receipt)
            protocol['receipt_snapshots']=snapshots;raise
        integrity.write_json_private(rank_dir/'receipt.json',receipt)
        receipt_sha=strict(rank_dir/'receipt.json')['openssl_sha256']
        protocol['receipt_snapshots']=snapshots
        result=dict(result,new_output_publication=dict(protocol=publication.PROTOCOL,receipt=str(rank_dir/'receipt.json'),
            receipt_sha256=receipt_sha,entry_sha256=args.expected_entry_sha,publication_sha256=args.expected_publication_sha,
            complete=True,passed=True,full_reads=receipt['full_reads']))
        return result
    try:
        integrity.read_dual=patched
        sys.argv=[str(args.adapter),*remaining];frozen.main()
        require(len(calls)==(1 if rank==0 else 0),'Required publication boundary was not reached exactly once')
        success=True
    finally:
        integrity.read_dual=strict;sys.argv=saved
        protocol.update(complete=True,passed=success,publication_calls=len(calls))
        integrity.write_json_private(rank_dir/'protocol.json',protocol)
        print('PHASE7_PUBLICATION '+json.dumps(dict(rank=rank,passed=success,protocol=str(rank_dir/'protocol.json'),
            protocol_sha256=strict(rank_dir/'protocol.json')['openssl_sha256'])),flush=True)

if __name__=='__main__':main()
