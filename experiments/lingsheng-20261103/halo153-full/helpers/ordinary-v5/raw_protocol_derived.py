#!/usr/bin/env python3
"""New explicit protocol4 argv factory with fresh-derived-gauge helper revision.

Default applies ONLY to new stages/fresh verification directories. Legacy mode
returns the exact old prefix for old passed command identities; never rewrite
old stages or turn a failed parent task into a pass.
"""
import importlib.util
from pathlib import Path
import re

import raw_protocol_v4 as legacy

DERIVED_FILES={
    'derived_publication.py':'83b790954b64b0ae7ae8e71ed2978b752f30477bafd7fa48cdfd6ef548b683a6',
    'raw_scalar_helper_derived.py':'25b6fb0d171efb12954edbd0941701ac38fdcb954cf1882de443b50e755659a2',
}


def verify_derived(root):
    root=Path(root)
    spec=importlib.util.spec_from_file_location('pinned_derived_factory_integrity',root/'file_integrity.py')
    integrity=importlib.util.module_from_spec(spec);spec.loader.exec_module(integrity)
    for name,expected in {**legacy.FILES,**DERIVED_FILES}.items():integrity.read_dual(root/name,expected)


def prefix(root,entry,entry_sha,audit_tag,python,*,legacy_helper=False,verify=True,**kwargs):
    argv=legacy.prefix(root,entry,entry_sha,audit_tag,python,verify=verify,**kwargs)
    if legacy_helper:return argv
    root=Path(root)
    if verify:verify_derived(root)
    argv[argv.index('--helper-wrapper')+1]=str(root/'raw_scalar_helper_derived.py')
    argv[argv.index('--helper-wrapper-sha')+1]=DERIVED_FILES['raw_scalar_helper_derived.py']
    return argv


def command(root,entry,entry_sha,audit_tag,python,arguments,**kwargs):
    return prefix(root,entry,entry_sha,audit_tag,python,**kwargs)+['--',*map(str,arguments)]


def benchmark_command(root,benchmark,audit_output,python,arguments,*,
                      retry_existing_verification_sha=None,verify=True):
    """Direct new-stage argv. Do not wrap this already adapted argv a second time.

    For controller/trial dispatch, use command()/prefix() instead. Here the
    caller's existing stage function logs this exact argv under a NEW stage ID.
    """
    root=Path(root);arguments=list(map(str,arguments))
    if verify:verify_derived(root)
    argv=[str(python),str(root/'raw_benchmark_v4.py'),'--benchmark',str(benchmark),
        '--audit-output',str(audit_output),'--expected-benchmark-sha',legacy.BENCHMARK_SHA,
        '--expected-wrapper-sha',legacy.FILES['raw_benchmark_v4.py'],
        '--expected-reader-sha',legacy.FILES['file_integrity.py'],
        '--expected-helper-sha',legacy.HELPER_SHA,'--helper-wrapper',str(root/'raw_scalar_helper_derived.py'),
        '--expected-helper-wrapper-sha',DERIVED_FILES['raw_scalar_helper_derived.py']]
    if '--verify'in arguments:
        if '--verification-output'not in arguments:raise ValueError('Fresh explicit verification directory required')
        argv+=['--expected-gold-sha',legacy.GOLD_SHA]
    if retry_existing_verification_sha is not None:
        if not re.fullmatch('[0-9a-f]{64}',retry_existing_verification_sha):raise ValueError('Exact prior failed-report SHA required')
        argv+=['--retry-existing-verification-sha',retry_existing_verification_sha]
    return argv+arguments
