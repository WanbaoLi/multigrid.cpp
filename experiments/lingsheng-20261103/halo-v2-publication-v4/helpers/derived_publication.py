#!/usr/bin/env python3
"""Bounded publication proof ONLY for an absent-at-start derived scratch file.

Immutable inputs continue to use file_integrity.read_dual without this adapter.
An initial timestamp-only rejection is evidence, never a successful strict read.
"""
from copy import deepcopy
import os
from pathlib import Path
import re
import time

import file_integrity as integrity

METHOD='fresh derived scratch publication: initial strict read; timestamp-only rejection retained; two strict stable re-reads, maximum3'
IDENTITY=('dev','inode','bytes')
METADATA={'dev','inode','bytes','mtime_ns','ctime_ns'}


def timestamp_only_rejection(row,expected,size):
    metadata=[row.get(key,{})for key in ('initial','fd_before','fd_after','path_after')]
    return (row.get('complete') is True and row.get('passed') is False and
        row.get('metadata_stable') is False and row.get('byte_count_exact') is True and
        row.get('same_immutable_bytes') is True and row.get('eof_probe_bytes')==0 and
        row.get('read_bytes')==size and row.get('required_bytes')==size and
        row.get('expected_sha256')==row.get('openssl_sha256')==row.get('software_sha256')==expected and
        row.get('error')=='Strict digest/identity/count/EOF gate failed' and
        all(set(value)==METADATA for value in metadata) and
        metadata[0]==metadata[1] and metadata[2]==metadata[3] and metadata[0]!=metadata[2] and
        all(value['bytes']==size and all(value[key]==metadata[0][key]for key in IDENTITY)for value in metadata))


def strict_row(row,expected,size,metadata):
    return (row.get('complete') is True and row.get('passed') is True and
        row.get('metadata_stable') is True and row.get('byte_count_exact') is True and
        row.get('same_immutable_bytes') is True and row.get('eof_probe_bytes')==0 and row.get('read_bytes')==size and
        row.get('required_bytes')==size and row.get('expected_sha256')==row.get('openssl_sha256')==row.get('software_sha256')==expected and
        all(row.get(key)==metadata for key in ('initial','fd_before','fd_after','path_after')))


def sync_directory(path):
    fd=os.open(str(path),os.O_RDONLY|getattr(os,'O_DIRECTORY',0)|getattr(os,'O_CLOEXEC',0))
    try:os.fsync(fd)
    finally:os.close(fd)


class FreshDerivedPublication:
    def __init__(self,output,expected,size,audit_output,reader=None):
        output=Path(output)
        integrity.require(output.is_absolute() and output==output.resolve(strict=False),
                          'Derived output must be an absolute canonical fresh path')
        integrity.require(not os.path.lexists(output) and not os.path.lexists(output/'gauge.bin'),
                          'Derived output/gauge must be absent at helper CLI startup')
        integrity.require(re.fullmatch('[0-9a-f]{64}',expected)and type(size)is int and size>0,
                          'Fixed expected digest and exact derived byte count required')
        self.path=output/'gauge.bin';self.output=output;self.expected=expected;self.size=size
        self.audit=Path(audit_output);self.reader=reader or integrity.read_dual;self.used=False
        parent=integrity.metadata(output.parent.stat())
        self.eligibility=dict(complete=True,path=str(self.path),output_absent_at_cli_start=True,
            gauge_absent_at_cli_start=True,checked_epoch=time.time(),parent_identity={key:parent[key]for key in ('dev','inode')},
            expected_sha256=expected,required_bytes=size,maximum_full_reads=3)

    def _read(self,index):
        try:
            row=self.reader(self.path,self.expected,self.size,snapshot=self.audit/('read-%d-bad-view.bin'%index))
        except integrity.IntegrityError as error:
            integrity.write_json_private(self.audit/('read-%d.json'%index),error.report)
            sync_directory(self.audit)
            raise
        integrity.write_json_private(self.audit/('read-%d.json'%index),row)
        sync_directory(self.audit)
        return row

    def read(self):
        integrity.require(not self.used,'A derived publication protocol cannot restart or reset its read budget')
        self.used=True
        integrity.require(self.path.is_file() and not self.path.is_symlink() and self.path==self.path.resolve(strict=True),
                          'Created derived gauge must remain a regular canonical file')
        self.audit.mkdir(mode=0o700,parents=True,exist_ok=False)
        proof=dict(complete=False,passed=False,method=METHOD,eligibility=self.eligibility,reads=[],read_count=0)
        integrity.write_json_private(self.audit/'eligibility.json',self.eligibility)
        try:
            try:
                first=self._read(0);proof['reads'].append(first);proof['read_count']=1
            except integrity.IntegrityError as error:
                first=error.report;proof['reads'].append(first);proof['read_count']=1
                # This failure JSON and captured exact bytes have already been
                # durably retained by the strict reader before any retry.
                integrity.require(timestamp_only_rejection(first,self.expected,self.size),
                    'Derived first read failed beyond pure mtime/ctime publication; no retry allowed')
                baseline=first['fd_after']
                fd=os.open(str(self.path),os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_CLOEXEC',0))
                try:
                    integrity.require(integrity.metadata(os.fstat(fd))==baseline,
                                      'Derived metadata changed after first rejected read')
                    os.fsync(fd)  # publish closed derived output, never rewrite payload
                    integrity.require(integrity.metadata(os.fstat(fd))==baseline==integrity.metadata(self.path.stat()),
                                      'Derived metadata changed while publishing closed output')
                finally:os.close(fd)
                sync_directory(self.output)
                for index in (1,2):
                    try:row=self._read(index)
                    except integrity.IntegrityError as error:
                        proof['reads'].append(error.report);proof['read_count']+=1
                        raise
                    proof['reads'].append(row);proof['read_count']+=1
                    integrity.require(strict_row(row,self.expected,self.size,baseline),
                                      'Derived re-read must match first ending metadata and fixed digest exactly')
                final=proof['reads'][-1];proof['mode']='timestamp-only initial rejection plus2 strict stable reads'
            else:
                integrity.require(strict_row(first,self.expected,self.size,first['initial']),
                                  'Derived strict first read did not satisfy original integrity gate')
                final=first;proof['mode']='original strict first read passed'
            integrity.require(integrity.metadata(self.path.stat())==final['path_after'],
                              'Derived metadata changed after final strict read')
            proof.update(complete=True,passed=True,expected_sha256=self.expected,required_bytes=self.size,
                         first_rejection_preserved=not first['passed'])
            integrity.write_json_private(self.audit/'publication.json',proof);sync_directory(self.audit)
            result=deepcopy(final)
            # A compatible row remains a real strict successful read. Embed the
            # entire bounded proof so frozen parent row SHA covers all attempts.
            result['derived_publication']=proof
            return result
        except BaseException as error:
            proof.update(complete=False,passed=False,error_type=type(error).__name__,message=str(error))
            integrity.write_json_private(self.audit/'failure.json',proof);sync_directory(self.audit)
            raise
