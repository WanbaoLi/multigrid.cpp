#!/usr/bin/env python3
"""Resume a large immutable input between two SSH aliases via binary pipes.

Keys stay in the local SSH configuration. The destination remains .partial
until its size and SHA256 match. No third-party Python packages are required.
"""

import argparse
import json
from pathlib import Path
import re
import shlex
import subprocess
import time


def ssh(host, command):
    return ["ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20",
            "-o", "ServerAliveInterval=15", "-o", "ServerAliveCountMax=8",
            host, command]


def query(host, command):
    return subprocess.check_output(ssh(host, command), text=True).strip()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-host", required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--destination-host", required=True)
    p.add_argument("--destination", required=True)
    p.add_argument("--bytes", type=int, required=True)
    p.add_argument("--sha256", required=True)
    p.add_argument("--manifest", type=Path, required=True)
    a = p.parse_args()
    if a.bytes <= 0 or not re.fullmatch(r"[0-9a-f]{64}", a.sha256):
        p.error("Expected a positive byte count and lowercase SHA256")
    target = shlex.quote(a.destination)
    partial = shlex.quote(a.destination + ".partial")
    # A final file is never overwritten. An interrupted partial file resumes.
    offset = int(query(a.destination_host,
        f"test ! -e {target} || exit 2; "
        f"if test -f {partial}; then stat -c %s {partial}; else printf '0\\n'; fi"))
    if offset > a.bytes:
        raise RuntimeError("Partial file is larger than the expected source")
    started = last_report = time.monotonic()
    received = offset
    if offset < a.bytes:
        source_cmd = (f"dd if={shlex.quote(a.source)} bs=8M "
                      f"iflag=skip_bytes skip={offset} status=none")
        # SSH runs first, then dd appends; its successful exit confirms all
        # bytes written through the pipe have reached the destination process.
        dest_cmd = f"dd of={partial} bs=8M oflag=append conv=notrunc status=none"
        dest = subprocess.Popen(ssh(a.destination_host, dest_cmd), stdin=subprocess.PIPE)
        source = subprocess.Popen(ssh(a.source_host, source_cmd), stdout=subprocess.PIPE)
        try:
            while True:
                chunk = source.stdout.read(1024 * 1024)
                if not chunk:
                    break
                dest.stdin.write(chunk)
                received += len(chunk)
                now = time.monotonic()
                if now - last_report >= 15:
                    speed = (received-offset)/(now-started)/1024**2
                    print(f"TRANSFER {received}/{a.bytes} bytes "
                          f"{received/a.bytes:.1%} {speed:.2f} MiB/s", flush=True)
                    last_report = now
            source.stdout.close()
            source_rc = source.wait()
            dest.stdin.close()
            dest_rc = dest.wait()
            if source_rc or dest_rc or received != a.bytes:
                raise RuntimeError(f"Incomplete transfer: source={source_rc}, "
                                   f"destination={dest_rc}, bytes={received}")
        finally:
            for child in (source, dest):
                if child.poll() is None:
                    child.terminate()
                    child.wait()
    verified = query(a.destination_host,
        f"stat -c %s {partial}; sha256sum {partial}").splitlines()
    size, checksum = int(verified[0]), verified[1].split()[0]
    if size != a.bytes or checksum != a.sha256:
        raise RuntimeError(f"Verification failed: bytes={size}, sha256={checksum}")
    # Same-directory hard link publishes atomically and refuses an existing
    # target; remove only the verified partial name after publication succeeds.
    query(a.destination_host, f"ln -- {partial} {target} && rm -- {partial}")
    result = dict(complete=True, source_host=a.source_host, source_path=a.source,
                  destination_host=a.destination_host, destination_path=a.destination,
                  bytes=size, sha256=checksum, resumed_from_bytes=offset,
                  elapsed_seconds=time.monotonic()-started,
                  transfer_tool_commit=subprocess.check_output(
                      ["git", "-C", str(Path(__file__).resolve().parents[1]),
                       "rev-parse", "HEAD"], text=True).strip())
    a.manifest.parent.mkdir(parents=True, exist_ok=True)
    a.manifest.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
