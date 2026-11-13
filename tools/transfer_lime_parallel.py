#!/usr/bin/env python3
"""Parallel, resumable relay for a large LIME input between SSH hosts.

Each disjoint part is written to a separate destination file. After every part
reaches its expected size, the destination host concatenates them in order,
checks SHA256, and atomically publishes the final name.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import shlex
import subprocess
import threading
import time


class TransferInterrupted(RuntimeError):
    pass


def ssh(host, command):
    return ["ssh", "-T", "-c", "aes128-gcm@openssh.com", "-o", "IPQoS=none",
            "-o", "BatchMode=yes", "-o", "ConnectTimeout=20",
            "-o", "ServerAliveInterval=15", "-o", "ServerAliveCountMax=8",
            host, command]


def remote(host, command):
    return subprocess.check_output(ssh(host, command), text=True, timeout=90).strip()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-host", required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--destination-host", required=True)
    p.add_argument("--destination", required=True)
    p.add_argument("--bytes", type=int, required=True)
    p.add_argument("--sha256", required=True)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--parallel", type=int, default=4)
    p.add_argument("--chunk-bytes", type=int, default=1024**3)
    a = p.parse_args()
    if a.parallel < 1 or a.chunk_bytes < 8 * 1024**2:
        p.error("parallel must be positive and chunk-bytes must be at least 8 MiB")
    if len(a.sha256) != 64 or any(c not in "0123456789abcdef" for c in a.sha256):
        p.error("sha256 must be lowercase hexadecimal")
    destination = shlex.quote(a.destination)
    root = a.destination + ".parts"
    root_q = shlex.quote(root)
    remote(a.destination_host, f"test ! -e {destination} && mkdir -p {root_q}")
    chunks = []
    for index, start in enumerate(range(0, a.bytes, a.chunk_bytes)):
        chunks.append((index, start, min(a.chunk_bytes, a.bytes - start)))
    listing = remote(a.destination_host, f"for f in {root_q}/part-*.bin; do test -f \"$f\" && stat -c '%n %s' \"$f\"; done || true")
    sizes = {}
    for line in listing.splitlines():
        name, size = line.rsplit(" ", 1)
        sizes[Path(name).name] = int(size)
    lock = threading.Lock()
    done = sum(min(sizes.get(f"part-{i:04d}.bin", 0), size) for i, _, size in chunks)
    started = time.monotonic()

    def transfer_once(chunk):
        index, start, size = chunk
        name = f"part-{index:04d}.bin"
        part = shlex.quote(f"{root}/{name}")
        current = int(remote(a.destination_host,
            f"if test -f {part}; then stat -c %s {part}; else printf '0\\n'; fi"))
        if current > size:
            raise RuntimeError(f"destination part {name} is larger than expected")
        if current == size:
            return index, size, 0.0
        source_cmd = (f"dd if={shlex.quote(a.source)} bs=8M iflag=skip_bytes,count_bytes "
                      f"skip={start + current} count={size - current} status=none")
        destination_cmd = f"dd of={part} bs=8M oflag=append conv=notrunc status=none"
        source = subprocess.Popen(ssh(a.source_host, source_cmd), stdout=subprocess.PIPE)
        destination_proc = subprocess.Popen(ssh(a.destination_host, destination_cmd),
                                             stdin=subprocess.PIPE)
        # A connected SSH server may stop forwarding data while keepalives
        # still succeed. Interrupt stalled reads/writes from a separate thread.
        activity = [time.monotonic()]
        finished = threading.Event()

        def watchdog():
            while not finished.wait(5):
                if time.monotonic() - activity[0] > 180:
                    print(f"STALLED part={index}; preserving remote prefix", flush=True)
                    for child in (source, destination_proc):
                        if child.poll() is None:
                            child.terminate()
                    return

        monitor = threading.Thread(target=watchdog, daemon=True)
        monitor.start()
        try:
            while True:
                data = source.stdout.read(8 * 1024 * 1024)
                if not data:
                    break
                destination_proc.stdin.write(data)
                activity[0] = time.monotonic()
                with lock:
                    nonlocal_done[0] += len(data)
                    elapsed = time.monotonic() - started
                    speed = nonlocal_done[0] / 1024**2 / max(elapsed, 0.001)
                    if nonlocal_done[0] == len(data) or int(nonlocal_done[0] / 2**30) != int((nonlocal_done[0] - len(data)) / 2**30):
                        print(f"TRANSFER {nonlocal_done[0]}/{a.bytes} bytes "
                              f"{nonlocal_done[0]/a.bytes:.1%} {speed:.2f} MiB/s", flush=True)
            source.stdout.close()
            source_rc = source.wait()
            destination_proc.stdin.close()
            destination_rc = destination_proc.wait()
            if source_rc or destination_rc:
                raise TransferInterrupted(f"part {index} failed: source={source_rc}, destination={destination_rc}")
        finally:
            finished.set()
            for child in (source, destination_proc):
                if child.poll() is None:
                    child.terminate()
                    child.wait()
        return index, size, time.monotonic() - started

    def transfer(chunk):
        for attempt in range(1, 9):
            try:
                result = transfer_once(chunk)
                print(f"PART_COMPLETE index={chunk[0]} bytes={chunk[2]}", flush=True)
                return result
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired,
                    TransferInterrupted, BrokenPipeError, ConnectionResetError) as error:
                print(f"PART_RETRY index={chunk[0]} attempt={attempt}/8: {error}", flush=True)
                if attempt == 8:
                    raise
                time.sleep(min(5 * attempt, 30))

    nonlocal_done = [done]
    with ThreadPoolExecutor(max_workers=a.parallel) as pool:
        futures = [pool.submit(transfer, chunk) for chunk in chunks]
        for future in as_completed(futures):
            future.result()
    names = " ".join(shlex.quote(f"{root}/part-{i:04d}.bin") for i, _, _ in chunks)
    partial = shlex.quote(a.destination + ".partial")
    verify = remote(a.destination_host,
        f"cat {names} > {partial}; stat -c %s {partial}; sha256sum {partial}").splitlines()
    size, checksum = int(verify[0]), verify[1].split()[0]
    if size != a.bytes or checksum != a.sha256:
        raise RuntimeError(f"verification failed: bytes={size}, sha256={checksum}")
    remote(a.destination_host,
           f"ln -- {partial} {destination} && rm -- {partial} {names} && rmdir -- {root_q}")
    result = dict(complete=True, source_host=a.source_host, source_path=a.source,
                  destination_host=a.destination_host, destination_path=a.destination,
                  bytes=size, sha256=checksum, parallel=a.parallel,
                  chunk_bytes=a.chunk_bytes, elapsed_seconds=time.monotonic()-started,
                  transfer_tool_commit=subprocess.check_output(
                      ["git", "-C", str(Path(__file__).resolve().parents[1]), "rev-parse", "HEAD"],
                      text=True).strip())
    a.manifest.parent.mkdir(parents=True, exist_ok=True)
    a.manifest.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    for attempt in range(1, 9):
        try:
            main()
            break
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired,
                TransferInterrupted, BrokenPipeError, ConnectionResetError) as error:
            print(f"RETRY {attempt}/8: {error}", flush=True)
            if attempt == 8:
                raise
            time.sleep(30)
