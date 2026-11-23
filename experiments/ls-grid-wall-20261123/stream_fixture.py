"""Stream the verified fixture from the D: copy and the five verified replacement blocks."""

import argparse
import hashlib
from pathlib import Path
import sys


BLOCK_SIZE = 65536
EXPECTED_SIZE = 509748664
EXPECTED_SHA256 = "f9d2ae770c82bdb80c64491f7301c969420c25a5ba4645e406ef788efd210326"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original", type=Path)
    parser.add_argument("block_manifest", type=Path)
    parser.add_argument("replacement_blocks", type=Path)
    parser.add_argument("--skip", type=int, default=0)
    args = parser.parse_args()
    if not 0 <= args.skip <= EXPECTED_SIZE:
        parser.error("skip must be within the verified file")
    if args.original.stat().st_size != EXPECTED_SIZE:
        raise ValueError("unexpected original fixture size")

    replacements = {}
    with args.replacement_blocks.open("rb") as patches:
        for line in args.block_manifest.read_text().splitlines():
            offset, expected = line.split()
            offset = int(offset)
            if offset in replacements or offset % BLOCK_SIZE or not 0 <= offset <= EXPECTED_SIZE - BLOCK_SIZE:
                raise ValueError(f"invalid replacement block offset {offset}")
            block = patches.read(BLOCK_SIZE)
            if hashlib.sha256(block).hexdigest() != expected:
                raise ValueError(f"replacement block {offset} failed sha256")
            replacements[offset] = block
        if patches.read(1):
            raise ValueError("unexpected trailing replacement bytes")

    checksum = hashlib.sha256()
    with args.original.open("rb") as original:
        for offset in range(0, EXPECTED_SIZE, BLOCK_SIZE):
            native = original.read(BLOCK_SIZE)
            block = replacements.get(offset, native)
            checksum.update(block)
            if offset + len(block) > args.skip:
                sys.stdout.buffer.write(block[max(0, args.skip - offset):])
    if checksum.hexdigest() != EXPECTED_SHA256:
        raise ValueError("reconstructed fixture failed full sha256")


if __name__ == "__main__":
    main()
