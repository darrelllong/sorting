#!/usr/bin/env python3
"""Count the work of the caches and the branch predictor for every sort.

Each (sort, size) is one Pilot session, as in scripts/bench_pilot.py, and
pilot_sort counts hardware events over the timed batch as well (see
PILOT_SORT_EVENTS in pilot_sort.c). Pilot reports the mean of each count
for one sort, and its 95% confidence interval. The sizes are powers of two
from 1,024 to 4,194,304, and to 65,536 for the O(n^2) sorts.

The raw events are those of Intel Skylake and its successors, such as the
i5-8259U of dmz: l1d.replacement (lines brought into the L1 data cache),
l2_rqsts.miss, and longest_lat_cache.miss (misses of the L3 cache). The six
events fit the counters only if the NMI watchdog is off.

Usage: scripts/bench_cache.py [cache.csv]
"""

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bench_pilot import FIELDS, NLOGN, OTHERS, ROOT, run_session  # noqa: E402

EVENTS = [('cycles', 'cycles'), ('instructions', 'instructions'),
          ('branch_misses', 'branch-misses'), ('l1d_replacements', 'r151'),
          ('l2_misses', 'r3f24'), ('l3_misses', 'r412e')]
QUADRATIC = [s for s in OTHERS if s != 'shell']


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'bench', 'cache.csv')
    fields = FIELDS + [f for name, _ in EVENTS for f in (name, name + '_ci')]
    done = set()
    if os.path.exists(path):
        with open(path) as f:
            done = {(r['sort'], int(r['n'])) for r in csv.DictReader(f)}
    new_file = not os.path.exists(path)
    with open(path, 'a', newline='') as out:
        writer = csv.DictWriter(out, fields)
        if new_file:
            writer.writeheader()
        for k in range(10, 23):
            n = 2 ** k
            for sort in NLOGN + ['shell'] + (QUADRATIC if n <= 65536 else []):
                if (sort, n) in done:
                    continue
                r = run_session(sort, n, EVENTS)
                writer.writerow(r)
                out.flush()
                print('%-10s n=%-8d %6d rounds  %14.1f ns  %s' % (
                    sort, n, r['rounds'], r['time_ns'], r['status']), flush=True)


if __name__ == '__main__':
    main()
