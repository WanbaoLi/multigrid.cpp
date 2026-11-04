"""Verify fresh helper deployment and prepare a full8 trial task; never enqueue."""
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile

import file_integrity as integrity

ROOT=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
ARCHIVE_SHA='7fc295833e65d928608bbda15bc8c7ac00dee1f1cf65f8c9ba04836783d857fc'
MANIFEST_SHA='2de5df16026d4d7371cbd6498ba2ab3916944aababf3b02edadb7c2f49be518a'


def sha(path,expected=None):return integrity.read_dual(path,expected)['openssl_sha256']


def main():
    sha(ROOT/'file_integrity.py','34200de5efea2b362880886354c7436fdfb6300bb1c3730b57823aa8acebf427')
    archive=ROOT/'phase5-worker8-v5-helpers.tgz';sha(archive,ARCHIVE_SHA)
    target=ROOT/'aux-phase5-worker8-v5';target.mkdir(mode=0o700,exist_ok=False)
    with tarfile.open(archive)as tar:
        for member in tar.getmembers():
            assert member.isfile()and Path(member.name).name==member.name
            integrity.write_private_new(target/member.name,[tar.extractfile(member).read()])
    manifest=target/'capture-v5-package-manifest.json';sha(manifest,MANIFEST_SHA)
    for name,row in json.loads(manifest.read_text())['files'].items():sha(target/name,row['sha256'])
    from raw_scalar_helper import source_bytes
    argv_path=ROOT/'phase5-worker8-v5-prepare-argv.json'
    expected='7a8856bcec6edfd9f4132290c44c00d8d6304636742dcf3e7b17cd23a9251f1f'
    sha(argv_path,expected);original=json.loads(source_bytes(argv_path,expected))
    result=subprocess.run(original,capture_output=True,text=True,timeout=180)
    receipt=ROOT/'phase5-worker8-v5-preparation-receipt.json'
    integrity.write_json_private(receipt,dict(complete=result.returncode==0,argv=original,
        returncode=result.returncode,stdout=result.stdout,stderr=result.stderr,manifest_sha256=MANIFEST_SHA))
    print(json.dumps(dict(receipt=str(receipt),sha256=sha(receipt),returncode=result.returncode,
        stdout=result.stdout,stderr=result.stderr)),flush=True)
    assert result.returncode==0


if __name__=='__main__':main()
