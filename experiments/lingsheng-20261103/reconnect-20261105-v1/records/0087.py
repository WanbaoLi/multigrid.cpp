#!/usr/bin/env python3
"""Read-only explicit-offset integrity protocol; no buffered file payload reads."""
import errno
import hashlib
import importlib
import json
import os
from pathlib import Path
import stat as stat_module
import time

METHOD = 'raw os.pread exact offsets/count/EOF; independent OpenSSL+CPython software SHA256 on same immutable bytes'
BLOCK = 4 * 1024**2


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def software_constructor():
    for name in ('_sha256', '_sha2'):
        try:
            constructor = importlib.import_module(name).sha256
            if type(constructor()).__module__ != type(hashlib.sha256()).__module__:
                return constructor
        except (ImportError, AttributeError):
            pass
    raise RuntimeError('Distinct CPython software SHA256 implementation required')


def known_vectors():
    constructor = software_constructor()
    require(type(hashlib.sha256()).__module__ == '_hashlib' and
            type(constructor()).__module__ in ('_sha256','_sha2'), 'Independent SHA implementations required')
    examples = [(b'', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
                (b'abc','ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'),
                (b'a'*1000000,'cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0')]
    for payload, expected in examples:
        a,b = hashlib.sha256(),constructor()
        for offset in range(0,len(payload),79):
            part=payload[offset:offset+79];a.update(part);b.update(part)
        require(a.hexdigest()==b.hexdigest()==expected,'SHA256 known-vector failure')
    return dict(openssl_module=type(hashlib.sha256()).__module__,
                software_module=type(constructor()).__module__, known_vectors_passed=len(examples))


def metadata(value):
    return dict(dev=value.st_dev,inode=value.st_ino,bytes=value.st_size,
                mtime_ns=value.st_mtime_ns,ctime_ns=value.st_ctime_ns)


def write_private_new(path, payload):
    fd = os.open(str(path), os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
    try:
        for data in payload:
            view = memoryview(data)
            while view:
                try:
                    written = os.write(fd,view)
                except InterruptedError:
                    continue
                require(written > 0, 'Short snapshot write')
                view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)


class IntegrityError(RuntimeError):
    def __init__(self, message, report):
        super().__init__(message)
        self.report = report


def checked_pread(fd, request, offset, pread):
    while True:
        try:
            data = pread(fd,request,offset)
            break
        except OSError as exc:
            if isinstance(exc,InterruptedError) or exc.errno == errno.EINTR:
                continue
            raise
    require(isinstance(data,bytes), 'pread must return immutable bytes')
    return data


def read_dual(path, expected=None, expected_size=None, block=BLOCK, capture_limit=2200*1024**2,
              snapshot=None, pread=None, fstat=None, path_stat=None):
    """All positive short reads are handled; oversize/early EOF/extra EOF strictly fail.

    Injection points are for small contract tests. The production path supplies
    none and always uses os.pread/os.fstat/Path.stat directly.
    """
    require(hasattr(os,'pread') or pread is not None,'os.pread required; no buffered fallback')
    require(type(block) is int and block>0,'Positive bounded block size required')
    path=Path(path)
    require(not path.is_symlink() and path.absolute()==path.resolve(strict=True),'Symlink path rejected')
    pread=pread or os.pread;fstat=fstat or os.fstat;path_stat=path_stat or (lambda:path.stat())
    before_path=metadata(path_stat())
    require(expected_size is None or before_path['bytes']==expected_size,'Recorded file size mismatch')
    size=before_path['bytes'];keep=snapshot is not None and size<=capture_limit
    held=[];count=0;calls=0;short_reads=0;eof_bytes=None;error=None
    a,b=hashlib.sha256(),software_constructor()()
    row=dict(complete=False,passed=False,path=str(path),method=METHOD,block_bytes=block,
             expected_sha256=expected,required_bytes=expected_size,initial=before_path,
             original_open_mode='O_RDONLY',same_immutable_bytes=True,started=time.time())
    fd=os.open(str(path),os.O_RDONLY|getattr(os,'O_CLOEXEC',0)|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_BINARY',0))
    try:
        fd_stat=fstat(fd)
        require(stat_module.S_ISREG(fd_stat.st_mode),'Regular file required')
        row['fd_before']=metadata(fd_stat)
        require(row['fd_before']==before_path,'Path/FD identity changed before read')
        offset=0
        while offset<size:
            request=min(block,size-offset)
            data=checked_pread(fd,request,offset,pread);calls+=1
            row.update(last_request_offset=offset,last_request_bytes=request,last_returned_bytes=len(data))
            if keep:held.append(data)
            require(0<len(data)<=request,'pread returned empty/oversized data before logical EOF')
            if len(data)<request:short_reads+=1
            a.update(data);b.update(data)
            offset+=len(data);count+=len(data)
        # Do not truncate an unexpected EOF view. Extra bytes are a hard failure.
        tail=checked_pread(fd,1,size,pread);calls+=1;eof_bytes=len(tail)
        row.update(last_request_offset=size,last_request_bytes=1,last_returned_bytes=len(tail))
        if tail and keep:held.append(tail)
        require(tail==b'','pread returned data beyond recorded logical EOF')
    except BaseException as exc:
        error=exc
    finally:
        try:
            row['fd_after']=metadata(fstat(fd))
            row['path_after']=metadata(path_stat())
        finally:
            os.close(fd)
    row.update(complete=True,read_bytes=count,pread_calls=calls,positive_short_reads=short_reads,
               eof_probe_bytes=eof_bytes,openssl_sha256=a.hexdigest(),software_sha256=b.hexdigest(),
               seconds=time.time()-row['started'])
    row['metadata_stable']=row.get('fd_before')==row.get('fd_after')==before_path==row.get('path_after')
    row['byte_count_exact']=count==size and (expected_size is None or count==expected_size)
    row['passed']=error is None and row['metadata_stable'] and row['byte_count_exact'] and eof_bytes==0 and \
                  row['openssl_sha256']==row['software_sha256'] and (expected is None or row['openssl_sha256']==expected)
    if not row['passed']:
        row['error']=str(error) if error else 'Strict digest/identity/count/EOF gate failed'
        if keep and sum(map(len,held))<=capture_limit:
            write_private_new(snapshot,held)
            row['bad_view_snapshot']=str(snapshot)
            row['bad_view_bytes']=sum(map(len,held))
            row['snapshot_exact_held_bytes']=True
            row['snapshot_mode']='0600'
        elif keep:
            row['mismatch_capture_skipped']='Actual returned byte view exceeded the explicit retention budget'
        raise IntegrityError(row['error'],row) from error
    return row


def small_dual(payload):
    require(isinstance(payload,bytes),'Immutable manifest bytes required')
    a,b=hashlib.sha256(payload),software_constructor()(payload)
    require(a.hexdigest()==b.hexdigest(),'Manifest SHA implementations disagree')
    return a.hexdigest()


def write_json_private(path,value):
    write_private_new(path,[ (json.dumps(value,indent=2,allow_nan=False)+'\n').encode() ])
