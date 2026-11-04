"""Explicit capture-boundary extension around unchanged publication dispatcher."""
import argparse
import importlib.util
import os
from pathlib import Path
import sys

import file_integrity as integrity

BASE_SHA='a5cb583cbb0c911fa1e4236b7bfd026fc64f6902a9fcce2f4bffcb6b630ae78f'


def extend_stage(result, name, wrapper, wrapper_sha, directory):
    argv=result.get('argv',[])
    if '--verify'in argv:return result
    indices=[i for i,v in enumerate(argv)if Path(v).name=='raw_benchmark_publication_v2.py']
    if not indices:return result
    integrity.require(len(indices)==1,'Exactly one original publication wrapper required')
    i=indices[0]
    prefix=[str(wrapper),'--expected-self-sha',wrapper_sha,'--capture-output',str(directory/(name+'.json')),
            '--attempt',name,'--']
    return dict(result,argv=[*argv[:i],*prefix,*argv[i+1:]])


def main():
    argv=sys.argv[1:];integrity.require('--'in argv,'Explicit frozen dispatcher argv required')
    at=argv.index('--');parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-self-sha',required=True)
    parser.add_argument('--capture-wrapper-sha',required=True)
    args=parser.parse_args(argv[:at]);remaining=argv[at+1:]
    integrity.read_dual(__file__,args.expected_self_sha)
    root=Path(__file__).resolve().parent;wrapper=root/'runtime_benchmark_capture_v4.py'
    integrity.read_dual(wrapper,args.capture_wrapper_sha)
    base=root/'raw_controller_publication_v2.py';integrity.read_dual(base,BASE_SHA)
    spec=importlib.util.spec_from_file_location('_frozen_dispatch_capture_target',base)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    transform=module.transform_stage;child=module.child_trial_command
    directory=Path(os.environ['LQCD_OPT_CAPTURE_DIR'])
    integrity.require(directory.is_absolute()and directory==directory.resolve(strict=False),'Canonical external runtime audit directory required')
    def stage(options,campaign,name,key,command):
        return extend_stage(transform(options,campaign,name,key,command),name,wrapper,args.capture_wrapper_sha,directory)
    def trial(options,argv):
        result=child(options,argv)
        if result==argv:return result
        i=result.index(str(base))
        return [*result[:i],str(Path(__file__).resolve()),'--expected-self-sha',args.expected_self_sha,
                '--capture-wrapper-sha',args.capture_wrapper_sha,'--',*result[i+1:]]
    module.transform_stage=stage;module.child_trial_command=trial
    saved=sys.argv
    try:
        sys.argv=[str(base),*remaining];module.main()
    finally:sys.argv=saved


if __name__=='__main__':main()
