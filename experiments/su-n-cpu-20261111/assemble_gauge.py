import hashlib,json,sys
from pathlib import Path
import numpy as np
src=Path(sys.argv[1]);dst=Path(sys.argv[2])
manifest=json.loads((src/'canonical-manifest.json').read_text())
assert manifest['prepared_gauge_sha256']=='126d658999367b0ece3801c61cd143542d7db0dddc37ab60e6e668e18faa6834'
digest=hashlib.sha256()
with dst.open('xb')as out:
 for rank in range(16):
  path=src/f'gauge_rank{rank:05d}.npy'
  assert hashlib.sha256(path.read_bytes()).hexdigest()==manifest['files'][path.name]
  g=np.load(path)
  assert g.shape==(4,24,24,24,4,3,3) and g.dtype==np.complex128
  data=g.tobytes();digest.update(data);out.write(data)
assert digest.hexdigest()==manifest['prepared_gauge_sha256']
print(json.dumps(dict(complete=True,shape=[64,24,24,24,4,3,3],sha256=digest.hexdigest(),bytes=dst.stat().st_size)))
