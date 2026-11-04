"""Record only controlled runtime keys under the failed case's exact launcher."""
import json
import os
from pathlib import Path

rank=int(os.environ['OMPI_COMM_WORLD_RANK'])
if rank in (0,8):
    root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
    output=root/'runtime-environment-probe142'
    output.mkdir(exist_ok=True,mode=0o700)
    keys=('LD_LIBRARY_PATH','OMP_WAIT_POLICY','GOMP_SPINCOUNT')
    row=dict(rank=rank,observed={key:os.environ.get(key)for key in keys},native_solver_loaded=False)
    with (output/('rank%d.json'%rank)).open('x')as stream:json.dump(row,stream,indent=2)
    print('CONTROLLED_RUNTIME '+json.dumps(row),flush=True)
