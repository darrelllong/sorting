#!/usr/bin/env python3
"""Draw the figures of README.md from bench/results.csv.

Usage: scripts/plot.py [results.csv] [figures directory]

The figures are SVG, written without any library, and follow the light or
the dark scheme of the page that shows them.
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
QUADRATIC = ['min', 'bubble', 'shaker', 'insertion', 'binsert']
NLOGN = ['quick', 'quicki', 'bfs', 'merge', 'heap']

# Slots of the validated categorical palette, in order: light, dark. Shell
# sort, which is in both figures, keeps violet in both.
SLOTS = [('#2a78d6', '#3987e5'), ('#eb6834', '#d95926'), ('#1baf7a', '#199e70'),
         ('#eda100', '#c98500'), ('#e87ba4', '#d55181')]
SHELL = ('#4a3aa7', '#9085e9')


def colors(group):
    c = {s: SLOTS[i] for i, s in enumerate(group)}
    c['shell'] = SHELL
    return c


STYLE = '''<style>
  .viz { --surface: #fcfcfb; --ink: #0b0b0b; --ink2: #52514e; --muted: #898781;
         --grid: #e1e0d9; --axis: #c3c2b7; --ref: #898781; %(light)s }
  @media (prefers-color-scheme: dark) {
    .viz { --surface: #1a1a19; --ink: #ffffff; --ink2: #c3c2b7; --muted: #898781;
           --grid: #2c2c2a; --axis: #383835; --ref: #898781; %(dark)s }
  }
  .viz text { font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }
  .title { font-size: 15px; font-weight: 600; fill: var(--ink); }
  .sub { font-size: 12px; fill: var(--ink2); }
  .tick { font-size: 11px; fill: var(--muted); font-variant-numeric: tabular-nums; }
  .axlabel { font-size: 12px; fill: var(--ink2); }
  .label { font-size: 12px; fill: var(--ink); }
  .legend { font-size: 12px; fill: var(--ink2); }
  .grid { stroke: var(--grid); stroke-width: 1; }
  .axis { stroke: var(--axis); stroke-width: 1; }
  .line { fill: none; stroke-width: 2; stroke-linejoin: round; stroke-linecap: round; }
  .ci { stroke-width: 1.5; stroke-linecap: round; }
  .dot { stroke: var(--surface); stroke-width: 2; }
  .leader { stroke: var(--muted); stroke-width: 1; }
  .panel { fill: var(--surface); }
</style>'''


def load(path):
    rows = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            if r['status'].startswith('error') or r['status'].endswith('extended'):
                continue
            rows.setdefault(r['sort'], []).append({
                'n': int(r['n']), 't': float(r['time_ns']), 'tci': float(r['time_ci_ns']),
                'c': float(r['compares']), 'm': float(r['moves']),
                'stopped': r['status'].endswith('stopped')})
    for s in rows:
        rows[s].sort(key=lambda r: r['n'])
    return rows


def fmt_n(v):
    for d, suffix in ((1e6, 'M'), (1e3, 'K')):
        if v >= d:
            x = v / d
            return ('%g' % x) + suffix
    return '%g' % v


def fmt_time(v):
    for d, unit in ((1e9, 's'), (1e6, 'ms'), (1e3, 'µs')):
        if v >= d:
            return '%g %s' % (v / d, unit)
    return '%g ns' % v


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


class Panel:
    """One plotting area, with a log x scale and a log or linear y scale"""

    def __init__(self, x0, y0, w, h, xlo, xhi, ylo, yhi, ylog):
        self.x0, self.y0, self.w, self.h = x0, y0, w, h
        self.xlo, self.xhi, self.ylo, self.yhi, self.ylog = xlo, xhi, ylo, yhi, ylog

    def x(self, v):
        return self.x0 + self.w * (math.log10(v) - math.log10(self.xlo)) / (
            math.log10(self.xhi) - math.log10(self.xlo))

    def y(self, v):
        if self.ylog:
            f = (math.log10(v) - math.log10(self.ylo)) / (math.log10(self.yhi) - math.log10(self.ylo))
        else:
            f = (v - self.ylo) / (self.yhi - self.ylo)
        return self.y0 + self.h * (1 - f)

    def axes(self, out, yticks, yfmt, xlabel, ylabel):
        out.append('<rect class="panel" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>' % (
            self.x0, self.y0, self.w, self.h))
        for v in yticks:
            yy = self.y(v)
            out.append('<line class="grid" x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f"/>' % (
                self.x0, self.x0 + self.w, yy, yy))
            out.append('<text class="tick" x="%.1f" y="%.1f" text-anchor="end">%s</text>' % (
                self.x0 - 8, yy + 4, esc(yfmt(v))))
        v = 1
        while v <= self.xhi:
            if v >= self.xlo:
                xx = self.x(v)
                out.append('<line class="grid" x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f"/>' % (
                    xx, xx, self.y0, self.y0 + self.h))
                out.append('<text class="tick" x="%.1f" y="%.1f" text-anchor="middle">%s</text>' % (
                    xx, self.y0 + self.h + 16, fmt_n(v)))
            v *= 10
        out.append('<line class="axis" x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f"/>' % (
            self.x0, self.x0 + self.w, self.y0 + self.h, self.y0 + self.h))
        out.append('<text class="axlabel" x="%.1f" y="%.1f" text-anchor="middle">%s</text>' % (
            self.x0 + self.w / 2, self.y0 + self.h + 34, esc(xlabel)))
        out.append('<text class="axlabel" transform="translate(%.1f,%.1f) rotate(-90)" '
                   'text-anchor="middle">%s</text>' % (self.x0 - 58, self.y0 + self.h / 2, esc(ylabel)))

    def line(self, out, pts, var):
        pts = [(v, w) for v, w in pts if self.ylo <= w <= self.yhi]
        if len(pts) < 2:
            return
        d = ' '.join(('M' if i == 0 else 'L') + '%.1f,%.1f' % (self.x(v), self.y(w))
                     for i, (v, w) in enumerate(pts))
        out.append('<path class="line" d="%s" style="stroke: var(%s)"/>' % (d, var))

    def whiskers(self, out, pts, var):
        for v, lo, hi in pts:
            lo, hi = max(lo, self.ylo), min(hi, self.yhi)
            if self.y(lo) - self.y(hi) < 1.5:
                continue
            xx = self.x(v)
            out.append('<line class="ci" x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" style="stroke: var(%s)"/>'
                       % (xx, xx, self.y(lo), self.y(hi), var))

    def dot(self, out, v, w, var):
        out.append('<circle class="dot" cx="%.1f" cy="%.1f" r="4.5" style="fill: var(%s)"/>' % (
            self.x(v), self.y(w), var))


def end_labels(out, items, x, top, bottom, gap=14):
    """Labels at the right of the lines, pushed apart, with leader lines"""
    items = sorted(items, key=lambda i: i[1])
    ys = [max(top, min(bottom, y)) for _, y, _ in items]
    for _ in range(50):
        for i in range(1, len(ys)):
            if ys[i] - ys[i - 1] < gap:
                ys[i] = ys[i - 1] + gap
        for i in range(len(ys) - 2, -1, -1):
            if ys[i + 1] - ys[i] < gap:
                ys[i] = ys[i + 1] - gap
        ys = [max(top, min(bottom, y)) for y in ys]
    for (text, y, xend), ly in zip(items, ys):
        out.append('<line class="leader" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (
            xend + 6, y, x - 4, ly))
        out.append('<text class="label" x="%.1f" y="%.1f">%s</text>' % (x, ly + 4, esc(text)))


def legend(out, entries, x, y, width):
    """One row of swatches and names, above the plot, wrapped to the width"""
    cx, cy = x, y
    for name, var, dashed in entries:
        w = 26 + 7 * len(name)
        if cx + w > x + width:
            cx, cy = x, cy + 18
        dash = ' stroke-dasharray="5 3"' if dashed else ''
        out.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" style="stroke: var(%s)" '
                   'stroke-width="2" stroke-linecap="round"%s/>' % (cx, cx + 14, cy - 4, cy - 4, var, dash))
        out.append('<text class="legend" x="%.1f" y="%.1f">%s</text>' % (cx + 20, cy, esc(name)))
        cx += w + 12
    return cy


def svg(width, height, cmap, body, title, desc):
    light = ' '.join('--%s: %s;' % (s, c[0]) for s, c in cmap.items())
    dark = ' '.join('--%s: %s;' % (s, c[1]) for s, c in cmap.items())
    return ('<svg xmlns="http://www.w3.org/2000/svg" class="viz" width="%d" height="%d" '
            'viewBox="0 0 %d %d" role="img" aria-labelledby="t d">\n<title id="t">%s</title>\n'
            '<desc id="d">%s</desc>\n%s\n<rect width="100%%" height="100%%" fill="var(--surface)"/>\n%s\n</svg>\n'
            % (width, height, width, height, esc(title), esc(desc),
               STYLE % {'light': light, 'dark': dark}, '\n'.join(body)))


def decades(lo, hi):
    out, v = [], 10 ** math.floor(math.log10(lo))
    while v <= hi:
        if v >= lo:
            out.append(v)
        v *= 10
    return out


def nice_linear(lo, hi, count=5):
    span = hi - lo
    step = 10 ** math.floor(math.log10(span / count))
    for m in (1, 2, 2.5, 5, 10):
        if span / (step * m) <= count:
            step *= m
            break
    first = math.ceil(lo / step) * step
    return [first + i * step for i in range(int((hi - first) / step) + 1)]


def figure_quadratic(rows, path):
    """Time of the O(n^2) sorts and Shell sort, and of the slowest O(n log n)"""
    group = QUADRATIC + ['shell']
    cmap = colors(QUADRATIC)
    width, height = 900, 500
    body = ['<text class="title" x="24" y="30">When the quadratic sorts stop</text>',
            '<text class="sub" x="24" y="49">Mean time of one sort of n random keys, with its 95% '
            'confidence interval. A sort stops when it is slower than the slowest O(n log n) sort.</text>']
    def stop(s):
        rs = rows.get(s, [])
        return rs[-1]['n'] if rs and rs[-1]['stopped'] else None
    entries = [(NAMES[s] + (', stopped at n = {:,}'.format(stop(s)) if stop(s) else ''), '--' + s, False)
               for s in group] + [('Slowest O(n log n) sort', '--ref', True)]
    ly = legend(body, entries, 24, 76, width - 48)
    sizes = sorted({r['n'] for s in NLOGN for r in rows.get(s, [])})
    slowest = []
    for n in sizes:
        ts = [r for s in NLOGN for r in rows.get(s, []) if r['n'] == n]
        if len(ts) == len(NLOGN):
            slowest.append((n, max(r['t'] for r in ts)))
    # up to a little beyond where the last of them stopped
    stops = [stop(s) for s in group if stop(s)]
    xmax = max(n for n, _ in slowest)
    if stops:
        xmax = min(xmax, 4 * max(stops))
    slowest = [(n, t) for n, t in slowest if n <= xmax]
    ymax = max([t for _, t in slowest] + [r['t'] for s in group for r in rows.get(s, []) if r['n'] <= xmax])
    ymin = min(r['t'] for s in group + NLOGN for r in rows.get(s, []))
    p = Panel(96, ly + 22, width - 96 - 190, height - ly - 22 - 60, 2, xmax,
              10 ** math.floor(math.log10(ymin)), 10 ** math.ceil(math.log10(ymax)), True)
    p.axes(body, decades(p.ylo, p.yhi), fmt_time, 'Number of keys, n', 'Time of one sort')
    pts = [(p.x(n), p.y(t)) for n, t in slowest]
    body.append('<path class="line" d="%s" style="stroke: var(--ref)" stroke-dasharray="5 3"/>' %
                ' '.join(('M' if i == 0 else 'L') + '%.1f,%.1f' % xy for i, xy in enumerate(pts)))
    labels = []
    for s in group:
        rs = [r for r in rows.get(s, []) if r['n'] <= xmax]
        if not rs:
            continue
        p.line(body, [(r['n'], r['t']) for r in rs], '--' + s)
        last = rs[-1]
        if last['stopped']:
            # where it stopped is in the legend, and the dot marks it
            p.dot(body, last['n'], last['t'], '--' + s)
        else:
            labels.append((NAMES[s], p.y(last['t']), p.x(last['n'])))
    labels.append(('Slowest O(n log n)', pts[-1][1], pts[-1][0]))
    end_labels(body, labels, p.x0 + p.w + 14, p.y0 + 6, p.y0 + p.h)
    with open(path, 'w') as f:
        f.write(svg(width, height, dict(cmap, ref=('#898781', '#898781')), body,
                    'When the quadratic sorts stop',
                    'Log-log plot of the time of one sort against n for five quadratic sorts, Shell sort, '
                    'and the slowest O(n log n) sort at each n.'))


def figure_nlogn(rows, path):
    """Time per n log2 n of the O(n log n) sorts"""
    group = NLOGN
    cmap = colors(NLOGN)
    width, height = 900, 470
    body = ['<text class="title" x="24" y="30">The O(n log n) sorts, per n log₂ n</text>',
            '<text class="sub" x="24" y="49">Mean time of one sort divided by n log₂ n, with its 95% '
            'confidence interval. A line that is flat is n log n.</text>']
    ly = legend(body, [(NAMES[s], '--' + s, False) for s in group], 24, 76, width - 48)
    series = {s: [(r['n'], r['t'] / (r['n'] * math.log2(r['n'])),
                   (r['t'] - r['tci'] / 2) / (r['n'] * math.log2(r['n'])),
                   (r['t'] + r['tci'] / 2) / (r['n'] * math.log2(r['n'])))
                  for r in rows.get(s, []) if r['n'] >= 16] for s in group}
    xmax = max(v[0] for s in group for v in series[s])
    ymax = max(v[1] for s in group for v in series[s])
    p = Panel(96, ly + 22, width - 96 - 190, height - ly - 22 - 60, 16, xmax, 0, ymax * 1.08, False)
    p.axes(body, nice_linear(0, p.yhi), lambda v: '%g ns' % v, 'Number of keys, n',
           'Time / (n log₂ n)')
    labels = []
    for s in group:
        pts = series[s]
        if not pts:
            continue
        p.whiskers(body, [(v, lo, hi) for v, _, lo, hi in pts], '--' + s)
        p.line(body, [(v, w) for v, w, _, _ in pts], '--' + s)
        labels.append((NAMES[s], p.y(pts[-1][1]), p.x(pts[-1][0])))
    end_labels(body, labels, p.x0 + p.w + 14, p.y0 + 6, p.y0 + p.h)
    with open(path, 'w') as f:
        f.write(svg(width, height, cmap, body, 'The O(n log n) sorts, per n log2 n',
                    'Time of one sort divided by n log2 n against n, for the five O(n log n) sorts.'))


def figure_counts(rows, path, group, cmap, norm, norm_label, title, sub, nmin):
    """Two panels, compares and moves, divided by norm(n)"""
    width, height = 900, 420
    body = ['<text class="title" x="24" y="30">%s</text>' % esc(title),
            '<text class="sub" x="24" y="49">%s</text>' % esc(sub)]
    ly = legend(body, [(NAMES[s], '--' + s, False) for s in group], 24, 76, width - 48)
    pw = (width - 96 - 40 - 70) / 2
    for i, (key, name) in enumerate((('c', 'Comparisons'), ('m', 'Moves'))):
        series = {s: [(r['n'], r[key] / norm(r['n'])) for r in rows.get(s, []) if r['n'] >= nmin]
                  for s in group}
        xmax = max(v for s in group for v, _ in series[s])
        ymax = max(w for s in group for _, w in series[s])
        p = Panel(96 + i * (pw + 70), ly + 34, pw, height - ly - 34 - 60, nmin, xmax, 0, ymax * 1.08, False)
        body.append('<text class="label" x="%.1f" y="%.1f" font-weight="600">%s</text>' % (
            p.x0, p.y0 - 10, name))
        p.axes(body, nice_linear(0, p.yhi, 4), lambda v: '%g' % v, 'Number of keys, n',
               '%s / %s' % (name, norm_label) if i == 0 else '')
        for s in group:
            if series[s]:
                p.line(body, series[s], '--' + s)
    with open(path, 'w') as f:
        f.write(svg(width, height, cmap, body, title, sub))


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'bench', 'results.csv')
    fig = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'figures')
    os.makedirs(fig, exist_ok=True)
    rows = load(path)
    figure_quadratic(rows, os.path.join(fig, 'time-quadratic.svg'))
    figure_nlogn(rows, os.path.join(fig, 'time-nlogn.svg'))
    figure_counts(rows, os.path.join(fig, 'counts-nlogn.svg'), NLOGN, colors(NLOGN),
                  lambda n: n * math.log2(n), 'n log₂ n',
                  'Comparisons and moves of the O(n log n) sorts',
                  'Mean counts of one sort divided by n log₂ n.', 16)
    figure_counts(rows, os.path.join(fig, 'counts-quadratic.svg'), QUADRATIC, colors(QUADRATIC),
                  lambda n: n * n, 'n²', 'Comparisons and moves of the quadratic sorts',
                  'Mean counts of one sort divided by n², up to where each sort stopped.', 4)


if __name__ == '__main__':
    main()
