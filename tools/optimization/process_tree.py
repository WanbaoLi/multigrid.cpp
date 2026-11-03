"""Bounded cleanup of this experiment's processes, including detached sessions.

Never select a process by command name or dump /proc/*/environ. Ownership is a
same-UID exact random environment tag or a verified parent/child relationship;
PID start times are rechecked immediately before each individual signal.
"""
import contextlib
import ctypes
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
import uuid

TASK_KEY = 'LQCD_OPT_TASK_ID'
STAGE_KEY = 'LQCD_OPT_STAGE_ID'


def new_tag():
    return uuid.uuid4().hex


def enable_subreaper():
    if not sys.platform.startswith('linux'):
        return False
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(36, 1, 0, 0, 0):  # PR_SET_CHILD_SUBREAPER
        raise OSError(ctypes.get_errno(), 'Cannot enable owned-child reaping')
    return True


def identity(pid):
    try:
        directory = Path('/proc') / str(pid)
        if directory.stat().st_uid != os.geteuid():
            return None
        text = (directory / 'stat').read_text()
        fields = text[text.rfind(')')+2:].split()
        return dict(pid=int(pid), ppid=int(fields[1]), pgid=int(fields[2]),
                    state=fields[0], starttime=int(fields[19]))
    except (OSError, ValueError, IndexError):
        return None


def discover(root_pid, known, tag_key=None, tag=None):
    records = {}
    marker = (tag_key+'='+tag).encode() if tag_key and tag else None
    for directory in Path('/proc').iterdir():
        if not directory.name.isdigit():
            continue
        item = identity(int(directory.name))
        if not item or item['pid'] == os.getpid():
            continue
        records[item['pid']] = item
        previous = known.get(item['pid'])
        if previous and previous['starttime'] == item['starttime']:
            known[item['pid']] = item
            continue
        if marker:
            try:
                # Read only to test exact membership. No contents enter logs.
                match = marker in (directory / 'environ').read_bytes().split(b'\0')
            except OSError:
                match = False
            if match:
                known[item['pid']] = item
    # Capture descendants before signalling parents. Detached descendants that
    # have reparented are still found by the inherited exact tag above.
    changed = True
    while changed:
        changed = False
        for pid, item in records.items():
            parent = known.get(item['ppid'])
            actual_parent = records.get(item['ppid'])
            if pid not in known and parent and actual_parent and parent['starttime'] == actual_parent['starttime']:
                known[pid] = item
                changed = True
    return known


def alive(known):
    result = []
    for pid, old in known.items():
        item = identity(pid)
        if item and item['starttime'] == old['starttime'] and item['state'] != 'Z':
            result.append(item)
    return result


def signal_owned(items, sig):
    sent = []
    for item in items:
        current = identity(item['pid'])
        if not current or current['starttime'] != item['starttime'] or current['state'] == 'Z':
            continue
        try:
            os.kill(item['pid'], sig)
            sent.append((item['pid'], item['starttime']))
        except (ProcessLookupError, PermissionError):
            pass
    return sent


def reap(known, root_pid):
    for pid in known:
        if pid == root_pid:
            continue  # subprocess.Popen owns and reaps the direct child.
        try:
            os.waitpid(pid, os.WNOHANG)
        except (ChildProcessError, ProcessLookupError):
            pass


def tagged_processes(tag_key, tag):
    if not sys.platform.startswith('linux'):
        return []
    return alive(discover(-1,{},tag_key,tag))


@contextlib.contextmanager
def ignore_interrupts():
    previous = {}
    if threading.current_thread() is threading.main_thread():
        for sig in (signal.SIGINT, signal.SIGTERM):
            previous[sig] = signal.signal(sig, signal.SIG_IGN)
    try:
        yield
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def terminate_owned(process, tag_key=None, tag=None, grace=10):
    """Clean all observable owned work before reporting a task terminal.

    Detached grandchildren do not have to remain in process.pid's group. A
    cleanup failure is explicit and must stop the queue, never start next work.
    """
    with ignore_interrupts():
        if not sys.platform.startswith('linux'):
            if process.poll() is None:
                subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],
                               stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
            process.wait()
            return dict(complete=True, platform=sys.platform, method='taskkill-tree',
                        surviving_pids=[])
        known, term_sent, kill_sent = {}, set(), set()
        # A Popen child which has not been reaped cannot have its PID reused.
        # Once its identity is captured, later scans must match starttime.
        if process.poll() is None:
            root = identity(process.pid)
            if root:
                known[process.pid] = root
        discover(process.pid, known, tag_key, tag)
        deadline = time.monotonic()+grace
        while True:
            discover(process.pid, known, tag_key, tag)
            current = alive(known)
            unsignalled = [item for item in current if (item['pid'],item['starttime']) not in term_sent]
            term_sent.update(signal_owned(unsignalled,signal.SIGTERM))
            process.poll()
            reap(known,process.pid)
            if not alive(known) or time.monotonic() >= deadline:
                break
            time.sleep(.05)
        # Repeated scans catch children spawned by a termination handler.
        kill_deadline = time.monotonic()+3
        while True:
            discover(process.pid, known, tag_key, tag)
            current = alive(known)
            kill_sent.update(signal_owned(current,signal.SIGKILL))
            process.poll()
            reap(known,process.pid)
            if not alive(known) or time.monotonic() >= kill_deadline:
                break
            time.sleep(.05)
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            pass
        reap(known,process.pid)
        discover(process.pid,known,tag_key,tag)
        survivors = [item['pid'] for item in alive(known)]
        return dict(complete=not survivors and process.poll() is not None,
                    platform=sys.platform, method='same-uid exact tag and verified descendants',
                    tag_key=tag_key, targeted_pids=sorted(known),
                    term_signals=len(term_sent), kill_signals=len(kill_sent),
                    surviving_pids=survivors)
