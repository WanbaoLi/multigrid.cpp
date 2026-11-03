#!/usr/bin/env python3
"""Read closed setup profiles; partition exclusive perf leaves without wall claims.

No perf, SSH, solver, compiler or scheduler is executed. Inputs stay unchanged;
--output must be a new directory outside the profile input. Optional closed-data
re-decodes need a manifest binding successful report argv and input/output SHA.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re

CATEGORIES = (
    'coarse_assembly', 'gram_schmidt', 'rng', 'hierarchy_impl',
    'coarse_solver_work', 'fine_sap_vcycle_work', 'gomp_runtime', 'mpi_runtime',
    'memory_container_ambiguous', 'setup_shared_ambiguous', 'other_resolved', 'unresolved_symbol')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for part in iter(lambda:stream.read(8*1024**2),b''):h.update(part)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def require(value,message):
    if not value:raise ValueError(message)


def parse_flat(text):
    require(not re.search(r'^#\s+Children\s+Self',text,re.M),'Inclusive Children/Self reports cannot be added as exclusive leaves')
    events = re.findall(r"^#\s+Samples:\s+(.+?)\s+of event\s+'([^']+)'",text,re.M)
    require(len(events)==1,'Exactly one perf event section is required')
    require(events[0][1]=='cycles:u','Expected cycles:u setup profile')
    lost = re.findall(r'^#\s+Total Lost Samples:\s*(\d+)',text,re.M)
    event_count = re.findall(r'^#\s+Event count \(approx\.\):\s*(\d+)',text,re.M)
    rows=[]
    for lineno,line in enumerate(text.splitlines(),1):
        match=re.match(r'^\s*(\d+(?:\.\d+)?)%\s+(.+)$',line)
        if not match:continue
        pct=float(match[1]);body=match[2]
        require(not re.match(r'\d+(?:\.\d+)?%',body),'Multiple percentage columns are not an exclusive flat report')
        marker=re.search(r'\[([.k?])\]\s*',body)
        if marker:
            prefix=body[:marker.start()].strip()
            symbol=re.split(r'\s{2,}',body[marker.end():].strip(),maxsplit=1)[0]
            dso=prefix or None
        else:
            # Unknown/perf versions may omit a marker. Keep it unresolved.
            dso=None;symbol=re.split(r'\s{2,}',body.strip(),maxsplit=1)[0]
        rows.append(dict(line=lineno,exclusive_percent=pct,dso=dso,symbol=symbol,
            symbol_resolved=bool(symbol and not re.match(r'^(?:0x[0-9a-fA-F]+|\[unknown\]|unknown)(?:\s|$)',symbol))))
    require(rows,'Nonempty exclusive flat rows required')
    total=sum(row['exclusive_percent'] for row in rows)
    require(total<=100.5,'Exclusive report exceeds rounding allowance; inspect duplicate/event sections')
    return dict(event=events[0][1],sample_count_header=events[0][0],
        sample_count_header_may_be_rounded=True,total_lost_samples=int(lost[0]) if len(lost)==1 else None,
        approximate_event_count=int(event_count[0]) if len(event_count)==1 else None,
        shown_exclusive_percent=total,unshown_or_rounding_percent=max(0.,100-total),rows=rows)


def category(row,proof=None):
    symbol=row['symbol'];dso=(row.get('dso') or '').lower();lower=symbol.lower()
    if proof:
        matched=[rule for rule in proof if rule['symbol']==symbol and
                 (rule.get('dso') is None or rule['dso']==row.get('dso'))]
        require(len(matched)<=1,'More than one source proof applies to an exclusive leaf')
        if matched:return matched[0]['category'],'explicit source/disassembly proof: '+matched[0]['reason']
    if 'libgomp' in dso or re.search(r'\b(?:GOMP_|gomp_|omp_)',symbol):
        return 'gomp_runtime','Runtime identity; includes waits, scheduling and useful runtime work, not all recoverable wall'
    if any(value in dso for value in ('libmpi','mca_','libucp','libuct','libucs','libucg','libucc','libopen-pal')) or re.search(r'\b(?:MPI_|PMPI_|ompi_|opal_|ucp_|ucg_)',symbol):
        return 'mpi_runtime','MPI/transport leaf; no assumption that entire leaf is wait'
    if any(value in symbol for value in ('assemble_local_block','rebuild_coarse_operator')):
        return 'coarse_assembly','Direct assembly/rebuild symbol; called allocator leaves remain separate'
    if any(value in lower for value in ('gram_schmidt','gramschmidt','orthonormaliz')):
        return 'gram_schmidt','Explicit orthogonalization symbol'
    if any(value in lower for value in ('normal_distribution','mersenne_twister','generate_canonical','mt19937')):
        return 'rng','Explicit random generator/distribution symbol; generic log/sqrt remain unassigned'
    if 'NativeMG::Impl::Impl' in symbol or 'NativeMG::Impl::~Impl' in symbol:
        return 'hierarchy_impl','Direct hierarchy constructor/destructor leaf only'
    container_leaf=(symbol.startswith(('std::','__gnu_cxx::')) and
                    any(value in symbol for value in ('_Rb_tree','map<','vector<','allocator<')))
    if container_leaf or any(value in symbol for value in ('operator new','operator delete')) or re.search(r'\b(?:malloc|calloc|realloc|free|memset|memcpy|memmove|_int_malloc|_int_free)\b',symbol):
        return 'memory_container_ambiguous','Requires sample callchain/source evidence to assign to assembly, GS or Impl'
    if any(value in symbol for value in ('coarse_','coarse::')) and ('NativeMG' in symbol or 'lqcd_native' in symbol or 'coarse_gcr' in symbol):
        return 'coarse_solver_work','Coarse kernels during setup; adaptive/validation caller needs callgraph'
    if 'NativeMG::Impl::' in symbol and any(value in lower for value in ('vcycle','sap','fine_','local_range','clover_range','apply_double','encode','decode')):
        return 'fine_sap_vcycle_work','Fine/SAP/V-cycle kernel; homogeneous/adaptive/validation context may overlap'
    if 'generate_basis' in symbol:
        return 'setup_shared_ambiguous','Function contains RNG, normalization, Gram-Schmidt and pass orchestration; clone number is not proof'
    if not row['symbol_resolved']:
        return 'unresolved_symbol','No leaf symbol; DSO may still be known'
    return 'other_resolved','Resolved leaf outside conservative rules'


def load_proof(path):
    if not path:return [],None
    data=read(path);rules=data['rules']
    for rule in rules:
        require(rule['category'] in CATEGORIES,'Unknown source-proof category')
        require(rule.get('symbol') and rule.get('reason'),'Source proof needs exact symbol and reason')
        evidence=(path.parent/rule['evidence']).resolve()
        require(evidence.is_file() and sha(evidence)==rule['evidence_sha256'],'Source attribution evidence SHA differs')
        require(re.fullmatch('[0-9a-f]{64}',rule['library_sha256']),'Source proof must bind measured library SHA')
    return rules,dict(path=str(path.resolve()),sha256=sha(path))


def decoded_flat(decoded,rank,meta,summary_sha):
    manifest=read(decoded/'decode-manifest.json')
    require(manifest.get('complete') is True and manifest.get('closed_setup_summary_sha256')==summary_sha,
        'Additional decode needs a closed original setup summary SHA')
    evidence=manifest['ranks'][str(rank)]
    require(evidence.get('returncode')==0 and '--no-children' in evidence.get('argv',[]) and
        evidence.get('perf_data_sha256')==meta['perf_data_sha256'],'Additional decode did not prove success on original closed raw record')
    name=evidence['flat_file'];require(Path(name).name==name,'Additional decode flat filename must be one component')
    path=decoded/name;require(sha(path)==evidence['flat_sha256'],'Additional decoded report SHA differs')
    return path,dict(kind='successful additional exclusive decode',manifest_sha256=sha(decoded/'decode-manifest.json'),**evidence)


def analyze(profile,cold_report=None,decoded=None,proof_path=None,hash_raw=False):
    summary_path=profile/'setup-profile-summary.json';summary=read(summary_path)
    require(summary.get('complete') is True and summary.get('passed') is True,'Setup profile must be closed and passed before analysis')
    selected=summary['selected_ranks'];require(set(selected)=={0,8},'Expected completed ranks0/8 setup record')
    rules,proof_meta=load_proof(proof_path)
    cold=read(cold_report) if cold_report else None
    if cold:
        require(cold.get('complete') is True and cold.get('measurements_complete') is True and
                cold.get('timing_scope')=='profile_cold_canonical_fixture_to_first12','Cold report must remain completed diagnostic scope')
        verification=cold.get('verification',{})
        require(verification.get('complete') is True and verification.get('passed') is True and
                verification.get('columns')==12 and 0<=verification.get('max_true_residual',float('inf'))<=1e-8 and
                0<=verification.get('solution_relative_error',float('inf'))<=1e-6,
                'Provided cold report must finish unchanged independent12 residual/solution gates')
        require(cold.get('prepared_gauge_sha256')=='126d658999367b0ece3801c61cd143542d7db0dddc37ab60e6e668e18faa6834',
                'Provided cold report must match frozen canonical gauge bytes')
        for rule in rules:require(rule['library_sha256']==cold['library_sha256'],'Source proof belongs to another measured binary')
    else:require(not rules,'Source proof requires cold report with measured library SHA')
    out=dict(complete=True,diagnostic=True,rank_eligible=False,
        scope='Solver.setup only; exclusive cycles:u event shares on sampled ranks, not wall fractions',
        summary_sha256=sha(summary_path),source_proof=proof_meta,ranks={},
        warnings=['Never sum inclusive parents with their leaf costs; every shown leaf belongs to exactly one category.',
                  'Rank0 andrank8 are separate observations, not two terms of a node-wide wall sum.',
                  'Cycles shares are not elapsed-wall shares; GOMP runtime is not wholly removable wait.',
                  'Profiler attach/flush/decode lies inside diagnostic cold timing around the instrumented setup method; no performance ranking.'])
    for rank in selected:
        stem=profile/f'rank{rank:05d}';meta_path=stem.with_suffix('.setup-profile.json');meta=read(meta_path)
        require(meta.get('complete') is True and meta.get('passed') is True and meta.get('selected') is True and
                meta.get('solver_completed') is True and meta['rank']==rank,'Selected rank setup record not closed/passed')
        require(meta.get('record_returncode')==0 or
                (meta.get('record_returncode')==-2 and meta.get('stop_requested_sigint') is True),
                'perf record exit was not success or explicitly requested SIGINT')
        require('--no-children' in meta['report_argv'],'Original flat decode must explicitly disable inclusive children')
        flat=stem.with_suffix('.perf-flat.txt');require(sha(flat)==meta['flat_report_sha256'],'Original flat SHA differs')
        decode=dict(kind='original successful wrapper decode',argv=meta['report_argv'],
                    acceptance='passed wrapper requires nonempty raw data and report rc0',flat_sha256=meta['flat_report_sha256'])
        if decoded:flat,decode=decoded_flat(decoded,rank,meta,out['summary_sha256'])
        data=parse_flat(flat.read_text(errors='replace'))
        log=stem.with_suffix('.perf-record.log').read_text(errors='replace')
        exact=re.findall(r'\((\d+) samples\)',log)
        raw=stem.with_suffix('.perf.data')
        raw_evidence=dict(recorded_sha256=meta['perf_data_sha256'],present=raw.is_file(),sha256_checked=False)
        if raw.is_file():raw_evidence['bytes']=raw.stat().st_size
        if hash_raw:
            require(raw.is_file() and sha(raw)==meta['perf_data_sha256'],'Closed raw data missing or SHA changed')
            raw_evidence['sha256_checked']=True
        grouped=defaultdict(float);resolution=defaultdict(float)
        for row in data['rows']:
            row['category'],row['attribution_reason']=category(row,rules)
            grouped[row['category']]+=row['exclusive_percent']
            resolution['symbol_resolved' if row['symbol_resolved'] else 'symbol_unresolved']+=row['exclusive_percent']
        result=dict(rank=rank,metadata_sha256=sha(meta_path),decode=decode,raw_data=raw_evidence,
            exact_record_samples=int(exact[0]) if len(exact)==1 else None,
            categories={key:grouped[key] for key in CATEGORIES},resolution=dict(resolution),flat_report_path=str(flat),
            setup_python_wall_seconds=meta.get('setup_python_wall_seconds'),native_return_seconds=meta.get('native_return_seconds'),
            resource_before=meta.get('resource_before'),resource_after=meta.get('resource_after'),**data)
        runtime=stem.with_suffix('.runtime.json')
        if runtime.is_file():
            environment=read(runtime)
            result['runtime']=dict(sha256=sha(runtime),host=environment.get('host'),task_count=environment.get('task_count'),
                allowed_cpus=environment.get('allowed_cpus'),tuning_environment=environment.get('tuning_environment'),
                selected_libraries=[row for row in environment.get('mapped_libraries',[]) if
                    any(name in row.get('mapped_path','') for name in ('liblqcd','libgomp','libstdc++','libkupl','libmpi'))])
        out['ranks'][str(rank)]=result
        if data['total_lost_samples'] is None:out['warnings'].append(f'Rank{rank} has no exact lost-sample header; absence is not zero.')
        if not any(row.get('dso') for row in data['rows']):out['warnings'].append(f'Rank{rank} has no DSO column; unresolved addresses cannot be assigned toGOMP without successful closed-data re-decode.')
    if cold:
        out['cold_report']=dict(path=str(cold_report),sha256=sha(cold_report),timing_scope=cold['timing_scope'],
            cold_wall_seconds=cold.get('cold_wall_seconds'),first12_api_seconds=cold.get('first12_api_seconds'),
            phases=cold.get('phases'),library_sha256=cold.get('library_sha256'),
            source_manifest_sha256=cold.get('source_manifest_sha256'),verification=cold.get('verification'))
    return out


def markdown(data):
    lines=['Closed setup profile: exclusive cycles:u attribution, diagnostic only.','',
           '| Category | Rank0 exclusive % | Rank8 exclusive % |','|---|---:|---:|']
    for key in CATEGORIES:
        lines.append(f"| {key} | {data['ranks']['0']['categories'][key]:.2f} | {data['ranks']['8']['categories'][key]:.2f} |")
    lines+=['','| Evidence | Rank0 | Rank8 |','|---|---:|---:|']
    for label,key in [('Actual record sample count','exact_record_samples'),('Lost samples header','total_lost_samples'),
                      ('Shown exclusive percent','shown_exclusive_percent'),('Setup Python wall, diagnosticseconds','setup_python_wall_seconds')]:
        lines.append(f"| {label} | {data['ranks']['0'].get(key)} | {data['ranks']['8'].get(key)} |")
    lines+=['','Ambiguous std::map/allocator, generate_basis and unresolved addresses retain their own categories. ',
            'Any later source/callgraph attribution must bind the exact measured library and count each exclusive leaf once.','']
    for warning in data['warnings']:lines.append('- '+warning)
    for rank in ('0','8'):
        lines+=['',f'Rank{rank} top exclusive leaves:','', '| Exclusive % | Category | DSO | Symbol |','|---:|---|---|---|']
        for row in sorted(data['ranks'][rank]['rows'],key=lambda row:-row['exclusive_percent'])[:25]:
            escape=lambda value:str(value or '').replace('|','\\|')
            lines.append(f"| {row['exclusive_percent']:.2f} | {row['category']} | {escape(row['dso'])} | {escape(row['symbol'])} |")
    return '\n'.join(lines)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',type=Path,required=True)
    parser.add_argument('--cold-report',type=Path)
    parser.add_argument('--decoded-dir',type=Path)
    parser.add_argument('--source-proof',type=Path)
    parser.add_argument('--hash-raw',action='store_true',help='Optional full read of closed raw data, no perf execution')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();profile=args.profile.resolve();output=args.output.resolve()
    require(not output.exists() and not output.is_relative_to(profile),'Fresh output outside profile input required')
    data=analyze(profile,args.cold_report,args.decoded_dir,args.source_proof,args.hash_raw)
    output.mkdir(parents=True)
    (output/'analysis.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
    (output/'report.md').write_text(markdown(data))
    (output/'analysis-manifest.json').write_text(json.dumps({name:sha(output/name) for name in ('analysis.json','report.md')},indent=2)+'\n')
    print(json.dumps(dict(complete=True,output=str(output),rank_eligible=False)))


if __name__=='__main__':main()
