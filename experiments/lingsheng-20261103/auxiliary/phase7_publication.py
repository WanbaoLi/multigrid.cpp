#!/usr/bin/env python3
"""Bounded publication of a NEW self-produced output, before expected SHA exists.

Immutable input/gold/verification reads must never call this function. No file
write, timestamp update, sleep, expected-SHA rewrite or unbounded retry occurs.
"""
from copy import deepcopy
import json
from pathlib import Path
import re

IDENTITY=('dev','inode','bytes')
WINDOWS=('initial','fd_before','fd_after','path_after')
PROTOCOL='new-output-publication-v1: first strict read, or one unpublished metadata-only rejection followed by two strict stable full reads'


def require(value,message):
    if not value:raise RuntimeError(message)


def stable_fields(row):
    return [{key:row[window][key] for key in IDENTITY} for window in WINDOWS]


def metadata_only_rejection(row):
    """Recognize only the closed, observed read boundary, never generic I/O errors."""
    try:
        identity=stable_fields(row)
        return (row['complete'] is True and row['passed'] is False and row['expected_sha256'] is None and
            row['metadata_stable'] is False and row['byte_count_exact'] is True and row['eof_probe_bytes']==0 and
            row['original_open_mode']=='O_RDONLY' and row['same_immutable_bytes'] is True and
            row['read_bytes']==row['initial']['bytes'] and
            row['required_bytes'] in (None,row['read_bytes']) and
            row['openssl_sha256']==row['software_sha256'] and bool(re.fullmatch('[0-9a-f]{64}',row['openssl_sha256'])) and
            row['error']=='Strict digest/identity/count/EOF gate failed' and
            all(value==identity[0] for value in identity) and
            row['initial']==row['fd_before'] and row['fd_after']==row['path_after'] and
            set(row['initial'])==set(IDENTITY)|{'mtime_ns','ctime_ns'} and
            all(set(row[window])==set(row['initial']) for window in WINDOWS) and
            row['fd_before']!=row['fd_after'])
    except (KeyError,TypeError):return False


class PublicationFailure(RuntimeError):
    def __init__(self,message,receipt):
        super().__init__(message);self.receipt=receipt


def publish(path,strict_read,integrity_error,*,expected=None,expected_size=None,read_options=None,receipt_writer=None):
    """Return only a strict accepted row; injected reader/writer enable real contracts.

    The caller owns the fresh-path predicate. This function additionally rejects
    an already declared expected SHA. The first failed row is never accepted or
    relabelled. Its digest can only be a proposed, unpublished comparison value.
    """
    require(expected is None,'Publication is forbidden after an expected SHA is declared')
    path=Path(path);options=dict(read_options or {});rows=[]
    receipt=dict(complete=False,passed=False,protocol=PROTOCOL,path=str(path),expected_previously_published=False,
        source_modified=False,timestamps_modified=False,sleep_used=False,maximum_full_reads=3,reads=[])
    def save():
        if receipt_writer:receipt_writer(deepcopy(receipt))
    def call(index,comparison=None):
        kwargs=dict(options)
        if kwargs.get('snapshot') is not None:
            original=Path(kwargs['snapshot']);kwargs['snapshot']=original.with_name(original.stem+'-publication'+str(index)+original.suffix)
        try:
            row=strict_read(path,comparison,expected_size,**kwargs)
            rows.append(deepcopy(row));receipt['reads'].append(dict(index=index,strict_pass=True,report=deepcopy(row)));save()
            return row
        except integrity_error as error:
            row=deepcopy(error.report);rows.append(row)
            receipt['reads'].append(dict(index=index,strict_pass=False,report=row));save()
            raise
    try:
        try:
            first=call(0)
            require(first.get('passed') is True and first.get('metadata_stable') is True and first.get('byte_count_exact') is True and
                first.get('eof_probe_bytes')==0 and first['openssl_sha256']==first['software_sha256'],
                'Initial strict reader did not return a complete pass')
            final=first;receipt['mode']='first-strict-read'
        except integrity_error as error:
            first=deepcopy(error.report)
            require(metadata_only_rejection(first),'First publication read has a failure beyond timestamp change')
            proposed=first['openssl_sha256'];after=first['fd_after']
            receipt.update(mode='one-unpublished-metadata-rejection-plus-two-strict-windows',
                first_rejection_accepted=False,unpublished_proposed_sha256=proposed)
            for index in (1,2):
                row=call(index,proposed)
                require(row['passed'] is True and row['metadata_stable'] is True and row['byte_count_exact'] is True and
                    row['eof_probe_bytes']==0 and row['openssl_sha256']==row['software_sha256']==proposed,
                    'Follow-up strict full-file agreement failed')
                require(all(row[window]==after for window in WINDOWS),
                    'File timestamp/identity changed again after the unpublished rejection')
                final=row
        receipt.update(complete=True,passed=True,published_sha256=final['openssl_sha256'],full_reads=len(rows))
        save();return final,receipt
    except BaseException as error:
        receipt.update(complete=True,passed=False,full_reads=len(rows),error_type=type(error).__name__,error=str(error));save()
        raise PublicationFailure(str(error),receipt) from error
