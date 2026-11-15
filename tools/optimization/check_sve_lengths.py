#!/usr/bin/env python3
"""Run the packed-kernel oracle at 16/32/64-byte SVE lengths via exec.

Set VL in a separate Python child before exec, never inside a live SVE C++
stack frame. No numpy or solver library is imported into this wrapper.
"""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def child(binary, width, reuse):
    libc = ctypes.CDLL(None, use_errno=True)
    libc.prctl.argtypes = [ctypes.c_int, *([ctypes.c_ulong]*4)]
    libc.prctl.restype = ctypes.c_int
    # Linux uapi/linux/prctl.h: PR_SVE_SET_VL and PR_SVE_VL_INHERIT.
    actual = libc.prctl(50, width | (1 << 17), 0, 0, 0)
    if actual < 0:
        raise OSError(ctypes.get_errno(), "PR_SVE_SET_VL failed")
    if actual & 0xffff != width:
        raise RuntimeError(f"requested VL {width}, obtained {actual & 0xffff}")
    os.environ["LQCD_ARM_SVE_REUSE"] = str(reuse)
    os.execv(str(binary), [str(binary)])


def main():
    if len(sys.argv) == 5 and sys.argv[1] == "--child":
        child(Path(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
        return
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("binary", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    binary = args.binary.resolve(strict=True)
    rows = []
    for width in (16,32,64):
        for reuse in (0,1):
            run = subprocess.run([sys.executable,str(Path(__file__).resolve()),
                "--child",str(binary),str(width),str(reuse)],
                capture_output=True,text=True,timeout=60)
            match = re.search(r"PASS packed SVE:.*VL=(\d+) bytes",run.stdout)
            passed = run.returncode == 0 and bool(match) and int(match[1]) == width
            rows.append(dict(requested_vector_bytes=width,reuse=reuse,
                actual_vector_bytes=int(match[1]) if match else None,
                returncode=run.returncode,passed=passed,
                stdout=run.stdout[-4000:],stderr=run.stderr[-4000:]))
    result = dict(complete=True,passed=all(r["passed"] for r in rows),
        binary=str(binary),binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        wrapper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        host=os.uname().nodename,allowed_cpus=sorted(os.sched_getaffinity(0)),runs=rows)
    args.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
