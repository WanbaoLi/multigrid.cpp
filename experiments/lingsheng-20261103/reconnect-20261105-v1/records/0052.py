#!/usr/bin/env python3
"""Single-host, affinity-aware MPI/OpenMP NUMA launcher (Open MPI or MPICH/Hydra).

Commands are argv, never shell strings. {ranks}, {threads}, and {node} arguments
are substituted in each rank. Use --dry-run to inspect the complete placement.
"""

import argparse
import json
import os
from pathlib import Path
import shlex
import socket
import subprocess
import sys


def parse_cpu_list(value):
    result = set()
    for item in value.strip().split(","):
        if not item:
            continue
        bounds = item.split("-")
        if len(bounds) == 1:
            result.add(int(item))
        elif len(bounds) == 2:
            first, last = map(int, bounds)
            if first > last:
                raise ValueError("descending CPU/node range")
            result.update(range(first, last + 1))
        else:
            raise ValueError("invalid CPU/node range")
    return sorted(result)


def discover_nodes(sysfs=Path("/sys/devices/system"), allowed=None):
    allowed = set(os.sched_getaffinity(0) if allowed is None else allowed)
    nodes = {}
    for directory in sorted((sysfs / "node").glob("node[0-9]*")):
        node = int(directory.name[4:])
        cpus = allowed.intersection(parse_cpu_list((directory / "cpulist").read_text()))
        physical = {}
        for cpu in sorted(cpus):
            topology = sysfs / "cpu" / f"cpu{cpu}" / "topology"
            siblings = topology / "thread_siblings_list"
            if siblings.is_file():
                # Canonical physical-core identity, independent of whether the
                # first sibling is online/allowed in this rank's cpuset.
                group = tuple(parse_cpu_list(siblings.read_text()))
                if not group or cpu not in group:
                    raise ValueError(f"invalid thread_siblings_list for CPU {cpu}")
                key = ("siblings", group)
            else:
                # Some systems reuse core_id across dies of one package.
                die = topology / "die_id"
                key = (
                    "topology",
                    int((topology / "physical_package_id").read_text()),
                    int(die.read_text()) if die.is_file() else None,
                    int((topology / "core_id").read_text()),
                )
            physical.setdefault(key, cpu)
        if physical:
            nodes[node] = sorted(physical.values())
    if not nodes:
        raise ValueError("no allowed physical CPUs found in Linux NUMA sysfs")
    return nodes


