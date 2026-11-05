#!/usr/bin/env python3
"""Prepare reviewed worker12 argv/manifest only; no submit/deploy/scheduler API."""
import argparse
import hashlib
import json
from pathlib import Path,PurePosixPath
import re

ROOT='/home/share/nsls_lwb/.cache/mg-opt-20261103'
WRAPPERS=('worker12.sh','worker12_entry.py','worker12_preflight.py','worker12_login_record.py','worker12_runtime_probe.py')


def plan(source,expected_source_head,root=ROOT):
    source=PurePosixPath(source);root=PurePosixPath(root)
    if not source.is_absolute()or '..'in source.parts or not root.is_absolute():raise ValueError('Canonical absolute site paths required')
    if not re.fullmatch('[0-9a-f]{40}',expected_source_head):raise ValueError('Explicit exact reviewed40hex source head required')
    source_args=['--source',str(source),'--expected-source-head',expected_source_head]
    return dict(prepared_only_not_submitted=True,authorized_submission=False,previous_job='2026153',
        source_root=str(source),expected_source_head=expected_source_head,allocation='mg-opt-20261103-worker12',
        expected_host='cn19486',queue='queue12',idle_timeout_seconds=3600,wall_seconds=14400,safe_reserve_seconds=300,
        predecessor_requirement='Root must confirm2026153 terminal and inspect all old task cleanup before submission; login authentication then requires predecessor end<=new start',
        argv=['dsub','-q','q_hpcapp','-A','common','-nn','1','-N','1','-x','job','-nl','cn19486',
            '-R','cpu=592,mem=480000MB','-T','14400','-n','mg-opt-worker12','--cwd',str(root),
            '-o',str(root/'worker12.log'),'/bin/bash',str(root/'worker12.sh'),*source_args],
        login_record_writer_argv_after_submit=['python3',str(root/'worker12_login_record.py'),'--root',str(root),
            '--job','EXACT_NEW_DSUB_JOB_ID','--wait-seconds','3600',*source_args])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',required=True);parser.add_argument('--expected-source-head',required=True)
    parser.add_argument('--root',default=ROOT);parser.add_argument('--output',type=Path)
    args=parser.parse_args();value=plan(args.source,args.expected_source_head,args.root)
    value['wrapper_sha256']={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()for name in WRAPPERS}
    text=json.dumps(value,indent=2)+'\n'
    if args.output:
        with args.output.open('x',encoding='utf-8',newline='\n')as stream:stream.write(text)
    print(text,end='')


if __name__=='__main__':main()
