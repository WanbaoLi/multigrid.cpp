"""Read-only per-case publication closure for single/dual-case HaloV2 stages."""
from pathlib import Path
import re

import owned_publication_audit_v3 as single

require=single.require
read=single.read


def case_ids(plan,reports):
    cases=plan.get('cases',[])
    names=[row.get('id') for row in cases]
    require(names and all(isinstance(name,str) and re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,63}',name) for name in names)
        and len(set(names))==len(names),'Every startup plan case must be safe and unique')
    require(isinstance(reports,dict) and set(reports)==set(names),'No omitted or extra case publication/verification report allowed')
    ranks={row['configuration']['ranks'] for row in reports.values()}
    require(len(ranks)==1 and all(type(value)is int and 0<value<1024 for value in ranks),'Case rank counts differ')
    return names,ranks.pop()


def warm(attempt,plan,reports,aux,sha,files,stage='benchmark'):
    """Bind all outputs to one exact plan, producer stage and fresh case verifier."""
    require(stage in ('benchmark','diagnostic'),'Only explicit warm producer scopes allowed')
    attempt=Path(attempt).resolve();plan_path=attempt/'plan.json'
    names,ranks=case_ids(plan,reports)
    plan_sha=sha(plan_path);require(read(plan_path,sha,plan_sha)==plan,'Completed producer plan changed')
    module=single.core(aux,sha,files);audit=single.stage_audit(attempt,stage,sha)
    data=read(attempt/'attempt.json',sha);argv=list(map(str,data['stages'][stage]['argv']))
    def option(flag):
        require(argv.count(flag)==1 and argv.index(flag)+1<len(argv),'Exactly one actual '+flag+' required')
        return argv[argv.index(flag)+1]
    require(data['stages'][stage]['returncode']==0 and not data['stages'][stage]['cleanup'].get('surviving_pids') and
        Path(option('--plan'))==plan_path and Path(option('--output'))==attempt/'measurements' and
        Path(option('--benchmark')).name=='bench_full12.py' and
        option('--expected-wrapper-sha')==files['raw_benchmark_publication_v2.py'],
        'Actual stage plan/output/producer route differs')
    targets={str(attempt/'measurements'/name/'propagator.npy'):name for name in names}
    declaration=[dict(relative=name+'/propagator.npy',kind='npy-propagator',expected_sha256=None,bytes=module.PROP_BYTES) for name in names]
    result={str(plan_path):plan_sha};seen=set()
    for rank in range(ranks):
        directory=audit.parent/(audit.name+'-fresh-publication-v2')/('rank%05d'%rank)
        manifest=read(directory/'manifest.json',sha)
        startup=read(directory/'startup.json',sha,manifest['startup_sha256'])
        require(manifest['complete'] and manifest['passed'] and manifest['protocol']==module.PROTOCOL and manifest['rank']==rank and
            manifest['entry_sha256']==files['raw_benchmark_publication_v2.py'] and
            manifest['base_wrapper_sha256']==files['raw_benchmark_v4.py'] and
            manifest['publication_module_sha256']==files['fresh_publication_v2.py'] and
            startup['numeric_and_clock_bodies_unchanged'] and startup['immutable_reader_unchanged'] and
            startup['mode']=='benchmark' and startup['rank']==rank and
            len(manifest['published_outputs'])==(len(names) if rank==0 else 0),
            'Completed single/dual-case producer identity or publication count differs')
        require(set(manifest['parent_raw_artifacts'])=={'protocol.json','manifest.json'},'Both frozen parent artifacts required')
        for name,item in manifest['parent_raw_artifacts'].items():
            require(Path(item['path'])==audit/('rank%05d'%rank)/name,'Actual parent raw scope differs')
            parent=read(item['path'],sha,item['sha256'])
            require(parent['complete'],'Frozen parent artifact did not complete')
            result[item['path']]=item['sha256']
        if rank==0:
            require(startup['plan']==dict(path=str(plan_path),sha256=plan_sha,cases=names) and
                startup['eligibility']['output']==str(attempt/'measurements') and
                startup['eligibility']['declarations']==declaration,'Startup plan/declarations differ from every measured case')
            for value in manifest['published_outputs']:
                target=value['full_proof']['path']
                require(target in targets and target not in seen,'Omitted/extra/duplicate published case')
                seen.add(target);case=targets[target]
                require(value['full_proof']['eligibility']==startup['eligibility'],'Receipt was not derived from the same startup plan')
                require(value['parent_protocol']['path']==str(audit/'rank00000/protocol.json') and
                    value['parent_protocol']['startup_path']==str(directory/'startup.json'),
                    'Per-case receipt parent/startup route differs')
                result.update(single.publication(value,target,reports[case]['propagator_sha256'],
                    'npy-propagator',directory,module,sha))
        else:require(startup['plan'] is None and startup['eligibility'] is None,'Nonroot invented producer eligibility')
        result[str(directory/'manifest.json')]=sha(directory/'manifest.json')
        result[str(directory/'startup.json')]=manifest['startup_sha256']
    require(seen==set(targets),'Every declared case must publish exactly once')
    for name in names:
        run=attempt/'measurements'/name;report=reports[name]
        require(read(run/'result.json',sha)==report,'Case report view changed')
        result[str(run/'result.json')]=sha(run/'result.json')
        result.update(single.verification(attempt,run,report,aux,sha,files,stage='verify-'+name))
    return result
