"""Version the unexecuted profiler prototype with site-compatible perf decoding."""
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

root=Path(__file__).parent
target=root/'solve-profile-v7-helpers'
target.mkdir(exist_ok=False)
old=json.loads((root/'solve-profile-v6-helpers/solve-profile-v6-files.json').read_text())
for name,expected in old['files'].items():
    if '_v6.py'in name:continue
    source=root/'solve-profile-v6-helpers'/name
    assert hashlib.sha256(source.read_bytes()).hexdigest()==expected
    shutil.copyfile(source,target/name)
names=['profile_benchmark_publication','raw_controller_solve_profile','prepare_solve_profile','solve_profile_scope','test_solve_profile']
for stem in names:
    text=(root/(stem+'_v6.py')).read_text().replace('_v6','_v7').replace('-v6','-v7').replace('_V6','_V7')
    if stem=='profile_benchmark_publication':
        assert text.count('comm,pid,tid,dso,symbol')==1
        text=text.replace('comm,pid,tid,dso,symbol','comm,pid,dso,symbol')
        text=text.replace("flat_decode_call_graph='none'", "flat_decode_call_graph='none',\n            thread_key='pid (perf5.10 command and task TID; not a tid sort key)',\n            thread_key_primary_source='https://raw.githubusercontent.com/torvalds/linux/v5.10/tools/perf/Documentation/perf-report.txt'")
    if stem=='prepare_solve_profile':
        before="""    if not(state.get('complete')is True and state.get('status')=='complete'):
        reasons.append('Phase5 is not complete; keep its pending/failed state')
    if not(status.get('status')=='passed'and type(status.get('returncode'))is int and status['returncode']==0 and
        status.get('task_tag')and status.get('cleanup',{}).get('complete')is True and status.get('cleanup',{}).get('surviving_pids')==[]):
        reasons.append('Phase5 task must pass and clean all owned processes')"""
        after="""    # A diagnostic of the unchanged accepted best does not require adopting
    # or completing a failed comparison. Retain that failure, require its exact
    # terminal task outcome and cleanup, and never rank profile timings.
    passed=state.get('complete')is True and state.get('status')=='complete'and status.get('status')=='passed'and status.get('returncode')==0
    failed=state.get('complete')is False and state.get('status')=='failed'and status.get('status')=='failed'and type(status.get('returncode'))is int and status['returncode']!=0
    if not(passed or failed):reasons.append('Prior phase must be terminal; pending/running state is retained')
    if not(type(status.get('returncode'))is int and status.get('task_tag')and
        status.get('cleanup',{}).get('complete')is True and status.get('cleanup',{}).get('surviving_pids')==[]):
        reasons.append('Prior task must have exact terminal return code and clean all owned processes')"""
        assert before in text;text=text.replace(before,after)
        text=text.replace("task_timeout_seconds=BUDGET,original_trial_stage_caps_preserved=True)","task_timeout_seconds=BUDGET,original_trial_stage_caps_preserved=True,\n                prior_phase_status=state.get('status'),prior_failure_not_reclassified=True)")
    if stem=='test_solve_profile':
        text=text.replace("self.assertIn('--no-children',argv);self.assertIn('none',argv)","self.assertIn('--no-children',argv);self.assertIn('none',argv)\n                self.assertIn('comm,pid,dso,symbol',argv);self.assertNotIn('comm,pid,tid,dso,symbol',argv)")
        needle="    def test_dispatch_rechecks_full_parent_runtime_host_and_deadline(self):"
        addition="""    def test_failed_phase_is_retained_but_clean_terminal_task_allows_unranked_best_profile(self):
        state=dict(complete=False,status='failed',expected_best='best',contract=dict(host='cn',allocation='new'))
        status=dict(status='failed',returncode=1,task_tag='owned',host='cn',cleanup=dict(complete=True,surviving_pids=[]))
        startup=dict(complete=True,host='cn',allocation='new',safe_deadline_epoch=5000)
        gate=prepare.readiness(state,status,startup,dict(attempt='best'),1000)
        self.assertTrue(gate['passed']);self.assertTrue(gate['prior_failure_not_reclassified'])
        self.assertEqual(state['status'],'failed');self.assertFalse(state['complete'])
        for changed in (dict(status,status='running'),dict(status,returncode=0),dict(status,returncode=True),
                        dict(status,cleanup=dict(complete=True,surviving_pids=[42]))):
            self.assertFalse(prepare.readiness(state,changed,startup,dict(attempt='best'),1000)['passed'])

"""
        assert needle in text;text=text.replace(needle,addition+needle)
    (target/(stem+'_v7.py')).write_text(text,newline='\n')
manifest=dict(files={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(target.glob('*.py'))},
    prepared_not_executed=True,profile_scope='auxiliary sampled final verbose call only; ordinary promotion prohibited',
    compatibility='perf5.10 pid sort key contains task TID; verified on old data before dispatch',
    preceding_failed_phase='Terminal clean failure may permit an unchanged-best diagnostic; failure retained, no performance acceptance')
mp=target/'solve-profile-v7-files.json';mp.write_text(json.dumps(manifest,indent=2)+'\n',newline='\n')
archive=root/'solve-profile-v7-helpers.tgz'
with tarfile.open(archive,'w:gz')as tar:
    for p in sorted(target.iterdir()):tar.add(p,arcname=p.name)
print(json.dumps(dict(files=len(manifest['files']),manifest_sha256=hashlib.sha256(mp.read_bytes()).hexdigest(),
    archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest()),indent=2))