def make_plan(nodes, lattice, block, selected=None, threads=None, ranks_per_numa=1):
    selected = sorted(nodes) if selected is None else selected
    if not selected or len(set(selected)) != len(selected):
        raise ValueError("select at least one distinct NUMA node")
    if any(node not in nodes for node in selected):
        raise ValueError("selected NUMA node has no allowed physical CPUs")
    if isinstance(ranks_per_numa, bool) or not isinstance(ranks_per_numa, int) or ranks_per_numa < 1:
        raise ValueError("--ranks-per-numa must be a positive integer")
    if threads is not None and (isinstance(threads, bool) or not isinstance(threads, int) or threads < 1):
        raise ValueError("--threads must be a positive integer per MPI process")
    ranks = len(selected) * ranks_per_numa
    if any(n <= 0 or b <= 0 or n % b for n, b in zip(lattice, block)):
        raise ValueError(
            "positive lattice extents must be divisible by aggregate extents"
        )
    if any(n // b < 4 or (n // b) % 2 for n, b in zip(lattice, block)):
        raise ValueError("native SAP requires even coarse extents >=4")
    if any(n % 2 for n in lattice):
        raise ValueError("all global lattice extents must be even")
    if lattice[3] % ranks or (lattice[3] // ranks) % block[3]:
        raise ValueError(
            "t-slab ranks must divide Lt and leave complete time aggregates"
        )
    if (lattice[3] // ranks) % 2:
        raise ValueError("all local lattice extents must be even")
    counts = [len(nodes[node]) for node in selected]
    if any(count < ranks_per_numa for count in counts) or (threads is not None and
            any(threads * ranks_per_numa > count for count in counts)):
        raise ValueError("MPI processes and --threads must fit the allowed physical cores of every selected NUMA node")
    placement = []
    for node in selected:
        cpus = nodes[node]
        start = 0
        for partition in range(ranks_per_numa):
            # Spread remainder cores across the first partitions, never discard
            # allowed cores unless an explicit thread count requests fewer.
            count = (threads if threads is not None else
                     len(cpus) // ranks_per_numa + int(partition < len(cpus) % ranks_per_numa))
            placement.append(dict(rank=len(placement), node=node,
                                  numa_partition=partition, ranks_per_numa=ranks_per_numa,
                                  cpus=cpus[start:start + count],
                                  available_physical_cores=len(cpus)))
            start += count
    return {
        "ranks": ranks,
        "ranks_per_numa": ranks_per_numa,
        "threads_per_rank": [len(p["cpus"]) for p in placement],
        "grid": [1, 1, 1, ranks],
        "lattice": list(lattice),
        "block": list(block),
        "host": socket.gethostname(),
        "placement": placement,
    }


def rank_environment(placement):
    cpus = placement["cpus"]
    return {
        "OMP_NUM_THREADS": str(len(cpus)),
        "OMP_DYNAMIC": "FALSE",
        "OMP_PROC_BIND": "close",
        "OMP_PLACES": ",".join("{%d}" % cpu for cpu in cpus),
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "LQCD_NUMA_NODE": str(placement["node"]),
        "LQCD_CPU_THREADS": str(len(cpus)),
    }


def rank_placement(plan, environment, hostname):
    if hostname != plan["host"]:
        raise ValueError(
            "this launcher is single-host only; remote NUMA discovery is not implemented"
        )
    pairs = (("OMPI_COMM_WORLD_RANK", "OMPI_COMM_WORLD_SIZE"),
             ("PMI_RANK", "PMI_SIZE"))
    identities = []
    for rank_key, size_key in pairs:
        if rank_key in environment or size_key in environment:
            if rank_key not in environment or size_key not in environment:
                raise ValueError("incomplete MPI rank/size environment")
            identities.append((int(environment[rank_key]), int(environment[size_key])))
    if not identities:
        raise ValueError("internal rank mode requires Open MPI or MPICH PMI rank/size")
    if any(identity != identities[0] for identity in identities):
        raise ValueError("conflicting MPI rank environments")
    rank, size = identities[0]
    if size != plan["ranks"]:
        raise ValueError("MPI world size disagrees with placement plan")
    if not 0 <= rank < plan["ranks"]:
        raise ValueError("MPI rank is outside placement plan")
    placement = plan["placement"][rank]
    if (
        placement["rank"] != rank
        or not placement["cpus"]
        or len(set(placement["cpus"])) != len(placement["cpus"])
    ):
        raise ValueError("invalid rank placement metadata")
    return placement


def rank_exec(plan, command):
    if not command:
        raise ValueError("internal rank mode requires a command")
    placement = rank_placement(plan, os.environ, socket.gethostname())
    cpus = set(placement["cpus"])
    if not cpus.issubset(os.sched_getaffinity(0)):
        raise ValueError(
            "MPI/host affinity excludes planned CPUs; do not add MPI CPU binding"
        )
    os.sched_setaffinity(0, cpus)
    os.environ.update(rank_environment(placement))
    # Explicit CPU affinity gives first-touch NUMA placement without requiring
    # numactl/set_mempolicy privileges. Inherited interleave policies must be unset.
    substitutions = {
        "{ranks}": str(plan["ranks"]),
        "{threads}": str(len(cpus)),
        "{node}": str(placement["node"]),
    }
    argv = [substitutions.get(arg, arg) for arg in command]
    os.execvpe(argv[0], argv, os.environ)


def detect_launcher(executable):
    """Identify launch syntax without launching ranks; never guess from filename."""
    for option in ("--version", "-version"):
        try:
            result = subprocess.run([executable, option], capture_output=True,
                                    text=True, timeout=10, check=False)
        except subprocess.TimeoutExpired:
            continue
        banner = (result.stdout + result.stderr).lower()
        if result.returncode == 0:
            if any(name in banner for name in ("open mpi", "openrte", "prrte")):
                return "openmpi"
            if "hydra" in banner or "mpich" in banner:
                return "mpich"
    raise ValueError("unrecognized MPI launcher; supported: Open MPI and MPICH/Hydra")


def launcher_prefix(executable, family, ranks):
    if family == "openmpi":
        return [executable, "--host", f"localhost:{ranks}", "-n", str(ranks),
                "--bind-to", "none"]
    if family == "mpich":
        # Hydra's fork launcher and user resource manager constrain execution
        # to this host even inside a multi-node scheduler allocation. Python
        # sets each rank's affinity; Hydra must not pre-bind it to one core.
        return [executable, "-n", str(ranks), "-bind-to", "none",
                "-launcher", "fork", "-rmk", "user"]
    raise ValueError("unsupported MPI launcher family")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--_rank":
        if len(sys.argv) < 4:
            raise ValueError("internal rank mode requires a plan and command")
        rank_exec(json.loads(sys.argv[2]), sys.argv[3:])
        return
    if any(
        key in os.environ for key in ("OMPI_COMM_WORLD_RANK", "PMI_RANK", "PMIX_RANK")
    ):
        raise ValueError(
            "run_numa starts MPI itself; do not invoke it inside an existing MPI job"
        )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lattice",
        nargs=4,
        type=int,
        default=[24, 24, 24, 64],
        metavar=("X", "Y", "Z", "T"),
    )
    parser.add_argument("--block", nargs=4, type=int, default=[6, 6, 6, 4])
    parser.add_argument(
        "--numa-nodes",
        type=parse_cpu_list,
        help="allowed NUMA IDs, e.g. 0,2-3 (default all available)",
    )
    parser.add_argument(
        "--threads",
        type=int,
        help="OpenMP threads per MPI process (default evenly partition allowed physical cores within each NUMA)",
    )
    parser.add_argument(
        "--mpirun",
        default="mpirun",
        help="Open MPI or MPICH/Hydra executable matching application mpi4py",
    )
    parser.add_argument("--ranks-per-numa", type=int, default=1,
                        help="MPI processes per NUMA domain, each assigned disjoint physical cores (default1)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="-- executable args; standalone {ranks}/{threads}/{node} are expanded",
    )
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("a command after -- is required")
    plan = make_plan(
        discover_nodes(), args.lattice, args.block, args.numa_nodes, args.threads, args.ranks_per_numa
    )
    family = detect_launcher(args.mpirun)
    argv = launcher_prefix(args.mpirun, family, plan["ranks"]) + [
        sys.executable,
        str(Path(__file__).resolve()),
        "--_rank",
        json.dumps(plan, separators=(",", ":")),
        *command,
    ]
    print(
        json.dumps(
            {
                "mpi_launcher": family,
                "topology": plan,
                "rank_environments": [rank_environment(p) for p in plan["placement"]],
                "launch_command": shlex.join(argv),
            },
            indent=2,
        ),
        flush=True,
    )
    if not args.dry_run:
        os.execvp(argv[0], argv)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError) as error:
        sys.exit(f"run_numa: {error}")
