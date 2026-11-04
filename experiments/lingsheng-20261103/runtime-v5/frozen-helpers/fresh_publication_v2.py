#!/usr/bin/env python3
"""Bounded first publication of declared, absent-at-start producer outputs.

Immutable inputs never use this protocol. A rejected read is retained and never
relabeled. Before-read empty digests are diagnostics, never payload candidates.
"""
import ast
from copy import deepcopy
import hashlib
import os
from pathlib import Path
import re
import struct
import time

import file_integrity as integrity

PROTOCOL='fresh-output-publication-v2'
WINDOWS=('initial','fd_before','fd_after','path_after')
IDENTITY=('dev','inode','bytes')
FIELDS=set(IDENTITY)|{'mtime_ns','ctime_ns'}
EMPTY_SHA=hashlib.sha256(b'').hexdigest()
PROP_BYTES=2038431872
PROP_SHAPE=(64,24,24,24,4,4,3,3)
GAUGE_BYTES=509607936
GAUGE_SHA='126d658999367b0ece3801c61cd143542d7db0dddc37ab60e6e668e18faa6834'


def rejection_kind(row,expected,size):
    """Select only the two observed pure timestamp boundaries, with exact counts."""
    try:
        windows=[row[key]for key in WINDOWS]
        common=(row['complete']is True and row['passed']is False and row['metadata_stable']is False and
            row['original_open_mode']=='O_RDONLY'and row['same_immutable_bytes']is True and
            row['expected_sha256']==expected and row['required_bytes']==size and
            all(set(meta)==FIELDS and meta['bytes']==size for meta in windows)and
            all(all(meta[key]==windows[0][key]for key in IDENTITY)for meta in windows)and
            windows[2]==windows[3]and row['openssl_sha256']==row['software_sha256'])
        if not common:return None
        if (row['error']=='Path/FD identity changed before read'and row['read_bytes']==0 and
            row['pread_calls']==0 and row['positive_short_reads']==0 and row['eof_probe_bytes']is None and
            row['byte_count_exact']is False and row['openssl_sha256']==EMPTY_SHA and
            windows[0]!=windows[1]and windows[1]==windows[2]):return 'before-read-timestamp-only-zero-bytes'
        if (row['error']=='Strict digest/identity/count/EOF gate failed'and row['read_bytes']==size and
            row['pread_calls']>=2 and row['eof_probe_bytes']==0 and row['byte_count_exact']is True and
            windows[0]==windows[1]and windows[0]!=windows[2]and
            re.fullmatch('[0-9a-f]{64}',row['openssl_sha256'])and
            (expected is None or row['openssl_sha256']==expected)):return 'full-read-timestamp-only'
    except(KeyError,TypeError):pass
    return None


def strict_pass(row,expected,size,baseline=None):
    try:
        return (row['complete']is True and row['passed']is True and row['metadata_stable']is True and
            row['byte_count_exact']is True and row['same_immutable_bytes']is True and
            row['original_open_mode']=='O_RDONLY'and row['read_bytes']==size and row['required_bytes']==size and
            row['eof_probe_bytes']==0 and row['pread_calls']>=2 and
            row['expected_sha256']==expected and row['openssl_sha256']==row['software_sha256']and
            re.fullmatch('[0-9a-f]{64}',row['openssl_sha256'])and
            (expected is None or row['openssl_sha256']==expected)and
            all(row[key]==(baseline or row['initial'])for key in WINDOWS))
    except(KeyError,TypeError):return False


def sync_directory(path):
    fd=os.open(str(path),os.O_RDONLY|getattr(os,'O_DIRECTORY',0)|getattr(os,'O_CLOEXEC',0))
    try:os.fsync(fd)
    finally:os.close(fd)


