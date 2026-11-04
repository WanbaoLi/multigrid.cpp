"""New read/publication boundary around frozen c5 phase5 experiment.

All eight trials, fixed-team/runtime ordering and performance/precision gates
remain inherited. This entry is preparation only until explicitly dispatched.
"""
import importlib
import importlib.util
import os
from pathlib import Path
import sys
import time

import file_integrity as integrity
import raw_protocol_publication_v2 as protocol

BASE_SHA='c5a8a8b3c14d697c9062bf04172e2eb616ffebda66298a99aa123ca80419d9fe'
FACTORY_SHA='b94f04ff48ebefd075cefe770d49e9b6093f3baa50fc2f8261e73319f1e0fe36'
AUDITOR_SHA='1264d37ee7e05ae6247a7770351c426ab3c01324ef14d01f8abe614deb6a9103'
COMPATIBILITY_DSOS=('libpthread.so','libdl.so')


def sha(path):
    return integrity.read_dual(Path(path))['openssl_sha256']


def load_base():
    path=Path(__file__).with_name('phase5_validation_shim.py')
    integrity.read_dual(path,BASE_SHA)
    spec=importlib.util.spec_from_file_location('_frozen_phase5_c5_worker7',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


base=load_base()


class SetupObserver(base.SetupObserver):
    def libraries(self,pid,deadline):
        """Observe all mapped shared files; bounded strict SHA, no library load."""
        rows={}
        for line in (Path('/proc')/str(pid)/'maps').read_text().splitlines():
            fields=line.split(None,5)
            if len(fields)!=6 or not fields[5].startswith('/'):continue
            path=Path(fields[5])
            if '.so'not in path.name and base.library_family(path.name)is None:continue
            if self.stop_event.is_set()or time.time()>deadline:raise TimeoutError('Setup observer window expired')
            path=path.resolve(strict=True);stat=path.stat()
            key=(str(path),stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns)
            if key not in self.cache:self.cache[key]=sha(path)
            if self.stop_event.is_set()or time.time()>deadline:raise TimeoutError('Strict map checksum crossed setup window')
            rows[str(path)]=dict(path=str(path),sha256=self.cache[key],bytes=stat.st_size)
        result=sorted(rows.values(),key=lambda row:row['path'])
        if not all(sum(base.library_family(Path(row['path']).name)==family for row in result)==1
            for family in ('gomp','stdcpp','gcc','libc','mpi','solver')):return None
        return result


def other_shared_identity(libraries):
    """Compatibility libpthread/dl DSOs may disappear when old GOMP uses libc."""
    return sorted((row['path'],row['sha256'])for row in libraries
        if not Path(row['path']).name.startswith(('libgomp.so',*COMPATIBILITY_DSOS)))


class Phase5(base.Phase5):
    def __init__(self,args):
        tools=args.root.resolve()/'source/tools/optimization';sys.path.insert(0,str(tools))
        ledger=importlib.import_module('campaign')
        integrity.require(Path(ledger.__file__).resolve()==tools/'campaign.py','Mixed frozen campaign module')
        ledger.digest=sha  # file-read boundary only; no saved expected digest changes
        super().__init__(args)
        manifest=self.shim_manifest;binding=manifest.get('worker_startup',{})
        self.require(manifest.get('manifest_revision')==3 and manifest.get('other_solver_closure_unchanged')is True,
            'New inspected worker7 runtime manifest required; oldc3f is retained, not rewritten')
        self.require(binding.get('host')==self.host and binding.get('allocation')==self.allocation,
            'Runtime manifest belongs to another worker epoch')
        integrity.read_dual(binding['path'],binding['sha256'])
        auxiliary=Path(__file__).resolve().parent
        integrity.read_dual(protocol.__file__,FACTORY_SHA);protocol.verify_files(auxiliary)
        audit_path=auxiliary/'owned_publication_audit_v3.py';integrity.read_dual(audit_path,AUDITOR_SHA)
        spec=importlib.util.spec_from_file_location('_phase5_worker7_publication_audit',audit_path)
        self.publication_audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.publication_audit)
        self.auxiliary=auxiliary;self.publication_files=protocol.FILES
        extra=dict(entry_sha256=sha(__file__),base_controller_sha256=BASE_SHA,factory_sha256=FACTORY_SHA,
            publication_auditor_sha256=AUDITOR_SHA,shared_map_scope='All observed file-backed shared objects; exclude only GOMP and documented libpthread/libdl compatibility DSOs from cross-case signature',
            immutable_reader='Strict fixed-offset dualSHA; no expected digest changes',
            scientific_methods='All inherited c5 ordering, samples, precision and two-control gates unchanged')
        previous=self.state.get('worker7_v3_contract')
        self.require(previous is None or previous==extra,'Worker7v3 driver boundary changed; retain old state')
        self.state['worker7_v3_contract']=extra;self.save()

    def registered(self,name,expected):
        result=super().registered(name,expected)
        if result is None:return None
        _,report,_=result;path=self.campaign/'attempts'/name
        receipts=self.publication_audit.warm(path,path/'measurements/full12',report,
            self.auxiliary,sha,self.publication_files)
        saved=self.state.setdefault('fresh_publication_checkpoints',{}).get(name)
        self.require(saved is None or saved==receipts,'Published fresh proof changed after checkpoint')
        self.state['fresh_publication_checkpoints'][name]=receipts;self.save()
        return result

    def runtime_audit(self,group,names):
        result=super().runtime_audit(group,names)
        signatures=[];issues=group['runtime_audit']['issues']
        for name in names:
            path=Path(group['trials'][name]['runtime_audit_path'])
            if not path.is_file()or path.is_symlink():continue
            audit=self.ledger.read(path)
            for rank in audit.get('ranks',[]):
                libraries=rank.get('libraries',[])
                if group['base_configuration']['context_environment'].get('LQCD_HBW_ALLOC')=='require':
                    if not any(Path(row['path']).name.startswith('libkupl.so')for row in libraries):
                        issues.append(name+': HBW runtime map missing KUPL')
                signatures.append(other_shared_identity(libraries))
        if not signatures or any(value!=signatures[0]for value in signatures):
            issues.append('Non-GOMP observed shared-object closure differs; cannot isolate runtime change')
        group['runtime_audit'].update(complete=not issues,all_shared_object_signatures=signatures,
            compatibility_dso_exceptions=list(COMPATIBILITY_DSOS))
        self.save();return result and not issues


def main():
    base.SetupObserver=SetupObserver;base.Phase5=Phase5
    base.main()


if __name__=='__main__':main()
