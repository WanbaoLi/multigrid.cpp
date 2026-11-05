import hashlib,json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parent;repo=root.parent;m=json.loads((root/'evidence/file-map.json').read_text())
p=subprocess.Popen(['git','cat-file','--batch'],cwd=repo,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
for row in m['files']:
    path=str((root/'evidence'/row['local_path']).relative_to(repo)).replace('\\','/')
    p.stdin.write(('HEAD:'+path+'\n').encode());p.stdin.flush()
    header=p.stdout.readline().split();assert header[1]==b'blob';raw=p.stdout.read(int(header[2]));assert p.stdout.read(1)==b'\n'
    assert len(raw)==row['bytes']and hashlib.sha256(raw).hexdigest()==row['sha256']
p.stdin.close();assert p.wait()==0
print('EXACT_COMMITTED_RECORDS',len(m['files']))
