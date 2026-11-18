#!/usr/bin/env python3
"""Generate explicitly small-volume, exact-determinant Nf=2+1 Clover HMC fields."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from hmc.reference import CloverHMC, RD, write_lime


def atomic_json(path, obj):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')
    tmp.replace(path)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--lattice', type=int, nargs=4, default=(2, 2, 2, 2))
    p.add_argument('--beta', type=float, default=5.6)
    p.add_argument('--mass-light', type=float, default=0.5)
    p.add_argument('--mass-strange', type=float, default=0.8)
    p.add_argument('--csw', type=float, default=1.0)
    p.add_argument('--length', type=float, default=0.5)
    p.add_argument('--steps', type=int, default=10)
    p.add_argument('--integrator', choices=('leapfrog', 'omelyan'), default='leapfrog')
    p.add_argument('--warmup', type=int, default=40)
    p.add_argument('--trajectories', type=int, default=80)
    p.add_argument('--save-every', type=int, default=10)
    p.add_argument('--seed', type=int, default=1729)
    p.add_argument('--threads', type=int, default=2)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        p.error('Output must be new; never overwrite a chain')
    if (not 0 <= args.warmup < args.trajectories or args.save_every < 1 or args.steps < 1
            or args.length <= 0 or not math.isfinite(args.length) or args.threads < 1
            or args.save_every > args.trajectories - args.warmup):
        p.error('Invalid trajectory, warmup, save interval or integration parameters')
    torch.set_num_threads(args.threads)
    model = CloverHMC(args.lattice, args.beta, args.mass_light, args.mass_strange, args.csw)
    args.output.mkdir(parents=True)
    rng = torch.Generator().manual_seed(args.seed)
    u = model.cold()
    report = dict(complete=False, algorithm=f'exact dense determinant HMC, {args.integrator} + Metropolis',
                  target='exp(-Sg) det(M_light)^2 det(M_strange), positive strange determinant required',
                  nf='2+1', lattice_xyzt=args.lattice, beta=args.beta, mass_light=args.mass_light,
                  mass_strange=args.mass_strange, csw=args.csw, gauge_action='Wilson plaquette',
                  fermion_operator='normalized Wilson-Clover, DeGrand-Rossi spin basis',
                  gauge_t_boundary=1, fermion_t_boundary=-1, stout_steps=0,
                  precision='complex128/float64 CPU', dense_operator_dimension=12 * model.volume,
                  pseudofermions=False, rhmc=False, mg_used=False, seed=args.seed,
                  trajectory_length=args.length, integration_steps=args.steps, threads=args.threads,
                  requested_trajectories=args.trajectories, requested_warmup=args.warmup,
                  thermalization_established=False, independent_samples_established=False,
                  intended_use='small-volume algorithm verification; not a physical-point production ensemble',
                  host=platform.node(), torch_version=torch.__version__,
                  source_commit=subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip(),
                  source_branch=subprocess.check_output(['git', '-C', str(ROOT), 'branch', '--show-current'], text=True).strip(),
                  source_tracked_status=subprocess.check_output(['git', '-C', str(ROOT), 'status', '--porcelain', '--untracked-files=no'], text=True),
                  samples=[], saved_configurations=[])
    if report['source_tracked_status']:
        raise RuntimeError('Refuse a modified tracked source checkout')
    started = time.perf_counter()
    for trajectory in range(1, args.trajectories + 1):
        t = time.perf_counter()
        u, item = model.trajectory(u, rng, args.length, args.steps, args.integrator)
        item.update(trajectory=trajectory, warmup=trajectory <= args.warmup,
                    seconds=time.perf_counter() - t, **model.observables(u))
        report['samples'].append(item)
        if trajectory > args.warmup and (trajectory - args.warmup) % args.save_every == 0:
            filename = 'hmc_%06d.lime' % trajectory
            path = args.output / filename
            write_lime(path, u.numpy(), args.lattice,
                       {k: report[k] for k in ('nf', 'beta', 'mass_light', 'mass_strange', 'csw', 'source_commit', 'seed')})
            report['saved_configurations'].append(dict(file=filename, trajectory=trajectory,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(), bytes=path.stat().st_size,
                **model.observables(u)))
            torch.save(dict(gauge=u, rng_state=rng.get_state(), trajectory=trajectory,
                            source_commit=report['source_commit']), args.output / 'latest-state.pt')
        atomic_json(args.output / 'result.json', report)
        print(json.dumps(item), flush=True)
    production = [s for s in report['samples'] if not s['warmup']]
    report.update(complete=True, elapsed_seconds=time.perf_counter() - started,
                  acceptance_rate=sum(s['accepted'] for s in report['samples']) / args.trajectories,
                  production_acceptance_rate=sum(s['accepted'] for s in production) / len(production),
                  production_mean_exp_minus_delta_h=sum(math.exp(-s['delta_h']) for s in production) / len(production),
                  production_mean_plaquette=sum(s['plaquette'] for s in production) / len(production))
    atomic_json(args.output / 'result.json', report)
    if not report['saved_configurations'] or not any(s['accepted'] for s in production):
        raise RuntimeError('No nontrivial production update or no saved fields')


if __name__ == '__main__':
    main()
