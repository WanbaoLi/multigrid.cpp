"""MPI2 shared-file round trip and actual PyQUDA file-contract test."""
from pathlib import Path
import shutil
import sys
import tempfile
import numpy as np
from mpi4py import MPI
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'python'))
from lqcd_cpu import columns_to_propagator, propagator_to_columns
from lqcd_cpu.propagator_io import write_propagator, read_propagator
from pyquda_comm import initGrid
from pyquda.field import LatticeInfo, LatticePropagator
from pyquda_utils.source import point

comm = MPI.COMM_WORLD
if comm.size != 2:raise SystemExit('test_propagator_io requires MPI2')
grid=(1,1,1,2);lat=(4,4,4,8);initGrid(grid_size=grid)
li=LatticeInfo(list(lat),-1,1.);coords=tuple(li.grid_coord)
base=comm.bcast(tempfile.mkdtemp(prefix='lqcd-propagator-io-') if comm.rank==0 else None,root=0)
path=Path(base)/'propagator.npy'
# Distinct spin/color entries expose swapping source and sink indices.
rng=np.random.default_rng(7913+comm.rank)
lex=(rng.standard_normal((*li.size[::-1],4,4,3,3))+1j*rng.standard_normal((*li.size[::-1],4,4,3,3))).astype(np.complex128)
def fails(fn):
    caught=False
    try:fn()
    except (ValueError,RuntimeError):caught=True
    assert comm.allreduce(int(caught))==comm.size
try:
    write_propagator(path,lex,lat,grid,coords,comm)
    read=read_propagator(path,lat,grid,coords,comm)
    assert np.array_equal(read,lex) and read.flags.c_contiguous
    read.flat[0]+=1
    assert not np.array_equal(read,lex)
    gathered=comm.gather(lex,root=0)
    if comm.rank==0:
        disk=np.load(path,allow_pickle=False)
        assert disk.shape==(*lat[::-1],4,4,3,3)
        assert disk.dtype==np.complex128
        assert np.array_equal(disk,np.concatenate(gathered,axis=0))
    # Real PyQUDA .load uses MPI-IO, then lexical->EO conversion.
    prop=LatticePropagator.load(str(path))
    expected=li.evenodd(lex,False)
    assert np.array_equal(prop.data,expected)
    columns=propagator_to_columns(prop.data)
    assert np.array_equal(columns_to_propagator(columns),expected)
    for spin in range(4):
        for color in range(3):assert np.array_equal(prop.getFermion(spin,color).data,columns[spin*3+color])
    # Nontrivial point on rank1, odd local parity and nonzero spin/color.
    source=point(li,[3,1,2,5],2,1)
    actual=source.data
    expected_source=np.zeros_like(actual)
    if coords[3]==1:expected_source[1,1,2,1,1,2,1]=1
    assert np.array_equal(actual,expected_source)
    fails(lambda:write_propagator(path,lex,lat,grid,coords,comm))
    assert np.array_equal(read_propagator(path,lat,grid,coords,comm),lex)
    fails(lambda:read_propagator(path,lat,grid,(0,0,0,0),comm))
    fails(lambda:read_propagator(path if comm.rank==0 else path.with_name('other.npy'),lat,grid,coords,comm))
    fails(lambda:write_propagator(Path(base)/'bad.npy',lex.astype(np.complex64) if comm.rank==0 else lex,lat,grid,coords,comm))
    bad=Path(base)/'bad-dtype.npy'
    if comm.rank==0:np.save(bad,np.zeros((*lat[::-1],4,4,3,3),dtype=np.complex64))
    comm.Barrier()
    fails(lambda:read_propagator(bad,lat,grid,coords,comm))
    if comm.rank==0:print('PASS: disjoint NPY slabs, PyQUDA load/columns, nontrivial point, overwrite/geometry/dtype rejection',flush=True)
finally:
    comm.Barrier()
    if comm.rank==0:shutil.rmtree(base)
