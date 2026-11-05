import hashlib,json
from pathlib import Path
import numpy as np
import h5py
root=Path('/home/share/nsls_lwb/.cache/fair-solve-20261105-v2');root.mkdir(exist_ok=True)
out=root/'input';out.mkdir(exist_ok=False)
fixture=Path('/home/share/nsls_lwb/.cache/mg-20261102/propagator')
gauge=np.concatenate([np.load(fixture/f'gauge_rank{i:05d}.npy')for i in range(16)])
assert gauge.shape==(64,24,24,24,4,3,3)and gauge.dtype==np.complex128
digest=hashlib.sha256(gauge.view(np.uint8)).hexdigest()
assert digest=='126d658999367b0ece3801c61cd143542d7db0dddc37ab60e6e668e18faa6834'
np.save(out/'gauge-untwisted.npy',gauge)
gauge[-1,:,:,:,3]*=-1
with h5py.File(out/'gauge-pyqcu-ap-c128.h5','x')as f:
    f.create_dataset('data',data=gauge.transpose(5,6,4,3,2,1,0))
    f.attrs['mass']=-.277;f.attrs['csw']=1.160920226
(out/'manifest.json').write_text(json.dumps(dict(complete=True,canonical_gauge_sha256=digest,stout_steps=1,stout_rho=.125,
    mass=-.277,csw=1.160920226,tol=1e-8,pyqcu_boundary='last temporal links multiplied by-1 exactly once',
    source_fixture=str(fixture),normalization_scale=3.723),indent=2)+'\n')
print('COMMON_INPUT_READY',flush=True)
