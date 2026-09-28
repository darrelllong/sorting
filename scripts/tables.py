#!/usr/bin/env python3
"""Write the tables of README.md from bench/results.csv, in Markdown.

Usage: scripts/tables.py [results.csv]

The tables go between the lines <!-- tables --> and <!-- /tables --> of
README.md, which is rewritten.
"""

import csv
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMES = {
    'min': 'Min sort', 'bubble': 'Bubble sort', 'shaker': 'Shaker sort',
    'insertion': 'Insertion sort', 'binsert': 'Binary insertion', 'shell': 'Shell sort',
    'quick': 'Quicksort', 'quicki': 'Quicksort (iterative)', 'bfs': 'BFS (queue) sort',
    'merge': 'Merge sort', 'heap': 'Heap sort',
}
NLOGN = ['quick', 'quicki', 'bfs', 'merge', 'heap']
OTHERS = ['min', 'bubble', 'shaker', 'insertion', 'binsert', 'shell']


def fmt_time(v):
    for d, unit in ((1e9, 's'), (1e6, 'ms'), (1e3, 'µs')):
        if v >= d:
            return '%.3g %s' % (v / d, unit)
    return '%.3g ns' % v


def fmt_n(n):
    return '{:,}'.format(n)


def tex_n(n):
    """n = 65,536 in LaTeX, with the commas as {,} so that they do not space"""
    return '$n = %s$' % fmt_n(n).replace(',', '{,}')


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'bench', 'results.csv')
    rows = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            rows.setdefault(r['sort'], {})[int(r['n'])] = r
    sizes = sorted({n for s in NLOGN for n in rows.get(s, {})})
    out = []

    out.append('**Where each sort stopped.** It was slower than the slowest $O(n \\log n)$ sort at '
               'this $n$, and the sweep went no further with it. It was timed again at the larger sizes of the '
               'next table, for that table only.\n')
    out.append('| Sort | Stopped at $n$ | Its time | Slowest $O(n \\log n)$ sort at $n$ | Its time |')
    out.append('|---|---:|---:|---|---:|')
    for s in OTHERS:
        stop = [n for n, r in rows.get(s, {}).items() if r['status'].endswith('stopped')]
        if not stop:
            last = max(rows.get(s, {}) or [0])
            out.append('| %s | did not stop up to %s | | | |' % (NAMES[s], fmt_n(last)))
            continue
        n = stop[0]
        ref = max((rows[q][n] for q in NLOGN), key=lambda r: float(r['time_ns']))
        out.append('| %s | %s | %s | %s | %s |' % (
            NAMES[s], fmt_n(n), fmt_time(float(rows[s][n]['time_ns'])), NAMES[ref['sort']],
            fmt_time(float(ref['time_ns']))))
    out.append('')

    picks = [n for n in sizes if n in (16, 128, 1024, 8192, 65536, 524288) or n == sizes[-1]]
    out.append('**Mean time of one sort**, with the half-width of its 95% confidence interval. '
               'A time in italics is past the size at which the sort stopped: it was measured '
               'for this table, after the sweep. A blank is a size at which the sort was not run.\n')
    out.append('| Sort | ' + ' | '.join(tex_n(n) for n in picks) + ' |')
    out.append('|---|' + '---:|' * len(picks))
    for s in NLOGN + OTHERS:
        cells = []
        for n in picks:
            r = rows.get(s, {}).get(n)
            if r is None:
                cells.append('')
            else:
                t, ci = float(r['time_ns']), float(r['time_ci_ns'])
                h = 50 * ci / t
                cell = '%s $\\pm$ %s%%' % (fmt_time(t), '%.1f' % h if h >= 0.05 else '%.2f' % h)
                cells.append('*%s*' % cell if r['status'].endswith('extended') else cell)
        out.append('| %s | %s |' % (NAMES[s], ' | '.join(cells)))
    out.append('')

    n = sizes[-1]
    out.append('**At %s**, the largest size: time and counts divided by $n \\log_2 n$.\n' % tex_n(n))
    out.append('| Sort | Time / $(n \\log_2 n)$ | Comparisons / $(n \\log_2 n)$ | Moves / $(n \\log_2 n)$ | Rounds |')
    out.append('|---|---:|---:|---:|---:|')
    for s in sorted(NLOGN + ['shell'], key=lambda s: float(rows.get(s, {}).get(n, {'time_ns': 'inf'})['time_ns'])):
        r = rows.get(s, {}).get(n)
        if r is None:
            continue
        d = n * math.log2(n)
        out.append('| %s | %.2f ns | %.3f | %.3f | %s |' % (
            NAMES[s], float(r['time_ns']) / d, float(r['compares']) / d, float(r['moves']) / d, r['rounds']))
    out.append('')

    limited = [(s, n) for s in rows for n, r in rows[s].items() if not r['status'].startswith('converged')]
    total = sum(float(r['session_s']) for s in rows for r in rows[s].values())
    sessions = sum(len(rows[s]) for s in rows)
    rounds = sum(int(r['rounds']) for s in rows for r in rows[s].values())
    out.append('%d Pilot sessions, %s rounds, %.1f hours. ' % (sessions, fmt_n(rounds), total / 3600) +
               ('Every session converged.' if not limited else
                'These did not converge: ' + ', '.join('%s at %s' % (NAMES[s], tex_n(n)) for s, n in limited) + '.'))

    readme = os.path.join(ROOT, 'README.md')
    text = open(readme).read()
    a, b = text.index('<!-- tables -->'), text.index('<!-- /tables -->')
    text = text[:a] + '<!-- tables -->\n\n' + '\n'.join(out) + '\n\n' + text[b:]
    open(readme, 'w').write(text)


if __name__ == '__main__':
    main()
