#!/usr/bin/env python3
"""Static ARM codegen evidence; instruction sites are NOT dynamic counters."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess


def inspect(library):
    header = library.read_bytes()[:20]
    byteorder = "little" if len(header)>5 and header[5] == 1 else "big"
    if header[:4] != b"\x7fELF" or int.from_bytes(header[18:20],byteorder) != 183:
        raise ValueError("Expected an AArch64 ELF binary")
    output = subprocess.check_output(["nm","-CS","--size-sort",str(library)],text=True)
    functions = []
    selected = ("try_arm_packed_range", "wilson_sve_impl", "clover_range_sve",
                "NativeMG::Impl::local_range", "NativeMG::Impl::clover_range",
                "NativeMG::Impl::block_apply")
    for line in output.splitlines():
        symbol = re.match(r"^([0-9a-f]+)\s+([0-9a-f]+)\s+[TtWw]\s+(.+)$",line)
        if not symbol or not any(s in symbol[3] for s in selected):
            continue
        start, size = int(symbol[1],16), int(symbol[2],16)
        assembly = subprocess.check_output(["objdump","-d",f"--start-address={start}",
            f"--stop-address={start+size}",str(library)],text=True)
        instructions = []
        for row in assembly.splitlines():
            match = re.match(r"\s*[0-9a-f]+:\s+[0-9a-f]{8}\s+(\S+)\s*(.*)",row)
            if match: instructions.append((match[1],match[2]))
        sve = Counter(m for m,o in instructions if re.search(r"\bz\d+\.",o))
        stack = next((int(m[1]) for _,o in instructions[:8]
            if (m:=re.search(r"\[sp, #-(\d+)\]!",o))),None)
        functions.append(dict(symbol=symbol[3],address=start,code_bytes=size,
            entry_fixed_stack_bytes=stack,
            sve_instruction_sites=dict(sorted(sve.items())),
            sve_fused_multiply_add_sites=sum(sve[m] for m in
                ("fmla","fmls","fmad","fmsb","fnmla","fnmls","fnmad","fnmsb")),
            sve_stack_access_sites=sum("[sp" in o and bool(re.search(r"\bz\d+",o))
                                       for m,o in instructions),
            entry_instructions=[m+" "+o for m,o in instructions[:8]]))
    if not functions:
        raise ValueError("No matching ARM Wilson functions; inspect target/symbol retention")
    return dict(complete=True,library=str(library),
        library_sha256=hashlib.sha256(library.read_bytes()).hexdigest(),
        scope="static instruction sites in selected symbols; no dynamic frequency, executed-path or bandwidth claim",
        functions=functions)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("library",type=Path)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--binary-source-commit",required=True)
    p.add_argument("--tool-commit",required=True)
    args=p.parse_args()
    if any(not re.fullmatch(r"[0-9a-f]{40}",v) for v in
           (args.binary_source_commit,args.tool_commit)):
        p.error("source revisions must be exact 40-digit Git commits")
    result=inspect(args.library.resolve(strict=True))
    result.update(binary_source_commit=args.binary_source_commit,
                  tool_commit=args.tool_commit,
                  tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    args.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dict(functions=len(result["functions"]),library_sha256=result["library_sha256"])))


if __name__ == "__main__": main()
