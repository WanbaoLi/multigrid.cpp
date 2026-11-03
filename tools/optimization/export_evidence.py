#!/usr/bin/env python3
"""Export a small, read-only campaign evidence snapshot (stdlib only).

This copies evidence, not numerical verification. Arrays, build trees, raw perf
data and private environment values are omitted; every transformation is named.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tarfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import campaign as ledger

REDACTED = '[REDACTED: private environment/credential]'
SAFE_ENV = set('PATH LD_LIBRARY_PATH LIBRARY_PATH CPATH C_INCLUDE_PATH CPLUS_INCLUDE_PATH '
    'PKG_CONFIG_PATH CMAKE_PREFIX_PATH CC CXX FC CFLAGS CXXFLAGS LDFLAGS PYTHONPATH '
    'OMP_NUM_THREADS OMP_PLACES OMP_PROC_BIND OMP_WAIT_POLICY OMP_DYNAMIC OMP_THREAD_LIMIT '
    'OMP_MAX_ACTIVE_LEVELS OMP_DISPLAY_ENV OMP_DISPLAY_AFFINITY OMP_STACKSIZE '
    'GOMP_CPU_AFFINITY GOMP_SPINCOUNT KMP_AFFINITY KMP_BLOCKTIME '
    'OPENBLAS_NUM_THREADS MKL_NUM_THREADS BLIS_NUM_THREADS VECLIB_MAXIMUM_THREADS '
    'LQCD_MPI_FLAGS LQCD_EXPERIMENT_KUPL_ROOT LQCD_EXPERIMENT_CXX_RUNTIME '
    'LQCD_CPU_LIBRARY LQCD_RHS_BATCH LQCD_VERBOSE LQCD_HALO_PROFILE LQCD_HBW '
    'LQCD_HBM LQCD_GCR_FUSED LQCD_GCR_CGS2 LQCD_COARSE_BATCH_REDUCE '
    'LQCD_COARSE_THREADS LQCD_COARSE_OVERLAP LQCD_SVE_REUSE LQCD_BATCH_SVE_REUSE '
    'LQCD_SAP_THREADS LQCD_SAP_EO LQCD_COARSE_EO LQCD_COARSE_SVE_REUSE '
    'LQCD_MG_SAP_STEPS LQCD_MG_SAP_CYCLES LQCD_MG_COARSE_IT LQCD_MG_COARSE_TOL '
    'LQCD_CORRECTION_BASE_TOL LQCD_FLOAT_CORRECTION_VERIFY LQCD_FINE_TEAM_FUSED '
    'LQCD_COARSE_CGS2 LQCD_RESTRICT_FLOAT LQCD_LOCAL_CONTIGUOUS LQCD_ARM_SVE '
    'LQCD_ARM_SVE_PLANNED LQCD_ARM_SVE_REUSE LQCD_ARM_SVE_TRANSFER LQCD_COARSE_FUSED '
    'LQCD_ARM_COARSE_SVE LQCD_HBW_ALLOC LQCD_COARSE_SPATIAL_OVERLAP '
    'LQCD_SETUP_UPDATE LQCD_ADAPTIVE_CORRECTION LQCD_HALO_OVERLAP '
    'LQCD_OPT_TASK_ID LQCD_OPT_STAGE_ID LQCD_HBW_VERIFY LQCD_HBW_NODES '
    'UCX_TLS UCX_NET_DEVICES UCX_MEMTYPE_CACHE MPI_THREAD_LEVEL '
    'PERF_COUNTER_ROOT LD_PRELOAD'.split())
PRIVATE = re.compile(r'(?:password|passwd|secret|credential|private[_-]?key|api[_-]?key|'
                     r'access[_-]?token|auth(?:orization)?|(?:^|[_-])token(?:$|[_-]))', re.I)
ASSIGNMENT = re.compile(r'''(?ix)([\w.-]*(?:password|passwd|secret|credential|private[_-]?key|api[_-]?key|token)[\w.-]*["']?\s*[:=]\s*)(["'][^"'\r\n]*["']|[^\s,;}]+)''')
BEARER = re.compile(r'(?i)(\bBearer\s+)[A-Za-z0-9._~+/-]+=*')
ACTIVE = {'running'}
TERMINAL = {'measured', 'best', 'failed', 'timeout', 'cleanup_failed', 'blocked',
            'inconclusive', 'rejected', 'interrupted'}


def safe_relative(name):
    value = PurePosixPath(str(name).replace('\\', '/'))
    if value.is_absolute() or '..' in value.parts or not value.parts or ':' in value.parts[0]:
        raise ValueError(f'Unsafe evidence path: {name}')
    return Path(*value.parts)


def sensitive_name(name):
    parts = [part.lower() for part in Path(name).parts]
    return any(part in {'.env', '.ssh', '.netrc', '.git-credentials', 'credentials',
                        'id_rsa', 'id_ed25519'} or part.endswith(('.pem', '.key'))
               or part.startswith('.env.') for part in parts)


def redact(value, environment=False):
    if isinstance(value, dict):
        result = {}
        for key, child in value.items():
            private = PRIVATE.search(str(key)) and key != 'history_read_token'
            if private or (environment and key not in SAFE_ENV):
                result[key] = REDACTED
            else:
                env = key in {'env', 'environ', 'environment', 'env_overrides'} or str(key).endswith('_environment')
                result[key] = redact(child, env)
        return result
    if isinstance(value, list):
        result, hide_next = [], False
        for child in value:
            if hide_next:
                result.append(REDACTED)
                hide_next = False
            else:
                result.append(redact(child))
                hide_next = isinstance(child, str) and child.startswith('--') and bool(PRIVATE.search(child)) and '=' not in child
        return result
    if isinstance(value, str):
        return BEARER.sub(r'\1[REDACTED]', ASSIGNMENT.sub(lambda m: m[1] + REDACTED, value))
    return value


def metadata(root):
    return sorted([*root.glob('campaign.json'), *root.glob('best.json'),
        *root.glob('history-read.json'), *root.glob('attempts/*/attempt.json'),
        *root.glob('events/*.json'), *root.glob('best-history/*.json')])


def fingerprint(paths):
    return {str(p): ledger.digest(p) if p.is_file() and not p.is_symlink() else None for p in paths}


def archive_check(path, manifest):
    if any(p.is_symlink() for p in (path,*path.parents)):
        raise ValueError('Archive symlink is never followed')
    expected = {row['path']: row for row in manifest['files'] if not row.get('deleted')}
    found = set()
    with tarfile.open(path, 'r:gz') as archive:
        for member in archive:
            safe_relative(member.name)
            if not member.isfile() or member.name not in expected or member.name in found:
                raise ValueError('Archive contains unexpected/link/duplicate members')
            if sensitive_name(member.name):
                raise ValueError('Archive contains an environment/credential file; original archive omitted')
            if Path(member.name).suffix in {'.npy','.npz'} or Path(member.name).name.startswith('perf.data'):
                raise ValueError('Source archive contains scientific arrays/raw perf data; original omitted')
            row = expected[member.name]
            if member.size != row['bytes']:
                raise ValueError('Archive member size differs from source manifest')
            stream = archive.extractfile(member)
            h = hashlib.sha256()
            size = 0
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                size += len(chunk)
                h.update(chunk)
            if size != row['bytes'] or h.hexdigest() != row['sha256']:
                raise ValueError('Archive contents differ from source manifest')
            found.add(member.name)
    if found != set(expected):
        raise ValueError('Archive is missing source manifest files')


class Exporter:
    def __init__(self, root, output, completed_only=True, max_log_bytes=131072,
                 max_total_bytes=268435456):
        self.root, self.output = Path(root).resolve(), Path(output).resolve()
        self.completed_only, self.max_log_bytes = completed_only, max_log_bytes
        self.max_total_bytes, self.total = max_total_bytes, 0
        self.entries, self.errors, self.reads, self.attempts = [], [], {}, []
        self.changed_during_reads = set()
        self.verification_candidates = None

    def item(self, source, reason=None):
        row = dict(source_path=str(Path(source).absolute()), included=False, sha256=None)
        try:
            row['bytes'] = Path(source).lstat().st_size
        except OSError:
            row['bytes'] = None
        if reason:
            row['excluded_reason'] = reason
        self.entries.append(row)
        return row

    def read(self, source):
        source = Path(source)
        if any(p.is_symlink() for p in (source,*source.parents)) or not source.is_file():
            raise ValueError(f'Not a regular evidence file: {source}')
        raw = source.read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        previous = self.reads.setdefault(str(source),actual)
        if previous != actual:
            self.changed_during_reads.add(str(source))
        return raw

    def linked_verification(self, expected, evidence_relative_path='independent/verification.json'):
        """Interleaved child reports may reference their parent's run directory.

        Read only small verifier JSON; copy only an exact registered digest and
        its column logs, even when the containing parent campaign is ongoing.
        No completion is inherited from that parent or its raw result.
        """
        relative_evidence = safe_relative(evidence_relative_path).as_posix()
        if Path(relative_evidence).name != 'verification.json':
            raise ValueError('Independent evidence path must identify verification.json')
        if self.verification_candidates is None:
            self.verification_candidates = []
            for directory, directories, names in os.walk(self.root/'attempts',followlinks=False):
                directories[:] = [name for name in directories if name not in
                    {'source','build','artifacts','__pycache__','.git'} and not (Path(directory)/name).is_symlink()]
                if 'verification.json' in names:
                    self.verification_candidates.append(Path(directory)/'verification.json')
        for target in self.verification_candidates:
            if not target.as_posix().endswith('/'+relative_evidence):
                continue
            try:
                raw = self.read(target)
                if hashlib.sha256(raw).hexdigest() != expected:
                    continue
                independent = json.loads(raw)
                relative = target.relative_to(self.root).as_posix()
                self.write(target,'campaign/'+relative,'json',expected=expected)
                for index in range(12):
                    for name in [f'column{index}.log',f'verified{index}.residual']:
                        source = target.parent/name
                        if source.is_file():
                            self.write(source,'campaign/'+source.relative_to(self.root).as_posix(),'text')
                return target, independent
            except (OSError,ValueError):
                continue
        return None

    def write(self, source, relative, kind='raw', expected=None):
        source = Path(source)
        row = self.item(source)
        try:
            if any(p.is_symlink() for p in (source,*source.parents)) or not source.is_file():
                raise ValueError('Symlink/missing/nonregular evidence is never followed')
            if sensitive_name(source.name):
                raise ValueError('Environment/credential file')
            # Big scientific payloads cannot enter through a misleading extension.
            if kind == 'raw' and source.stat().st_size > self.max_total_bytes:
                raise ValueError('File exceeds total export budget')
            raw = self.read(source)
            original_sha = hashlib.sha256(raw).hexdigest()
            row.update(sha256=original_sha, bytes=len(raw))
            if expected and original_sha != expected:
                raise ValueError('Original evidence SHA256 differs from ledger/report')
            exported = raw
            transformations = []
            if kind == 'json':
                value = json.loads(raw, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
                cleaned = redact(value)
                if cleaned != value:
                    exported = ledger.canonical(cleaned)
                    transformations.append('private fields/environment values redacted; original digest is not export digest')
            elif kind == 'text':
                cleaned = redact(raw.decode('utf-8', errors='replace'))
                exported = cleaned.encode('utf-8')
                if exported != raw:
                    transformations.append('credential assignments redacted or non-UTF8 replaced')
                if len(exported) > self.max_log_bytes:
                    count = max(0, (self.max_log_bytes - 64) // 2)
                    exported = exported[:count] + b'\n[EXPORT EXCERPT: middle omitted; see original SHA256]\n' + exported[-count:]
                    transformations.append('head/tail excerpt; full original omitted')
            if self.total + len(exported) > self.max_total_bytes:
                raise ValueError('Total export budget exhausted')
            relative = safe_relative(relative)
            target = self.output / relative
            if target.exists():
                if ledger.digest(target) != hashlib.sha256(exported).hexdigest():
                    raise ValueError('Conflicting export destination')
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(exported)
                self.total += len(exported)
            row.update(included=True, export_path=relative.as_posix(),
                export_sha256=hashlib.sha256(exported).hexdigest(), export_bytes=len(exported),
                transformations=transformations)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            row['excluded_reason'] = str(exc)
            self.errors.append(dict(path=str(source), error=str(exc)))
        return row

    def copy_archive(self, path, data):
        try:
            manifest_path = path / 'source-manifest.json'
            manifest = json.loads(self.read(manifest_path))
            if ledger.digest(manifest_path) != data['snapshot']['source_manifest_sha256']:
                raise ValueError('Source manifest differs from attempt snapshot')
            archive = path / 'source.tar.gz'
            archive_check(archive, manifest)
            result = self.write(archive, 'archives/' + data['snapshot']['archive_sha256'] + '.tar.gz',
                                expected=data['snapshot']['archive_sha256'])
            return manifest, result
        except (OSError, ValueError, KeyError, TypeError, tarfile.TarError) as exc:
            self.item(path/'source.tar.gz', str(exc))
            self.errors.append(dict(path=str(path), error=str(exc)))
            return None, None

    def verification_review(self, path, data, report, files):
        result = dict(registered_report_contract=False, complete_review_material=False,
                      numerical_verification_rerun=False, errors=[])
        try:
            if not data.get('report'):
                raise ValueError('No ingested report; raw/diagnostic evidence is not completed')
            if ledger.object_digest(report) != data['report']['sha256']:
                raise ValueError('Registered report identity changed')
            result['samples_summary'] = ledger.validate_report(report, self.config,
                data['snapshot']['source_manifest_sha256'])
            result['registered_report_contract'] = True
            relative_evidence = safe_relative(report['verification'].get('evidence_relative_path',
                'independent/verification.json')).as_posix()
            if Path(relative_evidence).name != 'verification.json':
                raise ValueError('Independent evidence path must identify verification.json')
            matching = []
            for target in files:
                if target.as_posix().endswith('/'+relative_evidence):
                    raw = self.read(target)
                    if hashlib.sha256(raw).hexdigest() == report['verification'].get('evidence_sha256'):
                        matching.append((target, json.loads(raw)))
            if not matching:
                linked = self.linked_verification(report['verification'].get('evidence_sha256'),relative_evidence)
                if linked:
                    matching.append(linked)
                else:
                    raise ValueError('Original independent verification.json absent or digest mismatch')
            target, independent = matching[0]
            columns = independent.get('columns', [])
            identities = {(x['source_spin'], x['source_color']) for x in columns}
            if independent.get('complete') is not True or len(columns) != 12 or identities != {(s,c) for s in range(4) for c in range(3)}:
                raise ValueError('Independent verification does not cover exactly 12 columns')
            if independent.get('reference_sha256') != self.config['reference_sha256'] or independent.get('propagator_sha256') != report['verification'].get('propagator_sha256'):
                raise ValueError('Independent reference/propagator identity differs')
            if any(not isinstance(x['residual'], (int,float)) or not math.isfinite(x['residual']) or not 0 <= x['residual'] <= self.config['residual_limit'] for x in columns):
                raise ValueError('Independent residual contract failed')
            column_logs = [target.parent/f'column{i}.log' for i in range(12)]
            exported = {row['source_path']: row for row in self.entries if row['included']}
            if any(str(p) not in exported or exported[str(p)]['transformations'] for p in column_logs):
                raise ValueError('Twelve complete untransformed column logs are not all exported')
            by_column = {x['source_spin']*3+x['source_color']:x['residual'] for x in columns}
            for index, log in enumerate(column_logs):
                matches = re.findall(r'true relative residual\s+(\S+)',self.read(log).decode('utf-8'))
                if not matches or not math.isclose(float(matches[-1]),by_column[index],rel_tol=1e-12,abs_tol=0):
                    raise ValueError('Column log residual differs from independent verification')
            result.update(complete_review_material=True, independent_path=str(target), columns=columns,
                          unbundled_arrays_rehashed=False)
        except (OSError, ValueError, KeyError, TypeError, ledger.EvidenceError) as exc:
            result['errors'].append(str(exc))
        return result

    def run(self):
        if self.output.exists():
            raise ValueError('Refusing to overwrite export output')
        initial_config = self.read(self.root/'campaign.json')
        initial_config_sha = hashlib.sha256(initial_config).hexdigest()
        self.config = json.loads(initial_config)
        protected = [self.root, Path(self.config['reference_skill']).resolve()]
        protected += [p.resolve() for p in (self.root/'attempts').glob('*/source')]
        if any(self.output.is_relative_to(p) for p in protected):
            raise ValueError('Export output must be outside ledger, frozen source and reference trees')
        self.output.mkdir(parents=True)
        before = fingerprint(metadata(self.root))
        for path in metadata(self.root):
            self.write(path, 'campaign/'+path.relative_to(self.root).as_posix(), 'json')
        self.best = json.loads(self.read(self.root/'best.json')) if (self.root/'best.json').is_file() else None
        paths = sorted((self.root/'attempts').iterdir(),key=lambda p:(not self.best or self.best.get('attempt')!=p.name,p.name))
        for path in paths:
            if path.is_symlink() or not path.is_dir():
                self.item(path, 'Nonregular attempt directory')
                continue
            try:
                data = json.loads(self.read(path/'attempt.json'))
            except (OSError, ValueError) as exc:
                self.errors.append(dict(path=str(path), error=str(exc)))
                continue
            active = any(stage.get('status') in ACTIVE for stage in data.get('stages',{}).values())
            payload = not active and (not self.completed_only or data.get('status') in TERMINAL)
            row = dict(id=path.name, status=data.get('status'), running_checkpoint=active,
                       payload_included=payload, registered=bool(data.get('report')))
            self.attempts.append(row)
            files = []
            for directory, directories, names in os.walk(path, followlinks=False):
                for name in list(directories):
                    target = Path(directory)/name
                    if name in {'source','build','artifacts','__pycache__','.git'} or target.is_symlink():
                        self.item(target, 'Source exported by manifest/archive; build/artifacts/cache trees not traversed')
                        directories.remove(name)
                for name in sorted(names):
                    target = Path(directory)/name
                    if target == path/'attempt.json':
                        continue
                    relative = target.relative_to(self.root).as_posix()
                    if name in {'source.tar.gz'}:
                        if not payload:
                            self.item(target,'Active/unfinished source archive excluded; manifest retained')
                        continue
                    if name in {'proposal.json','plan.json','source-manifest.json','source.diff','git-status.txt'}:
                        kind = 'json' if target.suffix == '.json' else 'text'
                    elif not payload:
                        self.item(target, 'Active/unfinished payload excluded by completed-only policy')
                        continue
                    elif target.suffix in {'.json','.log','.residual'}:
                        kind = 'json' if target.suffix == '.json' else 'text'
                    else:
                        excluded = self.item(target, 'Large arrays/binaries/raw perf/unknown payload excluded; bytes not rehashed')
                        excluded['hash_recomputed'] = False
                        continue
                    self.write(target, 'campaign/'+relative, kind)
                    files.append(target)
            report = {}
            if data.get('report') and payload:
                try:
                    report = json.loads(self.read(path/'report.json'))
                except (OSError, ValueError) as exc:
                    row['report_read_error'] = str(exc)
            # Expected array digests are declarations from the original report,
            # not hashes computed by this collector. Never stream giant arrays.
            for excluded in self.entries:
                original = Path(excluded['source_path'])
                if not excluded['included'] and original.is_relative_to(path) and original.suffix == '.npy':
                    declared = None
                    raw_report = original.parent/'result.json'
                    try:
                        declaration = json.loads(self.read(raw_report)) if raw_report.is_file() else {}
                    except (OSError,ValueError):
                        declaration = {}
                    if original.name == 'propagator.npy':
                        declared = declaration.get('propagator_sha256')
                    match = re.fullmatch(r'gauge_rank(\d+)\.npy',original.name)
                    hashes = declaration.get('saved_gauge_sha256',[])
                    if match and isinstance(hashes,list) and int(match[1]) < len(hashes):
                        declared = hashes[int(match[1])]
                    if match:
                        declared = dict(declaration.get('output_gauge_files',[])).get(int(match[1]),declared)
                    if declared:
                        excluded['declared_sha256'] = declared
                        excluded['declaration_source_path'] = str(raw_report)
            row['review'] = self.verification_review(path,data,report,files) if payload else dict(
                registered_report_contract=False, complete_review_material=False,
                numerical_verification_rerun=False, errors=['Active/unfinished attempt; no completion inferred'])
            if payload and 'snapshot' in data:
                manifest, copied = self.copy_archive(path,data)
                if self.best and self.best.get('attempt') == path.name:
                    row['current_best'] = True
                    if copied and copied['included']:
                        row['best_source_archive'] = copied['export_path']
                        for entry in manifest['files']:
                            if not entry.get('deleted'):
                                relative = safe_relative(entry['path'])
                                self.write(path/'source'/relative, 'best/source/'+relative.as_posix(), expected=entry['sha256'])
                    self.write(path/'artifacts/liblqcd_cpu.so','best/liblqcd_cpu.so',
                               expected=data.get('report',{}).get('library_sha256'))
        reference = Path(self.config['reference_skill']).resolve()
        try:
            if ledger.tree_manifest(reference) != self.config['reference_manifest']:
                raise ValueError('Frozen reference skill tree differs from campaign manifest')
        except (OSError, ValueError, ledger.EvidenceError) as exc:
            self.errors.append(dict(path=str(reference),error=str(exc)))
        for entry in self.config['reference_manifest']:
            relative = safe_relative(entry['path'])
            self.write(reference/relative, 'reference-skill/'+relative.as_posix(), expected=entry['sha256'])
        after = fingerprint(metadata(self.root))
        changed = list(self.changed_during_reads)
        for path, original_sha in self.reads.items():
            try:
                same = not Path(path).is_symlink() and ledger.digest(path) == original_sha
            except OSError:
                same = False
            if not same:
                if path not in changed:
                    changed.append(path)
        consistent = before == after and not changed and before.get(str(self.root/'campaign.json')) == initial_config_sha
        registered_review_complete = all(not row['registered'] or row['review']['complete_review_material'] for row in self.attempts)
        best_review_complete = bool(self.best and any(row['id']==self.best.get('attempt') and
            row['review']['complete_review_material'] for row in self.attempts))
        result = dict(schema=1, generated_at=ledger.now(), campaign_path=str(self.root),
            export_complete=True, read_consistent=consistent, ongoing=any(r['running_checkpoint'] or
                r['status'] not in TERMINAL for r in self.attempts), completed_only=self.completed_only,
            registered_review_complete=registered_review_complete, best_review_complete=best_review_complete,
            objective=self.config.get('objective'), best=redact(self.best), attempts=self.attempts,
            counts=dict(attempts=len(self.attempts),statuses=dict(Counter(r['status'] for r in self.attempts)),
                running_checkpoints=sum(r['running_checkpoint'] for r in self.attempts),
                registered_full12_contracts=sum(r['review']['registered_report_contract'] for r in self.attempts),
                complete_review_material=sum(r['review']['complete_review_material'] for r in self.attempts)),
            metadata_before_sha256=ledger.object_digest(before), metadata_after_sha256=ledger.object_digest(after),
            changed_files_during_read=changed, original_metadata_sha256=before,
            max_log_bytes=self.max_log_bytes, max_total_bytes=self.max_total_bytes,
            included_bytes=self.total, included_files=sum(x['included'] for x in self.entries),
            exclusion_counts=dict(Counter(x['excluded_reason'] for x in self.entries if not x['included'])),
            entries=self.entries, errors=self.errors,
            interpretation='Read-only evidence copy; no seal, promotion, solver, profile or new numerical verification. '
                'Only samples determine timings. Declared hashes of excluded arrays are not reverified. '
                'Redacted/excerpted files have separate original and export hashes. Inconsistent snapshots require regeneration.')
        ledger.atomic(self.output/'export-manifest.json',result)
        (self.output/'README.md').write_text('# Ongoing campaign evidence snapshot\n\n' +
            f'Read consistent: {consistent}; ongoing: {result["ongoing"]}.\n\n' +
            result['interpretation']+'\n\nOriginal paths, all statuses, exclusions and hashes are in export-manifest.json. '
            'archives/ contains deduplicated exact source archives; best/source and best/liblqcd_cpu.so retain the current best. '
            'Build trees and scientific arrays remain on the source machine. No original evidence was sealed or modified.\n',encoding='utf-8')
        return result


def export(campaign, output, **options):
    return Exporter(campaign,output,**options).run()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--completed-only', action=argparse.BooleanOptionalAction, default=True,
                        help='Always include every attempt status; default omits active/unfinished payload')
    parser.add_argument('--max-log-bytes', type=int, default=131072)
    parser.add_argument('--max-total-bytes', type=int, default=268435456)
    args = parser.parse_args(argv)
    if args.max_log_bytes < 128 or args.max_total_bytes < 1024:
        parser.error('Require max-log-bytes >=128 and max-total-bytes >=1024')
    result = export(args.campaign,args.output,completed_only=args.completed_only,
                    max_log_bytes=args.max_log_bytes,max_total_bytes=args.max_total_bytes)
    print(json.dumps({k:result[k] for k in ['campaign_path','generated_at','read_consistent','ongoing',
        'included_files','included_bytes','counts','registered_review_complete','best_review_complete','best']},ensure_ascii=False))
    return 0 if result['read_consistent'] and result['registered_review_complete'] and not result['errors'] else 2


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print('EVIDENCE EXPORT ERROR: '+str(exc),file=sys.stderr)
        sys.exit(2)
