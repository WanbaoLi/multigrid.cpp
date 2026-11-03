#!/usr/bin/env python3
"""Strengthen a frozen verifier's SHA checks, without changing its numerical path."""
import argparse
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

BLOCK = 4 * 1024**2
METHOD = 'SHA256: OpenSSL plus independent CPython software, identical immutable 4MiB chunks'


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def software_constructor():
    for name in ('_sha256', '_sha2'):
        try:
            constructor = importlib.import_module(name).sha256
            candidate = constructor()
        except (ImportError, AttributeError):
            continue
        if type(candidate).__module__ != type(hashlib.sha256()).__module__:
            return constructor
    raise RuntimeError('A distinct CPython software SHA256 implementation is required')


def vectors(constructor=None):
    constructor = constructor or software_constructor()
    require(type(hashlib.sha256()).__module__ == '_hashlib', 'OpenSSL hashlib implementation required')
    require(type(constructor()).__module__ in ('_sha256', '_sha2'), 'Independent software implementation required')
    examples = [(b'', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
                (b'abc', 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'),
                (b'a' * 1000000, 'cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0')]
    for payload, expected in examples:
        a, b = hashlib.sha256(), constructor()
        for offset in range(0, len(payload), 79):
            chunk = payload[offset:offset+79]
            a.update(chunk); b.update(chunk)
        require(a.hexdigest() == b.hexdigest() == expected, 'Independent SHA256 known-vector check failed')
    return dict(openssl_module=type(hashlib.sha256()).__module__,
                software_module=type(constructor()).__module__, known_vectors_passed=len(examples))


def stat(value):
    return dict(dev=value.st_dev, inode=value.st_ino, bytes=value.st_size,
                mtime_ns=value.st_mtime_ns, ctime_ns=value.st_ctime_ns)


def write_new(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')


def bytes_sha(payload, constructor=None):
    a, b = hashlib.sha256(payload), (constructor or software_constructor())(payload)
    require(a.hexdigest() == b.hexdigest(), 'Manifest implementations disagree')
    return a.hexdigest()


def available_memory():
    if sys.platform.startswith('linux'):
        for line in Path('/proc/meminfo').read_text().splitlines():
            if line.startswith('MemAvailable:'):
                return int(line.split()[1]) * 1024
    return None


def resource_gate(payload_bytes, retain_bytes, available=None):
    require(isinstance(retain_bytes, int) and retain_bytes >= payload_bytes,
            'Retention budget must hold the complete large payload to preserve a mismatched read')
    available = available_memory() if available is None else available
    require(available is None or available >= retain_bytes + 256 * 1024**2,
            'Insufficient available memory for bounded mismatch-byte retention')


class AuditedSHA:
    def __init__(self, output, expected, required_sizes=None, retain_bytes=2200 * 1024**2, constructor=None):
        self.output = Path(output)
        require(self.output.is_dir() and not self.output.is_symlink(), 'Fresh regular audit directory required')
        self.expected = {str(Path(k).resolve()):v for k,v in expected.items()}
        self.required_sizes = {str(Path(k).resolve()):v for k,v in (required_sizes or {}).items()}
        self.retain_bytes = retain_bytes
        self.constructor = constructor or software_constructor()
        self.rows = []

    def __call__(self, path):
        path = Path(path)
        require(not path.is_symlink(), 'Audit rejects symlink file targets')
        resolved = path.resolve(strict=True)
        require(path.absolute() == resolved, 'Audit rejects symlink path components')
        required = self.required_sizes.get(str(resolved))
        expected = self.expected.get(str(resolved))
        initial = stat(path.stat())
        require(required is None or initial['bytes'] == required, 'Recorded payload byte size differs')
        if required is not None:
            resource_gate(required, self.retain_bytes)
        keep = initial['bytes'] <= self.retain_bytes
        parts = []
        a, b = hashlib.sha256(), self.constructor()
        count = 0
        started = time.time()
        with path.open('rb') as stream:
            before = stat(os.fstat(stream.fileno()))
            for chunk in iter(lambda: stream.read(BLOCK), b''):
                require(isinstance(chunk, bytes), 'Immutable input bytes required')
                a.update(chunk); b.update(chunk)
                if keep:
                    parts.append(chunk)
                count += len(chunk)
            after = stat(os.fstat(stream.fileno()))
        final = stat(path.stat())
        ca, cb = a.hexdigest(), b.hexdigest()
        stable = initial == before == after == final and count == before['bytes']
        passed = stable and ca == cb and (expected is None or ca == expected)
        row = dict(index=len(self.rows), path=str(resolved), complete=True, passed=passed,
                   method=METHOD, block_bytes=BLOCK, openssl_sha256=ca, software_sha256=cb,
                   expected_sha256=expected, read_bytes=count, required_bytes=required,
                   initial=initial, fd_before=before, fd_after=after, path_after=final,
                   metadata_stable=stable, same_immutable_bytes=True, original_open_mode='rb',
                   started=started, seconds=time.time()-started, retained_bytes=count if keep else 0)
        if not passed and keep:
            snapshot = self.output / ('hash-%03d-bad-view.bin' % row['index'])
            with snapshot.open('xb') as stream:
                for part in parts:
                    require(stream.write(part) == len(part), 'Short mismatch snapshot write')
                stream.flush(); os.fsync(stream.fileno())
            row['bad_view_snapshot'] = str(snapshot)
            row['bad_view_bytes'] = snapshot.stat().st_size
            row['snapshot_exact_held_byte_view'] = True
        self.rows.append(row)
        write_new(self.output / ('hash-%03d.json' % row['index']), row)
        require(passed, 'Strict dual SHA256/expected/FD byte-count check failed; actual view retained when budget permitted')
        return ca

    def manifest(self):
        return dict(complete=bool(self.rows) and all(r['passed'] for r in self.rows), method=METHOD,
                    block_bytes=BLOCK, rows=[dict(path='hash-%03d.json' % row['index'],
                        sha256=bytes_sha((self.output / ('hash-%03d.json' % row['index'])).read_bytes(), self.constructor))
                        for row in self.rows])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark', type=Path, required=True)
    parser.add_argument('--audit-output', type=Path, required=True)
    parser.add_argument('--expected-benchmark-sha', required=True)
    parser.add_argument('--expected-propagator-sha', required=True)
    parser.add_argument('--expected-gold-sha', required=True)
    parser.add_argument('--payload-bytes', type=int, default=2038431872)
    parser.add_argument('--retain-mib', type=int, default=2200)
    args, remaining = parser.parse_known_args()
    require('--verify' in remaining and '--diagnostic' not in remaining, 'Precision-only --verify command required')
    require('--verification-output' in remaining, 'Explicit fresh verification output required')
    index = remaining.index('--verify')
    run = Path(remaining[index+1]).resolve(strict=True)
    initial = json.loads((run / 'result.json').read_text())
    require(not initial.get('verification',{}).get('complete'), 'Fresh precision protocol only; cached verification is not a new result')
    require(initial['propagator_sha256'] == args.expected_propagator_sha, 'Stored original expected SHA changed')
    constructor = software_constructor()
    identity = vectors(constructor)
    resource_gate(args.payload_bytes, args.retain_mib * 1024**2)
    require(bytes_sha(args.benchmark.read_bytes(), constructor) == args.expected_benchmark_sha,
            'Frozen verifier source differs')
    args.audit_output.mkdir(exist_ok=False)
    expected = {run / 'propagator.npy':args.expected_propagator_sha,
                Path(initial['reference_propagator']):args.expected_gold_sha,
                args.benchmark:args.expected_benchmark_sha}
    expected.update({run / ('gauge_rank%05d.npy' % rank):value for rank,value in initial['output_gauge_files']})
    hasher = AuditedSHA(args.audit_output, expected,
                       {run / 'propagator.npy':args.payload_bytes,
                        Path(initial['reference_propagator']):args.payload_bytes},
                       args.retain_mib * 1024**2, constructor)
    provenance = dict(complete=True, method=METHOD, identity=identity, wrapper_sha256=bytes_sha(Path(__file__).read_bytes(),constructor),
                      benchmark_sha256=args.expected_benchmark_sha, payload_bytes=args.payload_bytes,
                      source_unchanged=True, numerical_thresholds_unchanged=True,
                      original_sha_function_retained=True, prior_failure_root_cause='unresolved')
    write_new(args.audit_output / 'protocol.json', provenance)
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location('frozen_audited_bench', args.benchmark)
    bench = importlib.util.module_from_spec(spec); spec.loader.exec_module(bench)
    original_sha = bench.sha
    require(original_sha.__code__.co_name == 'sha', 'Original checksum function missing')
    # Only the checksum callback changes. Numerical verifier/helper and solver remain frozen.
    bench.sha = hasher
    sys.argv = [str(args.benchmark), *remaining]
    try:
        bench.main()
        measured = json.loads((run / 'result.json').read_text())
        require({k:v for k,v in initial.items() if k != 'verification'} ==
                {k:v for k,v in measured.items() if k != 'verification'}, 'Non-verification measurement fields changed')
        verification = measured['verification']
        require(verification['propagator_sha256'] == args.expected_propagator_sha and
                verification['reference_propagator_sha256'] == args.expected_gold_sha,
                'Frozen helper/gold checks do not match original expected values')
        require(verification['complete'] and verification['passed'] and verification['columns'] == 12,
                'Complete numerical verification required')
        manifest = hasher.manifest()
        require(manifest['complete'], 'Checksum audit incomplete')
        write_new(args.audit_output / 'manifest.json', manifest)
        manifest_sha = bytes_sha((args.audit_output / 'manifest.json').read_bytes(),constructor)
        verification['checksum_audit'] = dict(method=METHOD, wrapper_sha256=provenance['wrapper_sha256'],
            benchmark_sha256=args.expected_benchmark_sha, manifest_path=str(args.audit_output / 'manifest.json'),
            manifest_sha256=manifest_sha, protocol_sha256=bytes_sha((args.audit_output/'protocol.json').read_bytes(),constructor),
            independent_modules=identity, prior_failure_root_cause='unresolved')
        bench.atomic(run / 'result.json', measured)
        print('AUDITED_VERIFY_COMPLETE ' + json.dumps(dict(manifest_sha256=manifest_sha, checks=len(hasher.rows))),flush=True)
    except BaseException as exc:
        write_new(args.audit_output / 'failure.json', dict(complete=False, error_type=type(exc).__name__,
            message=str(exc), method=METHOD, completed_checks=len(hasher.rows), numerical_acceptance=False))
        raise
    finally:
        bench.sha = original_sha


if __name__ == '__main__':
    main()
