"""Read-only integration checks for the three bounded fresh-publication scopes."""
import importlib.util
import json
from pathlib import Path
from raw_scalar_helper import source_bytes


def require(value,message):
    if not value:raise RuntimeError(message)


def read(path,sha,expected=None):
    path=Path(path);digest=sha(path)
    require(expected is None or digest==expected,'Changed publication metadata: '+str(path))
    return json.loads(source_bytes(path,digest))


def core(aux,sha,files):
    target=Path(aux)/'fresh_publication_v2.py'
    require(sha(target)==files[target.name],'Fresh core differs from frozen integration closure')
    spec=importlib.util.spec_from_file_location('_owned_audit_fresh_core',target)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def publication(value,target,digest,kind,audit_root,module,sha):
    target=Path(target).resolve();receipt_path=Path(value['receipt'])
    require(value['protocol']==module.PROTOCOL and value['complete'] and value['passed'] and
        receipt_path.resolve()==receipt_path and receipt_path.is_relative_to(Path(audit_root).resolve()),
        'Publication receipt outside exact owned audit scope')
    proof=read(receipt_path,sha,value['receipt_sha256'])
    require(proof==value['full_proof'] and proof['complete'] and proof['passed'] and proof['protocol']==module.PROTOCOL and
        proof['path']==str(target) and proof['published_sha256']==digest and proof['first_rejection_accepted'] is False,
        'Published output proof differs from its actual final receipt')
    fixed=None if kind=='npy-propagator' else module.GAUGE_SHA
    size=module.PROP_BYTES if kind=='npy-propagator' else module.GAUGE_BYTES
    eligibility=proof['eligibility'];output=Path(eligibility['output'])
    declarations=[row for row in eligibility['declarations'] if output/row['relative']==target]
    require(eligibility['complete'] and eligibility['output_absent_at_cli_start'] and
        eligibility['immutable_inputs_use_original_strict_reader'] and eligibility['maximum_strict_calls_per_output']==3 and
        len(declarations)==1 and declarations[0]['kind']==kind and declarations[0]['bytes']==size and
        declarations[0].get('expected_sha256')==fixed and proof['expected_previously_published']==(fixed is not None),
        'Unknown propagator and fixed canonical-gauge startup scopes were mixed')
    require(value['parent_protocol']==proof['parent_protocol'],'Parent protocol binding differs')
    parent=value['parent_protocol'];read(parent['path'],sha,parent['sha256'])
    if 'startup_path' in parent:read(parent['startup_path'],sha,parent['startup_sha256'])
    rows=proof['reads']
    require(proof['strict_calls']==value['strict_calls']==len(rows) and len(rows) in (1,3) and
        proof['full_reads']==value['full_reads'] and proof['rejected_read_count']==sum(not row['passed'] for row in rows),
        'Bounded strict-call count differs')
    if len(rows)==1:
        require(proof['mode']=='original-first-strict-pass' and module.strict_pass(rows[0],fixed,size) and proof['full_reads']==1,
            'Initial strict publication did not actually pass')
    else:
        mode=module.rejection_kind(rows[0],fixed,size)
        require(mode in ('before-read-timestamp-only-zero-bytes','full-read-timestamp-only') and proof['mode']==mode and
            not rows[0]['passed'] and proof['empty_digest_is_payload_candidate'] is False,
            'First rejection was broadened or relabelled')
        baseline=rows[0]['fd_after'];proposed=rows[0]['openssl_sha256'] if mode=='full-read-timestamp-only' else None
        for row in rows[1:]:
            expected=fixed or proposed
            require(module.strict_pass(row,expected,size,baseline),'Follow-up strict window failed its original identity/count/digest gate')
            if proposed is None:proposed=row['openssl_sha256']
            require(row['openssl_sha256']==proposed and (fixed is None or proposed==fixed),'Follow-up full views disagree')
        require(proposed==digest and proof['unpublished_proposed_sha256']==proposed and
            proof['full_reads']==(2 if mode.startswith('before-read') else 3),
            'Zero-byte failure was used as a payload digest or a complete read')
    if kind=='npy-propagator':
        header=proof['closed_npy_header']
        require(header['complete'] and header['passed'] and header['header_bytes']==128 and header['dtype']=='<c16' and
            header['shape']==list(module.PROP_SHAPE) and header['fortran_order'] is False,'Closed full12 NPY header proof missing')
    for item in proof['progress']:
        path=Path(item['path'])
        require(path.parent==receipt_path.parent,'Progress receipt escaped owned output audit')
        read(path,sha,item['sha256'])
    return {str(receipt_path):value['receipt_sha256']}


