"""Prove completed sequential CTest cases; never turn a failed test into a pass."""
import re


def require(value, message):
    if not value:
        raise RuntimeError(message)


def passed_prefix(text, names):
    rows = []
    for line in text.splitlines():
        if re.match(r'^\s*\d+/\d+ Test\s+#\d+:', line):
            match = re.fullmatch(r'\s*(\d+)/(\d+) Test\s+#\d+:\s+(\S+)\s+\.+\s+Passed\s+([0-9.]+) sec\s*', line)
            require(match is not None, 'Prior partial suite contains a non-passed result')
            require(int(match[1]) == len(rows)+1 and int(match[2]) == len(names), 'CTest order/count differs')
            rows.append(match[3])
    require(rows and len(rows) < len(names) and rows == names[:len(rows)], 'Exact nonempty incomplete passed prefix required')
    return rows


def completed_remainder(text, remaining):
    rows = []
    for line in text.splitlines():
        if re.match(r'^\s*\d+/\d+ Test\s+#\d+:', line):
            match = re.fullmatch(r'\s*(\d+)/(\d+) Test\s+#\d+:\s+(\S+)\s+\.+\s+Passed\s+([0-9.]+) sec\s*', line)
            require(match is not None, 'Remainder contains a non-passed result')
            require(int(match[1]) == len(rows)+1 and int(match[2]) == len(remaining), 'Remainder order/count differs')
            rows.append(match[3])
    require(rows == remaining and len(set(rows)) == len(rows), 'Every and only missing test must pass')
    require(re.search(r'100% tests passed, 0 tests failed out of '+str(len(remaining))+r'\b', text), 'Remainder terminal summary missing')
    return rows
