#!/usr/bin/env python3
"""Time Shell sort with its table of gaps against the whole sequence of Pratt.

Each (sort, size) is one Pilot session, as in scripts/bench_pilot.py, and
the results are appended to bench/shell_gaps.csv.

Usage: scripts/bench_shell_gaps.py [shell_gaps.csv]
"""

import csv
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bench_pilot import BENCH, FIELDS, ROOT, run_session  # noqa: E402

SIZES = [4096, 32768, 262144, 2097152, 8388608]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'bench', 'shell_gaps.csv')
    subprocess.run(['make', '-C', ROOT, 'pilot_sort'], check=True, stdout=subprocess.DEVNULL)
    if not os.access(BENCH, os.X_OK):
        sys.exit('bench of Pilot not found at %s; set PILOT_BENCH_CLI' % BENCH)
    done = set()
    if os.path.exists(path):
        with open(path) as f:
            done = {(r['sort'], int(r['n'])) for r in csv.DictReader(f)}
    new_file = not os.path.exists(path)
    with open(path, 'a', newline='') as out:
        writer = csv.DictWriter(out, FIELDS)
        if new_file:
            writer.writeheader()
        for n in SIZES:
            for sort in ('shell', 'pratt'):
                if (sort, n) in done:
                    continue
                r = run_session(sort, n)
                writer.writerow(r)
                out.flush()
                print('%-6s n=%-8d %6d rounds  %14.1f ns +- %.1f%%  %.4g compares  %s' % (
                    sort, n, r['rounds'], r['time_ns'], 50 * r['time_ci_ns'] / r['time_ns'],
                    r['compares'], r['status']), flush=True)


if __name__ == '__main__':
    main()
