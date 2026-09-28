#!/usr/bin/env python3
"""Draw figures/layout.svg from bench/layout_jcc.csv.

Cycles of one sort of 1,024 keys, in builds that differ only in the
padding in front of the sorts, with and without
-mbranches-within-32B-boundaries.

Usage: scripts/plot_layout.py [layout_jcc.csv]
"""

import csv
import os
import sys

from plot import NAMES, ROOT, SHELL, SLOTS, end_labels, esc, legend, svg

SORTS = ['min', 'bubble', 'merge', 'heap', 'shell']
CMAP = {'min': SLOTS[0], 'bubble': SLOTS[1], 'merge': SLOTS[3], 'heap': SLOTS[4], 'shell': SHELL}
N = 1024


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'bench', 'layout_jcc.csv')
    rows = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            if int(r['n']) == N and r['sort'] in SORTS:
                rows[(r['build'], r['sort'], int(r['pad']))] = (float(r['cycles']), float(r['cycles_ci']))
    pads = sorted({p for _, _, p in rows})
    best = {s: min(c for (b, t, p), (c, _) in rows.items() if t == s) for s in SORTS}
    width, height = 900, 440
    body = ['<text class="title" x="24" y="30">Where the code is</text>',
            '<text class="sub" x="24" y="49">Cycles of one sort of 1,024 keys, relative to the fewest for '
            'that sort, in builds that differ only in the bytes of padding in front of the sorts.</text>']
    ly = legend(body, [(NAMES[s], '--' + s, False) for s in SORTS], 24, 76, width - 48)
    ylo, yhi = 0.9, 1.6
    ticks = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6]
    pw, gap = 300, 60
    for i, (build, name) in enumerate((('plain', 'As compiled'),
                                       ('jcc', 'With -mbranches-within-32B-boundaries'))):
        x0, y0, h = 96 + i * (pw + gap), ly + 40, height - ly - 40 - 60

        def X(p):
            return x0 + pw * (p - pads[0]) / (pads[-1] - pads[0])

        def Y(v):
            return y0 + h * (1 - (v - ylo) / (yhi - ylo))
        body.append('<text class="label" x="%.1f" y="%.1f" font-weight="600">%s</text>' % (x0, y0 - 10, esc(name)))
        body.append('<rect class="panel" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>' % (x0, y0, pw, h))
        for v in ticks:
            body.append('<line class="grid" x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f"/>' % (x0, x0 + pw, Y(v), Y(v)))
            body.append('<text class="tick" x="%.1f" y="%.1f" text-anchor="end">%.1f×</text>' % (x0 - 8, Y(v) + 4, v))
        for p in pads:
            body.append('<text class="tick" x="%.1f" y="%.1f" text-anchor="middle">%d</text>' % (X(p), y0 + h + 16, p))
        body.append('<line class="axis" x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f"/>' % (x0, x0 + pw, y0 + h, y0 + h))
        body.append('<text class="axlabel" x="%.1f" y="%.1f" text-anchor="middle">Bytes of padding</text>' % (
            x0 + pw / 2, y0 + h + 34))
        if i == 0:
            body.append('<text class="axlabel" transform="translate(%.1f,%.1f) rotate(-90)" '
                        'text-anchor="middle">Cycles / fewest</text>' % (x0 - 52, y0 + h / 2))
        labels = []
        for s in SORTS:
            pts = [(X(p), Y(rows[(build, s, p)][0] / best[s])) for p in pads]
            body.append('<path class="line" d="%s" style="stroke: var(--%s)"/>' % (
                ' '.join(('M' if k == 0 else 'L') + '%.1f,%.1f' % xy for k, xy in enumerate(pts)), s))
            for xx, yy in pts:
                body.append('<circle class="dot" cx="%.1f" cy="%.1f" r="4" style="fill: var(--%s)"/>' % (xx, yy, s))
            if i == 1:
                labels.append((NAMES[s], pts[-1][1], pts[-1][0]))
        if labels:
            end_labels(body, labels, x0 + pw + 14, y0 + 6, y0 + h)
    with open(os.path.join(ROOT, 'figures', 'layout.svg'), 'w') as f:
        f.write(svg(width, height, CMAP, body, 'Where the code is',
                    'Cycles of one sort of 1,024 keys relative to the fewest, against the bytes of padding '
                    'in front of the sorts, for five sorts, as compiled and with '
                    '-mbranches-within-32B-boundaries.'))


if __name__ == '__main__':
    main()