def stage_audit(attempt,stage,sha):
    data=read(Path(attempt)/'attempt.json',sha)
    row=data['stages'][stage];argv=row['argv']
    require(row['status']=='passed' and row['cleanup']['complete'] and argv.count('--audit-output')==1,
        'Actual stage was not a completed explicitly adapted command')
    result=Path(argv[argv.index('--audit-output')+1])
    require(result.resolve()==result and result.is_relative_to(Path(attempt).resolve()),'Stage checksum audit escaped its own attempt')
    return result


def verification(attempt,run,report,aux,sha,files,stage='independent'):
    module=core(aux,sha,files);audit=stage_audit(attempt,stage,sha)
    manifest=read(audit/'helper/manifest.json',sha,report['verification']['checksum_audit']['helper_manifest_sha256'])
    protocol=read(audit/'helper/protocol.json',sha)
    require(protocol['wrapper_sha256']==files['raw_scalar_helper_publication_v2.py'] and
        protocol['fresh_publication_module_sha256']==files['fresh_publication_v2.py'] and
        manifest['complete'] and manifest['passed'] and manifest['publication_module_sha256']==files['fresh_publication_v2.py'] and
        len(manifest['publications'])==1,'Actual fresh known-gauge helper route missing')
    verify=report['verification']
    gauge=Path(run)/verify['evidence_relative_path'];gauge=gauge.parent/'gauge.bin'
    result=publication(manifest['publications'][0],gauge,module.GAUGE_SHA,'canonical-gauge',audit/'helper',module,sha)
    result[str(audit/'helper/manifest.json')]=sha(audit/'helper/manifest.json')
    return result


def warm(attempt,run,report,aux,sha,files):
    module=core(aux,sha,files);audit=stage_audit(attempt,'benchmark',sha);result={}
    for rank in range(report['configuration']['ranks']):
        directory=audit.parent/(audit.name+'-fresh-publication-v2')/('rank%05d'%rank)
        manifest=read(directory/'manifest.json',sha);startup=read(directory/'startup.json',sha,manifest['startup_sha256'])
        require(manifest['complete'] and manifest['passed'] and manifest['protocol']==module.PROTOCOL and manifest['rank']==rank and
            manifest['entry_sha256']==files['raw_benchmark_publication_v2.py'] and
            manifest['base_wrapper_sha256']==files['raw_benchmark_v4.py'] and
            manifest['publication_module_sha256']==files['fresh_publication_v2.py'] and
            startup['numeric_and_clock_bodies_unchanged'] and startup['immutable_reader_unchanged'] and startup['mode']=='benchmark' and
            len(manifest['published_outputs'])==(1 if rank==0 else 0),'Actual new warm publication producer identity differs')
        for name,item in manifest['parent_raw_artifacts'].items():
            require(Path(item['path'])==audit/('rank%05d'%rank)/name,'Warm raw artifact link differs')
            read(item['path'],sha,item['sha256'])
        if rank==0:result.update(publication(manifest['published_outputs'][0],Path(run)/'propagator.npy',report['propagator_sha256'],
            'npy-propagator',directory,module,sha))
        result[str(directory/'manifest.json')]=sha(directory/'manifest.json')
    result.update(verification(attempt,run,report,aux,sha,files))
    return result


def cold(attempt,run,report,aux,sha,files):
    module=core(aux,sha,files);result={}
    for rank in range(report['configuration']['ranks']):
        directory=Path(attempt)/'checksum-audit/new-output-publication'/('rank%05d'%rank)
        protocol=read(directory/'protocol.json',sha);startup=read(directory/'startup.json',sha,protocol['startup_sha256'])
        require(protocol['complete'] and protocol['passed'] and protocol['protocol']==module.PROTOCOL and protocol['rank']==rank and
            protocol['entry_sha256']==files['phase7_cold_entry_v2.py'] and
            protocol['publication_module_sha256']==files['fresh_publication_v2.py'] and protocol['frozen_cold_and_clocks_unchanged'] and
            startup['frozen_adapter_sha256']==files['raw_cold_adapter.py'] and startup['immutable_reader_unchanged'] and
            protocol['publication_calls']==len(protocol['publications'])==(1 if rank==0 else 0),'Actual new cold publication producer identity differs')
        for name,item in protocol['parent_raw_artifacts'].items():
            require(Path(item['path'])==Path(attempt)/'checksum-audit/cold-runtime'/('rank%05d'%rank)/name,'Cold raw artifact link differs')
            read(item['path'],sha,item['sha256'])
        if rank==0:result.update(publication(protocol['publications'][0],Path(run)/'propagator.npy',report['propagator_sha256'],
            'npy-propagator',directory,module,sha))
        result[str(directory/'protocol.json')]=sha(directory/'protocol.json')
    result.update(verification(attempt,run,report,aux,sha,files))
    return result
