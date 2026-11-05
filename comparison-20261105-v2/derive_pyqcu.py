"""Derive a repeated, same-context timing driver; leave original unchanged."""
from pathlib import Path
root=Path('/home/share/nsls_lwb/.cache/fair-solve-20261105-v2')
original=Path('/home/share/nsls_lwb/.cache/pyqcu-propagator24-v20261103/benchmark_propagator12.py').read_text()
begin=original.index('        # Store the 12 outputs')
end=original.index('        report["memory_by_rank"]',begin)
body=original[begin:end]
# Reuse init/Clover, but repeat complete12 solves from zero. Verification remains
# outside every solve timer; include all same-column correction solve timers.
body='        report["samples"] = []\n        for repetition in range(1 if __import__("os").environ.get("FAIR_PILOT")=="1" else 4):\n'+''.join('    '+s+'\n'for s in body.splitlines())
body=body.replace('            saved = []','            report["columns"] = []\n            saved = []')
body+='            report["samples"].append({"repeat":repetition,"warmup":repetition==0,"native_seconds":timings["native_solve_sum_seconds"],"max_residual":report["max_independent_true_relative_residual"],"restarts":report["residual_restart_count_total"],"columns":[dict(c) for c in report["columns"]]})\n'
body+='            if report["status"] != "PASS": raise RuntimeError("Full12 precision gate failed")\n'
body+='            if rank==0: atomic_json(args.report,report)\n'
body+='        from pyqcu.testing.simple._common import kupl_fermion_to_qcu\n'
body+='        column0=kupl_fermion_to_qcu(saved[0]).transpose(5,4,3,2,0,1)/3.723\n'
body+='        np.save(args.report.parent/("column0-rank%05d.npy"%rank),np.ascontiguousarray(column0))\n'
target=root/'pyqcu_repeated.py';assert not target.exists();target.write_text(original[:begin]+body+original[end:])
entry=Path('/home/share/nsls_lwb/.cache/pyqcu-kunpeng-recheck/bound_entry.py').read_text()
entry=entry.replace('/home/share/nsls_lwb/.cache/pyqcu-propagator24-v20261103/benchmark_propagator12.py',str(target))
(root/'pyqcu_entry.py').write_text(entry)
print('DERIVED_REPEATED_DRIVER_READY')

