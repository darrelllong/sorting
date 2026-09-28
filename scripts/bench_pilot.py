#!/usr/bin/env python3
"""Time every sort with Pilot, over sizes from 2 to 2^23.

Each (sort, size) is one Pilot session: Pilot runs pilot_sort again and
again, each time on a fresh random input, until the 95% confidence interval
of the mean time is no wider than 10% of the mean (the "normal" preset).

The O(n log n) sorts are timed at every size. The others, the five O(n^2)
sorts and Shell sort, are timed until they are slower than the slowest of
the O(n log n) sorts at the same size, and then no more. Slower means that
the lower end of the sort's confidence interval is above the upper end of
the interval of the slowest O(n log n) sort.

After the sweep, the sorts that stopped are timed at the sizes of the
tables of README.md that are past where they stopped: the O(n^2) sorts up
to EXTEND_QUADRATIC, and Shell sort up to the largest size. These sessions
are marked "extended". They are in the tables and not in the figures.

Usage: scripts/bench_pilot.py [results.csv]

The results are appended to bench/results.csv, and sessions that are
already there are not run again, so the sweep can be stopped and started.

Environment:
    PILOT_BENCH_CLI   the bench program of Pilot
                      (default $HOME/pilot-bench/build/cli/bench)
    PILOT_PRESET      the preset of Pilot (default normal)
    PILOT_SESSION_LIMIT  seconds that a session may take (default 900)
    MAX_LOG2_N        the largest size is 2^MAX_LOG2_N (default 23)
    EXTEND_QUADRATIC  the largest size at which the O(n^2) sorts are timed
                      after they stop (default 65536)
"""

import csv
import os
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BENCH = os.environ.get('PILOT_BENCH_CLI', os.path.expanduser('~/pilot-bench/build/cli/bench'))
PRESET = os.environ.get('PILOT_PRESET', 'normal')
SESSION_LIMIT = int(os.environ.get('PILOT_SESSION_LIMIT', '900'))
MAX_LOG2_N = int(os.environ.get('MAX_LOG2_N', '23'))
EXTEND_QUADRATIC = int(os.environ.get('EXTEND_QUADRATIC', '65536'))

# The sizes of the tables of README.md, which scripts/tables.py shows
TABLE_SIZES = [16, 128, 1024, 8192, 65536, 524288, 2 ** MAX_LOG2_N]

NLOGN = ['quick', 'quicki', 'bfs', 'merge', 'heap']
OTHERS = ['min', 'bubble', 'shaker', 'insertion', 'binsert', 'shell']

FIELDS = ['sort', 'n', 'rounds', 'time_ns', 'time_ci_ns', 'compares', 'compares_ci',
          'moves', 'moves_ci', 'session_s', 'status']


def sizes():
    """2, 3, 4, 6, 8, 11, 16, ...: two sizes for every power of two"""
    out = []
    for k in range(2, 2 * MAX_LOG2_N + 1):
        n = int(round(2 ** (k / 2)))
        if n not in out:
            out.append(n)
    return out


