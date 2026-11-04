"""New immutable namespace for the attributed runtime-only retry."""
import hashlib
import json
from pathlib import Path
import shutil
import tarfile
root=Path(__file__).parent;target=root/'runtime-only-v6-helpers'
target.mkdir(exist_ok=False)
for p in(root/'phase5-worker8-v5-helpers').iterdir():
    if p.is_file()and p.suffix=='.py':shutil.copyfile(p,target/p.name)
for name in ('runtime_search_path_v6.py','phase5_runtime_only_v6.py'):
    shutil.copyfile(root/name,target/name)
benchmark=root/'bench_full12_frozen_711.py'
assert hashlib.sha256(benchmark.read_bytes()).hexdigest()=='711df30c341f31aa8770b371b5d8ec32fb90cbbe8dff0a173e5e1532d977f5a1'
shutil.copyfile(benchmark,target/'bench_full12_contract_source.py')
capture=(root/'runtime_benchmark_capture_v5.py').read_text()
old="MPI_PREFIX+str(context.get('LD_LIBRARY_PATH',os.environ['LQCD_OPT_CAPTURE_BASE_LD']))"
assert capture.count(old)==1
capture=capture.replace('import file_integrity as integrity','import file_integrity as integrity\nfrom runtime_search_path_v6 import expected_search_path')
capture=capture.replace(old,"expected_search_path(context,os.environ['LQCD_OPT_CAPTURE_BASE_LD'],MPI_PREFIX)")
capture=capture.replace('observed_fixed_mpi_prefix=MPI_PREFIX','known_mpi_launch_prefix=MPI_PREFIX,explicit_context_path_overwrites_launch_environment=True')
(target/'runtime_benchmark_capture_v6.py').write_text(capture,newline='\n')
capture_sha=hashlib.sha256((target/'runtime_benchmark_capture_v6.py').read_bytes()).hexdigest()
adapter=(root/'raw_controller_setup_capture_v5.py').read_text().replace('runtime_benchmark_capture_v5.py','runtime_benchmark_capture_v6.py')
(target/'raw_controller_setup_capture_v6.py').write_text(adapter,newline='\n')
for name in ('runtime_only_scope_v6.py','prepare_runtime_only_v6.py','test_runtime_only_v6.py'):
    source=root/name
    if source.exists():shutil.copyfile(source,target/name)
manifest=dict(files={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(target.glob('*.py'))},
    prepared_not_executed=True,scope='Fresh five-case runtime bracket; original141 failed state untouched',
    scientific_trials_and_gates='Inherited unchanged c5; only run scope and expected post-context LD expression differ')
mp=target/'runtime-only-v6-files.json';mp.write_text(json.dumps(manifest,indent=2)+'\n',newline='\n')
archive=root/'runtime-only-v6-helpers.tgz'
with tarfile.open(archive,'w:gz')as tar:
    for p in sorted(target.iterdir()):tar.add(p,arcname=p.name)
print(json.dumps(dict(files=len(manifest['files']),manifest_sha256=hashlib.sha256(mp.read_bytes()).hexdigest(),
    archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest()),indent=2))
