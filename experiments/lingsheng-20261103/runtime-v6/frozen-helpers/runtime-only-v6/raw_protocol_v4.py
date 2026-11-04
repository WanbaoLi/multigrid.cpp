#!/usr/bin/env python3
"""Frozen protocol4 argv factory: one reviewed SHA chain, parameterized target."""
import importlib.util
from pathlib import Path
import re

FILES={
    'file_integrity.py':'34200de5efea2b362880886354c7436fdfb6300bb1c3730b57823aa8acebf427',
    'raw_scalar_helper.py':'5691366c7f0dabc0c8714b0732612abb2f0019532fe070168ad2cc88f83867f3',
    'raw_benchmark_v4.py':'d006372cdd578e0d3b5694b5733483958b21c037f56df4efbedf996b4f3d3cec',
    'raw_controller_v4.py':'dd2d4049ed2ebd39e08efc03c4528e516c28e518a5c6e2e9de803358715d1b0e',
}
BENCHMARK_SHA='711df30c341f31aa8770b371b5d8ec32fb90cbbe8dff0a173e5e1532d977f5a1'
HELPER_SHA='bc441c56af7ffe65781816c8d18427578e8097f0b35168349a27629655fa2074'
GOLD_SHA='31d5cb29eeaa2714b4db003424da1215668d369288a6706bff03a1e0fb2e71cd'


def prefix(root,entry,entry_sha,audit_tag,python,*,framework_tools=None,
           benchmark_sha=BENCHMARK_SHA,helper_sha=HELPER_SHA,gold_sha=GOLD_SHA,verify=True):
    """Return argv through controller options; caller appends ['--', *target_args]."""
    root=Path(root);entry=Path(entry)
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,79}',audit_tag):raise ValueError('Safe audit tag required')
    for value in (entry_sha,benchmark_sha,helper_sha,gold_sha):
        if not re.fullmatch('[0-9a-f]{64}',value):raise ValueError('Exact SHA256 values required')
    if verify:
        spec=importlib.util.spec_from_file_location('pinned_protocol4_integrity',root/'file_integrity.py')
        integrity=importlib.util.module_from_spec(spec);spec.loader.exec_module(integrity)
        for name,expected in FILES.items():integrity.read_dual(root/name,expected)
        integrity.read_dual(entry,entry_sha)
    return [str(python),'-u',str(root/'raw_controller_v4.py'),
        '--entry',str(entry),'--entry-sha',entry_sha,
        '--framework-tools',str(framework_tools or root/'source/tools/optimization'),
        '--audit-root',str(root/'raw-driver-evidence'/audit_tag),
        '--wrapper',str(root/'raw_benchmark_v4.py'),'--wrapper-sha',FILES['raw_benchmark_v4.py'],
        '--reader-sha',FILES['file_integrity.py'],'--adapter-sha',FILES['raw_controller_v4.py'],
        '--benchmark-sha',benchmark_sha,'--gold-sha',gold_sha,'--helper-sha',helper_sha,
        '--helper-wrapper',str(root/'raw_scalar_helper.py'),'--helper-wrapper-sha',FILES['raw_scalar_helper.py']]


def command(root,entry,entry_sha,audit_tag,python,arguments,**kwargs):
    """The complete command; no shell expansion or environment evaluation."""
    return prefix(root,entry,entry_sha,audit_tag,python,**kwargs)+['--',*map(str,arguments)]