def run_session(sort, n, events=(), program=None):
    """One Pilot session; events are (name, event) pairs for PILOT_SORT_EVENTS,
    and program is the pilot_sort to run, if not the one in ROOT"""
    work = tempfile.mkdtemp(prefix='pilot_sort_')
    pi = 'time,ns,0,0,1:compares,,1,0,0:moves,,2,0,0' + ''.join(
        ':%s,,%d,0,0' % (name, 3 + i) for i, (name, _) in enumerate(events))
    env = dict(os.environ, PILOT_SORT_EVENTS=','.join(e for _, e in events))
    try:
        start = time.time()
        rc = subprocess.run(
            [BENCH, 'run_program', '--preset', PRESET, '--session-limit', str(SESSION_LIMIT),
             '--pi', pi,
             '-o', os.path.join(work, 'out'), '-q', '--',
             program or os.path.join(ROOT, 'pilot_sort'), sort, str(n)],
            cwd=work, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
        elapsed = time.time() - start
        with open(os.path.join(work, 'out', 'pi_results.csv')) as f:
            rows = {int(r['piid']): r for r in csv.DictReader(f)}
    finally:
        shutil.rmtree(work, ignore_errors=True)
    status = {0: 'converged', 13: 'session limit'}.get(rc, 'error %d' % rc)
    t, c, m = rows[0], rows[1], rows[2]
    extra = {}
    for i, (name, _) in enumerate(events):
        extra[name] = float(rows[3 + i]['readings_mean'])
        extra[name + '_ci'] = float(rows[3 + i]['readings_subsession_ci'])
    return extra | {
        'sort': sort, 'n': n, 'rounds': int(t['readings_num']),
        'time_ns': float(t['readings_mean']), 'time_ci_ns': float(t['readings_subsession_ci']),
        'compares': float(c['readings_mean']), 'compares_ci': float(c['readings_subsession_ci']),
        'moves': float(m['readings_mean']), 'moves_ci': float(m['readings_subsession_ci']),
        'session_s': round(elapsed, 1), 'status': status,
    }


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'bench', 'results.csv')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(os.path.join(ROOT, 'pilot_sort')):
        subprocess.run(['make', '-C', ROOT, 'pilot_sort'], check=True)
    if not os.access(BENCH, os.X_OK):
        sys.exit('bench of Pilot not found at %s; set PILOT_BENCH_CLI' % BENCH)

    done = {}
    if os.path.exists(path):
        with open(path) as f:
            for r in csv.DictReader(f):
                done[(r['sort'], int(r['n']))] = r
    new_file = not os.path.exists(path)
    out = open(path, 'a', newline='')
    writer = csv.DictWriter(out, FIELDS)
    if new_file:
        writer.writeheader()
        out.flush()

    def measure(sort, n, status=None):
        if (sort, n) in done:
            r = done[(sort, n)]
            return {k: (float(v) if k not in ('sort', 'status') else v) for k, v in r.items()}
        r = run_session(sort, n)
        if status:
            r['status'] += ', ' + status
        writer.writerow(r)
        out.flush()
        print('%-10s n=%-8d %7d rounds  %14.1f ns  +- %.1f%%  %s' % (
            sort, n, r['rounds'], r['time_ns'], 50 * r['time_ci_ns'] / r['time_ns'], r['status']),
            flush=True)
        return r

    active = list(OTHERS)
    # sorts that were stopped in an earlier run
    for sort in OTHERS:
        stopped = [r for (s, _), r in done.items() if s == sort and r['status'].endswith('stopped')]
        if stopped:
            active.remove(sort)

    for n in sizes():
        ref = [measure(s, n) for s in NLOGN]
        slowest = max(ref, key=lambda r: r['time_ns'])
        upper = slowest['time_ns'] + slowest['time_ci_ns'] / 2
        for sort in list(active):
            r = measure(sort, n)
            lower = r['time_ns'] - r['time_ci_ns'] / 2
            if lower > upper:
                active.remove(sort)
                print('%s is slower than %s at n=%d, and is stopped' % (sort, slowest['sort'], n),
                      flush=True)
                # record it, so that a later run knows
                with open(path) as f:
                    rows = list(csv.DictReader(f))
                for row in rows:
                    if row['sort'] == sort and int(row['n']) == n:
                        row['status'] += ', stopped'
                out.close()
                with open(path, 'w', newline='') as f:
                    w = csv.DictWriter(f, FIELDS)
                    w.writeheader()
                    w.writerows(rows)
                out = open(path, 'a', newline='')
                writer = csv.DictWriter(out, FIELDS)
                done[(sort, n)] = dict(r, status=r['status'] + ', stopped')

    # Past where they stopped, at the sizes of the tables
    for sort in OTHERS:
        stops = [n for (s, n), r in done.items() if s == sort and r['status'].endswith('stopped')]
        if not stops:
            continue
        limit = 2 ** MAX_LOG2_N if sort == 'shell' else EXTEND_QUADRATIC
        for n in TABLE_SIZES:
            if stops[0] < n <= limit:
                measure(sort, n, 'extended')
    out.close()


if __name__ == '__main__':
    main()