def npy_header(path,size,baseline,shape=PROP_SHAPE):
    """Read-only closed NPY header, bound to the final strict file identity."""
    fd=os.open(str(path),os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_CLOEXEC',0))
    try:
        integrity.require(integrity.metadata(os.fstat(fd))==baseline,'NPY header identity changed before check')
        prefix=os.pread(fd,10,0)
        integrity.require(len(prefix)==10 and prefix[:8]==b'\x93NUMPY\x01\x00','Expected closed NPY1 propagator header')
        length=struct.unpack('<H',prefix[8:])[0]
        integrity.require(10+length==128,'Frozen propagator header offset must remain128')
        raw=os.pread(fd,length,10)
        integrity.require(len(raw)==length and raw.endswith(b'\n'),'Truncated/unfinished NPY header')
        header=ast.literal_eval(raw.decode('latin1').strip())
        integrity.require(header==dict(descr='<c16',fortran_order=False,shape=tuple(shape)),
                          'Propagator dtype/shape/C-order differs from closed writer contract')
        elements=1
        for value in shape:elements*=value
        integrity.require(size==128+elements*16,'Propagator header/payload byte count differs')
        integrity.require(integrity.metadata(os.fstat(fd))==baseline==integrity.metadata(Path(path).stat()),
                          'NPY identity changed while checking closed header')
        return dict(complete=True,passed=True,header_bytes=128,dtype='<c16',shape=list(shape),fortran_order=False)
    finally:os.close(fd)


class FreshPublication:
    def __init__(self,output,declarations,audit,*,reader=None,parent_protocol=None):
        self.output=Path(output)
        integrity.require(self.output.is_absolute()and self.output==self.output.resolve(strict=False)and
            not os.path.lexists(self.output),'Entire declared output directory must be canonical and absent at CLI start')
        self.audit=Path(audit);self.reader=reader or integrity.read_dual;self.tokens={};self.published={}
        integrity.require(bool(declarations),'At least one predeclared fresh output required')
        parent_path=self.output.parent
        while not parent_path.exists():parent_path=parent_path.parent
        parent=integrity.metadata(parent_path.stat())
        for item in declarations:
            relative=Path(item['relative'])
            integrity.require(not relative.is_absolute()and '..'not in relative.parts and relative.parts,
                              'Safe explicit relative output required')
            path=self.output/relative;key=str(path)
            integrity.require(key not in self.tokens and not os.path.lexists(path),'Duplicate/existing fresh output')
            size=item['bytes'];expected=item.get('expected_sha256');kind=item['kind']
            integrity.require(type(size)is int and size>0 and(expected is None or re.fullmatch('[0-9a-f]{64}',expected)),
                              'Exact fresh byte count and optional fixed digest required')
            if kind=='npy-propagator':integrity.require(relative.name=='propagator.npy'and size==PROP_BYTES and expected is None,'Only unpublished full-size propagator may publish')
            elif kind=='canonical-gauge':integrity.require(relative==Path('gauge.bin')and size==GAUGE_BYTES and expected==GAUGE_SHA,'Canonical scratch gauge identity fixed from start')
            else:raise RuntimeError('Only full12 propagator and canonical fresh scratch gauge declarations are permitted')
            self.tokens[key]=dict(declaration=deepcopy(item),used=False,index=len(self.tokens))
        self.eligibility=dict(protocol=PROTOCOL,complete=True,output=str(self.output),output_absent_at_cli_start=True,
            checked_epoch=time.time(),existing_parent=str(parent_path),parent_identity={key:parent[key]for key in('dev','inode')},
            declarations=deepcopy(declarations),maximum_strict_calls_per_output=3,
            parent_protocol=deepcopy(parent_protocol),immutable_inputs_use_original_strict_reader=True)

    def contains(self,path):return str(Path(path).resolve(strict=False))in self.tokens

    def read(self,path,expected=None,expected_size=None,*,parent_protocol=None,**options):
        path=Path(path);key=str(path.resolve(strict=True));token=self.tokens.get(key)
        integrity.require(token is not None and path.absolute()==path.resolve(strict=True)and not path.is_symlink(),
                          'Fresh publication requires its exact predeclared canonical regular output')
        declaration=token['declaration'];size=declaration['bytes'];fixed=declaration.get('expected_sha256')
        integrity.require(expected_size==size and expected==fixed,'Publication callback expected identity differs from startup declaration')
        integrity.require(not token['used'],'Fresh publication cannot restart/reset, even after a successful publication')
        token['used']=True  # consume before any directory creation/read/failure
        integrity.require(isinstance(parent_protocol,dict)and set(parent_protocol)>={'path','sha256'},
                          'Actual already-written parent protocol path/SHA required')
        parent_path=Path(parent_protocol['path'])
        integrity.require(parent_path.is_absolute()and not parent_path.is_symlink()and
            parent_path==parent_path.resolve(strict=True),'Canonical parent protocol required')
        integrity.read_dual(parent_path,parent_protocol['sha256'])
        if 'startup_path'in parent_protocol:
            integrity.read_dual(parent_protocol['startup_path'],parent_protocol['startup_sha256'])
        directory=self.audit/('output-%03d'%token['index']);directory.mkdir(parents=True,mode=0o700,exist_ok=False)
        proof=dict(protocol=PROTOCOL,complete=False,passed=False,path=key,eligibility=deepcopy(self.eligibility),
            parent_protocol=deepcopy(parent_protocol),reads=[],progress=[],strict_calls=0,full_reads=0,
            maximum_strict_calls=3,first_rejection_accepted=False,expected_previously_published=fixed is not None)
        def persist():
            receipt=directory/('progress-%03d.json'%len(proof['progress']))
            integrity.write_json_private(receipt,deepcopy(proof));sync_directory(directory)
            proof['progress'].append(dict(path=str(receipt),sha256=integrity.read_dual(receipt)['openssl_sha256']))
        integrity.write_json_private(directory/'eligibility.json',proof['eligibility']);sync_directory(directory)
        def call(index,comparison):
            kwargs=dict(options);kwargs['snapshot']=directory/('read-%d-bad-view.bin'%index)
            try:row=self.reader(path,comparison,size,**kwargs)
            except integrity.IntegrityError as error:
                row=deepcopy(error.report);proof['reads'].append(row);proof['strict_calls']+=1
                proof['full_reads']+=int(row.get('byte_count_exact')is True and row.get('eof_probe_bytes')==0)
                integrity.write_json_private(directory/('read-%d.json'%index),row);persist();raise
            row=deepcopy(row);proof['reads'].append(row);proof['strict_calls']+=1
            proof['full_reads']+=int(row.get('byte_count_exact')is True and row.get('eof_probe_bytes')==0)
            integrity.write_json_private(directory/('read-%d.json'%index),row);persist();return row
        try:
            try:
                first=call(0,fixed)
                integrity.require(strict_pass(first,fixed,size),'Initial strict pass incomplete')
                final=first;proof['mode']='original-first-strict-pass'
            except integrity.IntegrityError as error:
                first=error.report;kind=rejection_kind(first,fixed,size)
                integrity.require(kind is not None,'First rejection exceeds the two exact timestamp-only publication boundaries')
                baseline=first['fd_after'];proposed=first['openssl_sha256']if kind=='full-read-timestamp-only'else None
                proof.update(mode=kind,ending_metadata=deepcopy(baseline),unpublished_proposed_sha256=proposed,
                    empty_digest_is_payload_candidate=False)
                persist()  # first rejection and precise selector durable before retry
                for index in(1,2):
                    comparison=fixed or proposed
                    row=call(index,comparison)
                    integrity.require(strict_pass(row,comparison,size,baseline),'Follow-up full strict window changed identity/metadata/digest')
                    if proposed is None:proposed=row['openssl_sha256'];proof['unpublished_proposed_sha256']=proposed
                    integrity.require(row['openssl_sha256']==proposed and(fixed is None or proposed==fixed),
                                      'Fresh full reads disagree or differ from fixed canonical digest')
                    final=row
            baseline=final['path_after']
            integrity.require(integrity.metadata(path.stat())==baseline,'Fresh output changed after final strict window')
            if declaration['kind']=='npy-propagator':proof['closed_npy_header']=npy_header(path,size,baseline,shape=PROP_SHAPE)
            proof.update(complete=True,passed=True,published_sha256=final['openssl_sha256'],
                         rejected_read_count=sum(not row['passed']for row in proof['reads']))
            persist();receipt=directory/'receipt.json';integrity.write_json_private(receipt,proof);sync_directory(directory)
            receipt_sha=integrity.read_dual(receipt)['openssl_sha256'];self.published[key]=final['openssl_sha256']
            result=deepcopy(final);result['fresh_output_publication']=dict(protocol=PROTOCOL,complete=True,passed=True,
                receipt=str(receipt),receipt_sha256=receipt_sha,strict_calls=proof['strict_calls'],full_reads=proof['full_reads'],
                parent_protocol=deepcopy(parent_protocol),full_proof=proof)
            return result
        except BaseException as error:
            proof.update(complete=False,passed=False,error_type=type(error).__name__,message=str(error))
            integrity.write_json_private(directory/'failure.json',proof);sync_directory(directory);raise
