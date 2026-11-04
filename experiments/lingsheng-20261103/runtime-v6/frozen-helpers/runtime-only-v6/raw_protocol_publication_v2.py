#!/usr/bin/env python3
"""Pinned fresh-publication-v2 argv factory; no nested/double benchmark wrapper."""
import importlib.util
from pathlib import Path
import re

import raw_protocol_v4 as legacy

BENCHMARK_SHA=legacy.BENCHMARK_SHA
HELPER_SHA=legacy.HELPER_SHA
GOLD_SHA=legacy.GOLD_SHA
NEW_FILES={
    'fresh_publication_v2.py':'9ac768cc695f3a1fc7febe15d28798bd39ef8e925d973b8f07e04bb67e3ea01a',
    'raw_benchmark_publication_v2.py':'f55aae8c4f460c93d5f913682e3f526e5f66d4109f84646a9c2a7198f8023f60',
    'raw_scalar_helper_publication_v2.py':'c70badd92adeaa7da071f9166282c6db1b34c75ca21c6bb06b7b8803bbaae097',
    'raw_controller_publication_v2.py':'a5cb583cbb0c911fa1e4236b7bfd026fc64f6902a9fcce2f4bffcb6b630ae78f',
    'phase7_cold_entry_v2.py':'d4e733d6a0188543e4ff50c323ea3a4b28dde849fb66497ba81751b1d0cec2f1',
}
FILES={**legacy.FILES,**NEW_FILES,
    'raw_protocol_v4.py':'1fe892d279305be75f6f814d8e7526d2c09531803ac5ffc6f8483f46b1fd0453'}


def verify_files(root):
    root=Path(root)
    spec=importlib.util.spec_from_file_location('_fresh_v2_factory_integrity',root/'file_integrity.py')
    integrity=importlib.util.module_from_spec(spec);spec.loader.exec_module(integrity)
    for name,expected in FILES.items():integrity.read_dual(root/name,expected)


verify_derived=verify_files


def prefix(root,entry,entry_sha,audit_tag,python,*,verify=True,**kwargs):
    root=Path(root)
    if verify:
        verify_files(root)
        spec=importlib.util.spec_from_file_location('_fresh_v2_entry_integrity',root/'file_integrity.py')
        integrity=importlib.util.module_from_spec(spec);spec.loader.exec_module(integrity)
        integrity.read_dual(entry,entry_sha)
    argv=legacy.prefix(root,entry,entry_sha,audit_tag,python,verify=False,**kwargs)
    argv[argv.index(str(root/'raw_controller_v4.py'))]=str(root/'raw_controller_publication_v2.py')
    for flag,name in(('--wrapper','raw_benchmark_publication_v2.py'),('--helper-wrapper','raw_scalar_helper_publication_v2.py')):
        argv[argv.index(flag)+1]=str(root/name)
    for flag,name in(('--adapter-sha','raw_controller_publication_v2.py'),('--wrapper-sha','raw_benchmark_publication_v2.py'),
                    ('--helper-wrapper-sha','raw_scalar_helper_publication_v2.py')):
        argv[argv.index(flag)+1]=NEW_FILES[name]
    return argv


def command(root,entry,entry_sha,audit_tag,python,arguments,**kwargs):
    return prefix(root,entry,entry_sha,audit_tag,python,**kwargs)+['--',*map(str,arguments)]


def benchmark_command(root,benchmark,audit_output,python,arguments,*,
                      retry_existing_verification_sha=None,verify=True,benchmark_sha=BENCHMARK_SHA):
    root=Path(root);arguments=list(map(str,arguments))
    if verify:verify_files(root)
    if not re.fullmatch('[0-9a-f]{64}',benchmark_sha):raise ValueError('Exact benchmark SHA required')
    argv=[str(python),str(root/'raw_benchmark_publication_v2.py'),'--benchmark',str(benchmark),
        '--audit-output',str(audit_output),'--expected-benchmark-sha',benchmark_sha,
        '--expected-wrapper-sha',NEW_FILES['raw_benchmark_publication_v2.py'],
        '--expected-reader-sha',FILES['file_integrity.py'],'--expected-helper-sha',HELPER_SHA,
        '--helper-wrapper',str(root/'raw_scalar_helper_publication_v2.py'),
        '--expected-helper-wrapper-sha',NEW_FILES['raw_scalar_helper_publication_v2.py']]
    if '--verify'in arguments:
        if '--verification-output'not in arguments:raise ValueError('Fresh explicit independent verification directory required')
        argv+=['--expected-gold-sha',GOLD_SHA]
    if retry_existing_verification_sha is not None:
        if not re.fullmatch('[0-9a-f]{64}',retry_existing_verification_sha):raise ValueError('Exact retained failed-report SHA required')
        argv+=['--retry-existing-verification-sha',retry_existing_verification_sha]
    return argv+arguments
