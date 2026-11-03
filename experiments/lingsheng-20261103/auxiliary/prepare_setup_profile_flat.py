#!/usr/bin/env python3
"""Prepare a fresh unranked setup profile from an existing exact-binary recipe.

No native load, profiler, MPI, solver, build, queue or deployment is executed.
The original recipe, profile_setup.py and failed092 records remain untouched.
"""
import argparse
import hashlib
import json
from pathlib import Path,PurePosixPath
import re
import shlex

import raw_protocol_derived as derived
import raw_protocol_v4 as protocol

FILES={
    'profile_setup.py':'309cd4ea35bcd4ea0f6515afd2a98a737a7d9ae546f9f752bcfcb0d06c60c42b',
    'profile_setup_flat.py':'c68317283dd207ba019f595e645448ce738c7d5b2072eead343a8507418d73fa',
    'phase7_cold_entry.py':'8aa8c7f78eb5d26a54a8d84442fff30bec808dbf18951ad396a6d5d4fd25d504',
    'phase7_publication.py':'d66744c2ee7f65442ee76ee86ea1e933b15cdc6948469b2fa0812cdacc1b1406',
    'raw_cold_adapter.py':'c65c2da816c9a68f992a6db4cdbbef98e02954a17015abf8405ea474d780cc69',
    'cold_full12.py':'245ecd8201c1268c8e3a78ba64383ce7dce6334709fe5856deac8033ed39a1de',
    'raw_protocol_derived.py':'a07ccf40e3808d8dd7c6480f1a8f511113d4b1d944e28f627fc5cca092a6fe27',
    'raw_protocol_v4.py':'1fe892d279305be75f6f814d8e7526d2c09531803ac5ffc6f8483f46b1fd0453',
    **derived.DERIVED_FILES,**protocol.FILES,
}
PROFILE_HELPER_SHA='0f8f91305635ae7085d6bb9dcaa96b4c0607b3dfbeb4b83cc3b34526f714bc98'


def option(argv,name):
    if argv.count(name)!=1 or argv.index(name)+1>=len(argv):raise ValueError('Exactly one '+name+' required')
    return argv[argv.index(name)+1]


def recipe_commands(text):
    lines=text.splitlines()
    if len(lines)!=5 or lines[:2]!=['#!/bin/bash','set -eo pipefail']:
        raise ValueError('Use the existing five-line canonical cold replay recipe with separate verifier')
    bootstrap=shlex.split(lines[2])
    if len(bootstrap)!=2 or bootstrap[0]!='source':raise ValueError('One explicit frozen site bootstrap required')
    commands=[shlex.split(line)for line in lines[3:]]
    if any(set(argv)&{'|','||','&&',';','&','>','<'}for argv in commands):raise ValueError('One argv per line required; no shell operators')
    return lines[2],commands[0],commands[1]


