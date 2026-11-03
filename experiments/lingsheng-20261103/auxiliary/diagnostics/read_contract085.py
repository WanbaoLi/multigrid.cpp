#!/usr/bin/env python3
"""085 read-only file-contract diagnosis. Never output raw tail strings/hex."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
import _sha256

R=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
RUN=R/'campaign/attempts/057-best-profile-worker5/measurements/full12'
ORIGINAL=RUN/'propagator.npy'
AUDIT=RUN/'sha-audit-retry2/hash-000.json'
BLOCK=4*1024**2
SIZE=2038431872
EXPECTED='805ebc992752c4127c342c40b491d897a2451b8095adab4a553eb172ba2507a0'


def stat(s):return dict(dev=s.st_dev,inode=s.st_ino,bytes=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns,blksize=s.st_blksize,blocks=s.st_blocks)
def pair(data):return dict(openssl=hashlib.sha256(data).hexdigest(),software=_sha256.sha256(data).hexdigest())
def dump(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')


def preserve(output,name,parts):
    path=output/(name+'-anomaly-view.bin');fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'wb') as f:
        for part in parts:
            if f.write(part)!=len(part):raise RuntimeError('Shortnewanomalysnapshotwrite')
        f.flush();os.fsync(f.fileno())
    return dict(path=str(path),bytes=path.stat().st_size,mode=oct(path.stat().st_mode&0o777),scope='Exactreturnedbytesheldbymethod; originalunchanged')


def anomaly(output,name,row,parts,message):
    row.update(complete=False,anomaly=message,preserved_view=preserve(output,name,parts))
    dump(output/(name+'.json'),row)
    raise RuntimeError(message)


def prefix(path,name,output):
    a,b=hashlib.sha256(),_sha256.sha256();parts=[];count=0;fd=os.open(path,os.O_RDONLY)
    row=dict(method='boundedos.pread',path=str(path),requested_limit=SIZE,stream_type='integerFD',raw_type='POSIXpread',reads=[])
    try:
        row['fd_before']=stat(os.fstat(fd));row['fd_position_before']=os.lseek(fd,0,os.SEEK_CUR)
        while count<SIZE:
            want=min(BLOCK,SIZE-count);part=os.pread(fd,want,count);parts.append(part)
            rec=dict(offset=count,requested=want,returned=len(part),fd_position=os.lseek(fd,0,os.SEEK_CUR));row['reads'].append(rec)
            if len(part)>want or not part:anomaly(output,name,row,parts,'preadlengthoutsideexplicitrequestor prematureEOF')
            a.update(part);b.update(part);count+=len(part)
        row.update(complete=True,read_bytes=count,openssl=a.hexdigest(),software=b.hexdigest(),fd_after=stat(os.fstat(fd)),fd_position_after=os.lseek(fd,0,os.SEEK_CUR))
        if row['fd_before']!=row['fd_after'] or row['fd_position_after']!=row['fd_position_before']:
            anomaly(output,name,row,parts,'preadmetadataorFDpositionchanged')
        dump(output/(name+'.json'),row);return row,a,b
    finally:os.close(fd)


def gnu_prefix(path,name,output):
    with (output/(name+'-head.stderr')).open('xb') as err:
        head=subprocess.Popen(['head','-c',str(SIZE),str(path)],stdout=subprocess.PIPE,stderr=err)
        sha=subprocess.Popen(['sha256sum'],stdin=head.stdout,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        head.stdout.close()
        try:out,error=sha.communicate(timeout=90);headrc=head.wait(timeout=10)
        except BaseException:sha.kill();head.kill();sha.wait();head.wait();raise
    row=dict(path=str(path),requested_prefix_bytes=SIZE,sha256=out.decode().split()[0],head_returncode=headrc,sha_returncode=sha.returncode,stderr=error.decode(errors='replace'))
    dump(output/(name+'-gnu.json'),row)
    if headrc or sha.returncode:raise RuntimeError('IndependentGNUhead-cpipelinefailed')
    return row


def exact_tail_and_eof(output):
    fd=os.open(ORIGINAL,os.O_RDONLY)
    try:
        row=dict(fd_before=stat(os.fstat(fd)),fd_position_before=os.lseek(fd,0,os.SEEK_CUR))
        part=os.pread(fd,128,SIZE-128);row.update(tail_requested=128,tail_returned=len(part),tail_sha=pair(part))
        if len(part)!=128:anomaly(output,'original-exact-tail',row,[part],'exact128bytetailreadcontractfailed')
        eof=os.pread(fd,1,SIZE);row.update(eof_requested=1,eof_offset=SIZE,eof_returned=len(eof),eof_sha=pair(eof))
        if eof:anomaly(output,'original-exact-tail',row,[eof],'preadreturneddataatlogicalEOF')
        row.update(fd_after=stat(os.fstat(fd)),fd_position_after=os.lseek(fd,0,os.SEEK_CUR))
        dump(output/'original-exact-tail.json',row);return row
    finally:os.close(fd)


def stream_eof(name,buffering,output):
    a,b=hashlib.sha256(),_sha256.sha256();parts=[];count=0;recent=[]
    with ORIGINAL.open('rb',buffering=buffering) as f:
        raw=getattr(f,'raw',f);fd=f.fileno()
        def positions():return dict(tell=f.tell(),raw_tell=raw.tell(),lseek=os.lseek(fd,0,os.SEEK_CUR))
        row=dict(method='readtoEOF',buffering=buffering,stream_type=type(f).__name__,raw_type=type(raw).__name__,fd_before=stat(os.fstat(fd)))
        while True:
            before=positions();part=f.read(BLOCK);after=positions()
            # Capture len/positions BEFORE either update; no rawbytes displayed.
            record=dict(offset=count,requested=BLOCK,returned=len(part),before=before,after=after)
            recent.append(record);recent=recent[-2:];row['last_two_reads']=recent
            if part:parts.append(part)
            if len(part)>BLOCK or count+len(part)>SIZE:
                row.update(observed_bytes=count+len(part),fd_at_anomaly=stat(os.fstat(fd)));anomaly(output,name,row,parts,'streamreturnedbytesbeyondlogicalsizeorrequest')
            if not part:break
            a.update(part);b.update(part);count+=len(part)
        row.update(complete=True,read_bytes=count,openssl=a.hexdigest(),software=b.hexdigest(),fd_after=stat(os.fstat(fd)),final_positions=positions())
        if count!=SIZE or row['fd_before']!=row['fd_after']:anomaly(output,name,row,parts,'streambytecountormetadatachanged')
    dump(output/(name+'.json'),row);return row


def main():
    D=R/'read-contract085-057';D.mkdir(exist_ok=False);start=time.time();audit=json.loads(AUDIT.read_text());bad=Path(audit['bad_view_snapshot'])
    if bad.is_symlink() or bad==ORIGINAL or audit['read_bytes']!=2039480320 or bad.stat().st_size!=audit['read_bytes']:raise RuntimeError('Originalbadviewidentitychanged')
    original_before=stat(ORIGINAL.stat());original_mode=ORIGINAL.stat().st_mode&0o777
    if (bad.stat().st_dev,bad.stat().st_ino)==(ORIGINAL.stat().st_dev,ORIGINAL.stat().st_ino):raise RuntimeError('Badviewaliasesoriginalinode')
    mode_before=bad.stat().st_mode&0o777;bad.chmod(0o600) # diagnostic snapshot only
    result=dict(complete=False,diagnostic_only=True,numerical_acceptance=False,original_before=original_before,bad_view=str(bad),bad_mode_before=oct(mode_before),bad_mode_after=oct(bad.stat().st_mode&0o777),trace_may_perturb_reproduction=True)
    dump(D/'contract.json',result)
    try:
        br,ba,bb=prefix(bad,'badview-logical-prefix',D);orr,oa,ob=prefix(ORIGINAL,'original-logical-prefix',D)
        bg=gnu_prefix(bad,'badview-prefix',D);og=gnu_prefix(ORIGINAL,'original-prefix',D)
        result['prefixes']=dict(badview=br,original=orr,gnu_badview=bg,gnu_original=og,all_match_expected=br['openssl']==br['software']==orr['openssl']==orr['software']==bg['sha256']==og['sha256']==EXPECTED)
        fd=os.open(bad,os.O_RDONLY)
        try:extra=os.pread(fd,bad.stat().st_size-SIZE,SIZE)
        finally:os.close(fd)
        if len(extra)!=bad.stat().st_size-SIZE:anomaly(D,'badview-extra-tail',dict(requested=bad.stat().st_size-SIZE,returned=len(extra)),[extra],'badviewtailreadlengthcontractfailed')
        freq=[0]*256
        for value in extra:freq[value]+=1
        ba.update(extra);bb.update(extra)
        tail=dict(bytes=len(extra),sha=pair(extra),zero_ratio=freq[0]/len(extra),printable_ascii_ratio=sum(freq[32:127])/len(extra),byte_frequency=freq,
            recomposed_full_badview_openssl=ba.hexdigest(),recomposed_full_badview_software=bb.hexdigest(),raw_strings_or_hex_included=False)
        dump(D/'badview-extra-tail.json',tail);result['extra_tail']=tail
        result['exact_tail_eof']=exact_tail_and_eof(D)
        # Raw first; a raw OS-contract violation stops before buffered test.
        result['raw_eof']=stream_eof('original-unbuffered-eof',0,D)
        result['buffered_eof']=stream_eof('original-buffered-eof',-1,D)
        result['complete']=True
    except BaseException as error:
        result.update(complete=True,os_contract_anomaly=True,error=repr(error),traceback=traceback.format_exc());raise
    finally:
        result.update(seconds=time.time()-start,original_after=stat(ORIGINAL.stat()),original_mode_before=oct(original_mode),original_mode_after=oct(ORIGINAL.stat().st_mode&0o777),original_mode_unchanged=(ORIGINAL.stat().st_mode&0o777)==original_mode,source_modified=False,solver_executed=False)
        dump(D/'result.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('prefixes','extra_tail','raw_eof','buffered_eof')}),flush=True)


if __name__=='__main__':main()
