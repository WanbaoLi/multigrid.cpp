"""Download base64-transported immutable exports without shell byte conversion."""
import base64,hashlib,json,re,subprocess,sys,tarfile
from pathlib import Path
local=Path(__file__).resolve().parent/'evidence';local.mkdir(exist_ok=False)
remote='/home/share/nsls_lwb/.cache/fair-solve-20261105-v2/export/'
ssh='/mnt/c/Windows/System32/OpenSSH/ssh.exe'
for name in('manifest.json','evidence.tar.gz'):
    r=subprocess.run([ssh,'-T','-o','ClearAllForwardings=yes','ls','base64 -w0 '+remote+name],capture_output=True,check=True,timeout=180)
    data=''.join(s for s in r.stdout.decode('ascii').splitlines()if re.fullmatch('[A-Za-z0-9+/=]+',s))
    (local/name).write_bytes(base64.b64decode(data,validate=True))
m=json.loads((local/'manifest.json').read_text());assert hashlib.sha256((local/'evidence.tar.gz').read_bytes()).hexdigest()==m['archive_sha256']
with tarfile.open(local/'evidence.tar.gz','r:gz')as t:
    members={r.name:r for r in t.getmembers()};assert len(members)==len(m['files'])
    for i,row in enumerate(m['files']):
        raw=t.extractfile(members[row['path']]).read();assert len(raw)==row['bytes']and hashlib.sha256(raw).hexdigest()==row['sha256']
        dest=local/'records'/('%04d'%i+Path(row['path']).suffix);dest.parent.mkdir(exist_ok=True);dest.write_bytes(raw)
        row['local_path']=str(dest.relative_to(local))
(local/'file-map.json').write_text(json.dumps(m,indent=2)+'\n')
(local/'.gitattributes').write_text('* -text\nrecords/* -text\n')
print('EXACT_EXPORT_FILES_VERIFIED',len(m['files']))
