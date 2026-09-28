#!/usr/bin/env python3
"""Time the same sorts in builds that differ only in where the code is.

Every build links the same object files, with PAD bytes of padding put in
front of the sorts, for PAD = 0, 16, ..., 112, so that each sort is moved
by that much and nothing else changes. Each (build, sort, size) is one
Pilot session that counts the same events as scripts/bench_cache.py, and
the results are appended to bench/layout.csv, with the address of each
sort in the build.

With LAYOUT_JCC=1, the sorts are also built with
-mbranches-within-32B-boundaries, which pads the code so that no jump
crosses or ends at a 32-byte boundary, and the events are those of the
front end: uops from the decoded uop cache (idq.dsb_uops) and from the
legacy decoders (idq.mite_uops). The results go to bench/layout_jcc.csv.

Usage: scripts/bench_layout.py [layout.csv]
"""

import csv
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bench_pilot import FIELDS, ROOT, run_session  # noqa: E402
from bench_cache import EVENTS  # noqa: E402

PADS = range(0, 128, 16)
SORTS = ['bubble', 'min', 'insertion', 'shell', 'quick', 'bfs', 'merge', 'heap']
FUNCTIONS = {'bubble': 'bubbleSort', 'min': 'minSort', 'insertion': 'insertionSort',
             'shell': 'shellSort', 'quick': 'qSort', 'bfs': 'BFSSort', 'merge': 'mergeSort',
             'heap': 'heapSort'}
SIZES = [1024, 8192]
CC = os.environ.get('CC', 'clang')
JCC = os.environ.get('LAYOUT_JCC') == '1'
FRONTEND = [('cycles', 'cycles'), ('instructions', 'instructions'),
            ('branch_misses', 'branch-misses'), ('dsb_uops', 'r879'), ('mite_uops', 'r479')]
CFLAGS = ['-Wall', '-Werror', '-Wextra', '-pedantic', '-O3'] + (['-DLAME'] if sys.platform == 'linux' else [])


def objects(flags, tag):
    """The sorts, compiled with flags into bench/layout/tag"""
    objs = subprocess.run(['make', '-C', ROOT, '-s', '--eval=print-sorts: ; @echo $(SORTS)',
                           'print-sorts'], check=True, capture_output=True, text=True).stdout.split()
    d = os.path.join(ROOT, 'bench', 'layout', tag)
    os.makedirs(d, exist_ok=True)
    out = []
    for o in objs:
        out.append(os.path.join(d, o))
        subprocess.run([CC] + CFLAGS + flags + ['-c', '-o', out[-1], os.path.join(ROOT, o[:-2] + '.c')],
                       check=True)
    return out


def build(pad, flags=(), tag='plain'):
    """pilot_sort with pad bytes in front of the sorts, and the address of each sort"""
    out = os.path.join(ROOT, 'bench', 'layout', tag, 'pilot_sort_%d' % pad)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    pad_o = out + '_pad.o'
    subprocess.run([CC, '-c', '-o', pad_o, '-x', 'c', '-'], check=True, text=True,
                   input='__asm__(".text\\n.globl pilot_pad\\npilot_pad:\\n.skip %d\\n");\n' % pad)
    subprocess.run([CC, '-o', out, os.path.join(ROOT, 'pilot_sort.o'), os.path.join(ROOT, 'pratt.o'),
                    pad_o] + objects(list(flags), tag), check=True)
    syms = {}
    for line in subprocess.run(['nm', out], check=True, capture_output=True, text=True).stdout.splitlines():
        parts = line.split()
        if len(parts) == 3:
            syms[parts[2]] = int(parts[0], 16)
    return out, syms


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        ROOT, 'bench', 'layout_jcc.csv' if JCC else 'layout.csv')
    subprocess.run(['make', '-C', ROOT, 'pilot_sort'], check=True, stdout=subprocess.DEVNULL)
    events = FRONTEND if JCC else EVENTS
    builds = [([], 'plain')] + ([(['-mbranches-within-32B-boundaries'], 'jcc')] if JCC else [])
    fields = ['build', 'pad', 'address'] + FIELDS + [f for name, _ in events for f in (name, name + '_ci')]
    done = set()
    if os.path.exists(path):
        with open(path) as f:
            done = {(r['build'], int(r['pad']), r['sort'], int(r['n'])) for r in csv.DictReader(f)}
    new_file = not os.path.exists(path)
    with open(path, 'a', newline='') as out:
        writer = csv.DictWriter(out, fields)
        if new_file:
            writer.writeheader()
        for flags, tag in builds:
            for pad in PADS:
                program, syms = build(pad, flags, tag)
                for n in SIZES:
                    for sort in SORTS:
                        if (tag, pad, sort, n) in done:
                            continue
                        r = run_session(sort, n, events, program)
                        r['build'], r['pad'], r['address'] = tag, pad, '0x%x' % syms[FUNCTIONS[sort]]
                        writer.writerow(r)
                        out.flush()
                        print('%-5s pad %3d %-10s n=%-6d %s %6d rounds %12.1f cycles  %s' % (
                            tag, pad, sort, n, r['address'], r['rounds'], r['cycles'], r['status']),
                            flush=True)


if __name__ == '__main__':
    main()