def build(cold_command,verify_command,auxiliary,profile_helper,run_output,profile_output,audit_output,publication_output,
          verification_output='independent-setup-flat',benchmark_sha=protocol.BENCHMARK_SHA):
    cold_command=list(map(str,cold_command));verify_command=list(map(str,verify_command));aux=PurePosixPath(auxiliary)
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,79}',verification_output):raise ValueError('Safe fresh verification directory name required')
    if not re.fullmatch('[0-9a-f]{64}',benchmark_sha):raise ValueError('Exact benchmark source SHA required')
    matches=[i for i,value in enumerate(cold_command)if PurePosixPath(value).name=='cold_full12.py']
    if len(matches)!=1:raise ValueError('Exactly one original cold entry required')
    index=matches[0];cold=aux/'cold_full12.py';flat=aux/'profile_setup_flat.py'
    if cold_command[index]!=str(cold):raise ValueError('Cold recipe must identify the pinned auxiliary cold source')
    arguments=cold_command[index+1:]
    if '--fixture'not in arguments or '--gauge'in arguments:raise ValueError('Use the canonical fixture setup diagnosis; no raw-LIME substitution')
    if '--diagnostic'in arguments or '--verify'in arguments:raise ValueError('Input must be an ordinary untouched cold replay recipe')
    original_run=option(arguments,'--output')
    if option(verify_command,'--verify')!=original_run:raise ValueError('Original cold and verification outputs differ')
    outputs=[PurePosixPath(value)for value in (run_output,profile_output,audit_output,publication_output)]
    if any(not value.is_absolute()or '..'in value.parts for value in outputs):raise ValueError('Fresh canonical absolute output paths required')
    run,profile,audit,publication=outputs
    if len(set(outputs))!=4 or any(value.is_relative_to(run)or run.is_relative_to(value)for value in outputs[1:]):
        raise ValueError('Numerical/profile/checksum/publication outputs must be separate')
    arguments[arguments.index('--output')+1]=str(run)
    arguments+=['--diagnostic']
    profile_args=['--cold-wrapper',str(cold),'--profile-helper',str(profile_helper),
                  '--profile-output',str(profile),'--frequency','19',*arguments]
    adapter_args=['--cold-wrapper',str(cold),'--expected-cold-sha',FILES['cold_full12.py'],
        '--expected-reader-sha',FILES['file_integrity.py'],'--expected-adapter-sha',FILES['raw_cold_adapter.py'],
        '--audit-output',str(audit),'--profile-setup',str(flat),'--expected-profile-sha',FILES['profile_setup_flat.py'],
        '--profile-helper',str(profile_helper),'--expected-profile-helper-sha',PROFILE_HELPER_SHA,'--',*profile_args]
    publication_args=['--adapter',str(aux/'raw_cold_adapter.py'),'--publication-output',str(publication),
        '--expected-entry-sha',FILES['phase7_cold_entry.py'],'--expected-adapter-sha',FILES['raw_cold_adapter.py'],
        '--expected-publication-sha',FILES['phase7_publication.py'],'--expected-reader-sha',FILES['file_integrity.py'],
        '--',*adapter_args]
    profiled=[*cold_command[:index],str(aux/'phase7_cold_entry.py'),*publication_args]
    matches=[i for i,value in enumerate(verify_command)if PurePosixPath(value).name=='bench_full12.py']
    if len(matches)!=1:raise ValueError('Exactly one original independent verifier entry required')
    verify_index=matches[0];python_index=verify_index-1
    while python_index>=0 and verify_command[python_index]in ('-u','-B','-I','-E','-s','-S','-O','-OO'):python_index-=1
    if python_index<0 or not PurePosixPath(verify_command[python_index]).name.startswith('python'):
        raise ValueError('Original verifier must be an explicit Python argv')
    verify_args=verify_command[verify_index+1:]
    verify_args[verify_args.index('--verify')+1]=str(run)
    if '--verification-output'in verify_args:raise ValueError('Keep old verifier unchanged; select a new output through this preparation')
    verify_args+=['--verification-output',verification_output]
    raw=derived.benchmark_command(aux,verify_command[verify_index],audit.parent/(audit.name+'-independent'),
        verify_command[python_index],verify_args,verify=False)
    raw[raw.index('--expected-benchmark-sha')+1]=benchmark_sha
    verified=[*verify_command[:verify_index],*raw[1:]]
    return dict(profile_argv=profiled,independent_argv=verified,profile_sources=FILES,
        profile_helper=dict(path=str(profile_helper),sha256=PROFILE_HELPER_SHA),
        original_numerical_output=original_run,new_numerical_output=str(run),
        preserved_launcher_and_environment_argv=cold_command[:index],
        profile_expected_sha256=FILES['profile_setup_flat.py'],benchmark_expected_sha256=benchmark_sha,
        scope='unranked profile_cold_canonical_fixture_to_first12; perf covers Solver.setup only',
        ordinary_ranking_allowed=False,full12_independent_required=True,source_numerics_changed=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recipe-script',type=Path,required=True);parser.add_argument('--auxiliary',required=True)
    parser.add_argument('--profile-helper',required=True);parser.add_argument('--run-output',required=True)
    parser.add_argument('--profile-output',required=True);parser.add_argument('--audit-output',required=True)
    parser.add_argument('--publication-output',required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--local-source-directory',type=Path,default=Path(__file__).parent)
    parser.add_argument('--benchmark-sha',default=protocol.BENCHMARK_SHA)
    args=parser.parse_args()
    for name,expected in FILES.items():
        if hashlib.sha256((args.local_source_directory/name).read_bytes()).hexdigest()!=expected:raise ValueError('Pinned preparation dependency changed: '+name)
    payload=args.recipe_script.read_bytes();bootstrap,cold,verify=recipe_commands(payload.decode('utf-8'))
    prepared=build(cold,verify,args.auxiliary,args.profile_helper,args.run_output,args.profile_output,args.audit_output,
                   args.publication_output,benchmark_sha=args.benchmark_sha)
    args.output.mkdir(parents=True,mode=0o700,exist_ok=False)
    for name,key in [('profile-stage.sh','profile_argv'),('independent-stage.sh','independent_argv')]:
        script=args.output/name
        script.write_text('\n'.join(['#!/bin/bash','set -eo pipefail',bootstrap,shlex.join(prepared[key])])+'\n',encoding='utf-8',newline='\n')
    prepared.update(complete=True,status='prepared_only_not_executed',recipe=str(args.recipe_script),
        recipe_sha256=hashlib.sha256(payload).hexdigest(),bootstrap_line=bootstrap,
        prepared_scripts={name:hashlib.sha256((args.output/name).read_bytes()).hexdigest()for name in ('profile-stage.sh','independent-stage.sh')})
    (args.output/'preparation.json').write_text(json.dumps(prepared,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(output=str(args.output),status=prepared['status'],performance_adoption=False),indent=2))


if __name__=='__main__':main()
