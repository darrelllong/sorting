# sorting

Eleven sorts from CSE 13S, with a driver that runs any of them and counts
their comparisons and moves, and a benchmark of all of them made with the
[Pilot](https://github.com/darrelllong/pilot-bench) benchmark framework.

| Sort | Flag | Comparisons, on average | Worst case | Notes |
|---|---|---|---|---|
| Min sort | `-m` | n²/2 | O(n²) | At most n swaps |
| Bubble sort | `-b` | about n²/2 | O(n²) | Stops after a pass with no swap |
| Shaker sort | `-S` | about n²/2 | O(n²) | Bubble sort in both directions |
| Insertion sort | `-i` | about n²/4 | O(n²) | |
| Binary insertion sort | `-B` | about n log₂ n | O(n²) | The search is binary; the moves are still about n²/4 |
| Shell sort | `-s` | | | Gaps that are products of 2 and 3; see below |
| Quicksort | `-q` | about 1.39 n log₂ n | O(n²) | Hoare's partition, the middle element as the pivot |
| Quicksort (iterative) | `-Q` | the same | O(n²) | The same, with an explicit stack |
| BFS (queue) sort | `-X` | the same | O(n²) | Quicksort that takes the subarrays breadth first, from a queue |
| Merge sort | `-M` | about n log₂ n | O(n log n) | Top down; copies both halves at every level |
| Heap sort | `-h` | about 2 n log₂ n | O(n log n) | After Sara Baase, *Computer Algorithms* |

The quicksorts are O(n²) in the worst case, but the benchmark gives them
random keys, on which they are O(n log n), so they are counted with the
O(n log n) sorts.

**Shell sort.** The gaps are numbers of the form 2ᵖ3ᵍ, from the sequence of
Pratt. The table in `shellsort.c` is an abbreviated sequence: it leaves out
32 of Pratt's numbers below 629,856, from 2,048 on (2,048, 4,096, 6,144,
8,192, …), and the loop uses the first 100 of its 102 entries. On random
keys the abbreviated sequence is the better one, once n is past a few
thousand. `pratt.c` is the same sort with all 128 numbers 2ᵖ3ᵍ up to
472,392, the largest gap of the table. Each row below is two Pilot sessions, one
for each sequence, on a Cortex-X925 core of an NVIDIA GB10
(`bench/vinge.txt`, `bench/shell_gaps.csv`). The half-width of every 95%
confidence interval is at most 0.14% of its mean.

| n | Table, time | Table, comparisons | Whole sequence, time | Whole sequence, comparisons |
|---:|---:|---:|---:|---:|
| 4,096 | 232 µs | 0.204 × 10⁶ | 229 µs | 0.206 × 10⁶ |
| 32,768 | 2.61 ms | 2.37 × 10⁶ | 2.71 ms | 2.55 × 10⁶ |
| 262,144 | 26.9 ms | 24.8 × 10⁶ | 29.9 ms | 29.1 × 10⁶ |
| 2,097,152 | 256 ms | 231 × 10⁶ | 291 ms | 286 × 10⁶ |
| 8,388,608 | 1.13 s | 981 × 10⁶ | 1.27 s | 1,205 × 10⁶ |

At n = 4,096 the whole sequence is 1.5% faster; at 8,388,608 the table is
11% faster and makes 19% fewer comparisons. It has fewer gaps, and so makes
fewer passes. Pratt's O(n log² n) bound on the worst case is proved for the
whole sequence and does not carry over to the abbreviated one.

## Building

```
make                 # the driver, sorting
make pilot_sort      # the program that the benchmark runs
./sorting -H         # its options
./sorting -A -n 20   # every sort, on 20 random keys
```

## The benchmark

Every sort was timed with Pilot on random keys from n = 2 to n = 2²³
(8,388,608), at two sizes for every power of two.

**One measurement.** A sort of a few keys is too fast to time, so
`pilot_sort` times a batch of sorts, each of other random 30-bit keys from a
fresh seed, doubling the batch until it takes at least 2 ms. It prints the
mean time of one sort in the batch, and the mean numbers of comparisons and
moves, which the sorts count as they are timed. After the timing it checks
that every array of the batch is in order; a sort that does not sort ends
the session.

In the sweep, `pilot_sort` also sorted one more array before the batch,
outside the timing, and took the comparisons and moves from it. When the
batch is one sort, as it is for the slow sorts at large n, that doubled the
cost of every reading. It was taken out for the sessions that were run after
the sweep for the tables (see below), whose counts are means over the batch.

Each sort in the batch has to be of other keys. A first version of
`pilot_sort` sorted copies of the same keys, and the branch predictor
learned their branches: at n = 181 quicksort and heap sort took a third of
the time that they take on keys they have not seen, and insertion sort 91%.
The effect was gone by n = 2,048, and it was not the same for every sort, so
it moved the sizes at which the sorts stopped. Those results were
discarded.

**One session.** Pilot runs `pilot_sort` again and again, and each run is
one reading of another random input, until the mean time is known to within
±5% at 95% confidence, from at least 50 readings that are nearly
independent (Pilot's `normal` preset). The comparisons and moves are
averaged over the same readings.

**When a sort stops.** The five O(n log n) sorts are timed at every size.
The others, the five O(n²) sorts and Shell sort, are timed at every size
until they are slower than the slowest of the O(n log n) sorts at the same
size, and at no larger size. Slower means that the lower end of the sort's
confidence interval is above the upper end of the interval of the slowest
O(n log n) sort, so that a difference within the noise does not stop it.

The figures show the sweep, and no more. For the tables, each sort that
stopped was timed again, after the sweep, at the sizes of the table of
times that are past where it stopped: the O(n²) sorts up to n = 65,536, where
bubble sort takes 5.55 s, and Shell sort up to n = 8,388,608. Those sessions
are marked `extended` in `bench/results.csv`, and are in italics in the
table.

**The machine.** A benchmark can be no steadier than the machine it runs on.
These results are from `dmz`:

```
machine: dmz, Intel(R) Core(TM) i5-8259U CPU @ 2.30GHz, 8 threads, 30 GB
system: Ubuntu 26.04.1 LTS, Linux 7.0.0-31-generic
compiler: Ubuntu clang version 21.1.8 (6ubuntu1), -O3
pilot: f01eec4 Replace the changepoint detection; document the revisions since 2016, preset normal
pinned: taskset -c 3; frequency governor powersave, turbo on
date: 2026-09-27 and 2026-09-28
```

The whole session ran on one core (`taskset -c 3`), with nothing else on the
machine. A first run on an Apple M4 was abandoned. The M4 has performance
and efficiency cores, and a sort that ran on an efficiency core took 2.7
times as long; readings from both kinds of core in one session made it one
that could not converge.

## Results

![Time of one sort against n, log-log, for the five O(n²) sorts and Shell sort, and the slowest O(n log n) sort at each n; each quadratic sort ends with a dot where it became slower than that](figures/time-quadratic.svg)

![Time of one sort divided by n log₂ n, against n, for the five O(n log n) sorts](figures/time-nlogn.svg)

![Comparisons and moves of one sort divided by n log₂ n, for the five O(n log n) sorts](figures/counts-nlogn.svg)

![Comparisons and moves of one sort divided by n², for the five O(n²) sorts](figures/counts-quadratic.svg)

The figures follow the light or dark setting of the page. Every number in
them is in `bench/results.csv`, and the tables below are made from it.

<!-- tables -->

**Where each sort stopped.** It was slower than the slowest O(n log n) sort at this n, and the sweep went no further with it. It was timed again at the larger sizes of the next table, for that table only.

| Sort | Stopped at n | Its time | Slowest O(n log n) sort at n | Its time |
|---|---:|---:|---|---:|
| Min sort | 91 | 4.95 µs | Merge sort | 4.67 µs |
| Bubble sort | 32 | 1.54 µs | Merge sort | 1.36 µs |
| Shaker sort | 32 | 1.48 µs | Merge sort | 1.36 µs |
| Insertion sort | 362 | 27.4 µs | Merge sort | 22 µs |
| Binary insertion | 362 | 23.9 µs | Merge sort | 22 µs |
| Shell sort | 1,024 | 71.6 µs | Merge sort | 68.2 µs |

**Mean time of one sort**, with the half-width of its 95% confidence interval. A time in italics is past the size at which the sort stopped: it was measured for this table, after the sweep. A blank is a size at which the sort was not run.

| Sort | n = 16 | n = 128 | n = 1,024 | n = 8,192 | n = 65,536 | n = 524,288 | n = 8,388,608 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Quicksort | 390 ns ± 0.3% | 4.99 µs ± 0.3% | 51.9 µs ± 0.5% | 505 µs ± 0.1% | 4.74 ms ± 0.2% | 43.5 ms ± 0.3% | 820 ms ± 0.8% |
| Quicksort (iterative) | 591 ns ± 0.2% | 6.25 µs ± 0.3% | 61 µs ± 0.4% | 577 µs ± 0.3% | 5.29 ms ± 0.3% | 47.9 ms ± 0.3% | 894 ms ± 0.7% |
| BFS (queue) sort | 570 ns ± 1.4% | 6.22 µs ± 0.5% | 61.1 µs ± 0.2% | 586 µs ± 0.1% | 5.52 ms ± 0.2% | 50.4 ms ± 1.8% | 975 ms ± 0.6% |
| Merge sort | 592 ns ± 0.1% | 6.72 µs ± 0.2% | 68.2 µs ± 0.4% | 654 µs ± 0.1% | 6.29 ms ± 0.5% | 58.1 ms ± 0.2% | 1.1 s ± 0.7% |
| Heap sort | 343 ns ± 0.3% | 5.07 µs ± 0.2% | 57.1 µs ± 1.0% | 559 µs ± 0.6% | 5.57 ms ± 0.3% | 57 ms ± 1.0% | 1.53 s ± 0.6% |
| Min sort | 388 ns ± 0.2% | *8.19 µs ± 0.5%* | *241 µs ± 0.3%* | *12.4 ms ± 0.2%* | *769 ms ± 0.5%* |  |  |
| Bubble sort | 425 ns ± 0.3% | *19.5 µs ± 0.1%* | *813 µs ± 0.3%* | *59.7 ms ± 0.3%* | *5.55 s ± 0.04%* |  |  |
| Shaker sort | 428 ns ± 0.6% | *16.4 µs ± 0.4%* | *692 µs ± 0.2%* | *50 ms ± 0.1%* | *4.34 s ± 0.2%* |  |  |
| Insertion sort | 183 ns ± 0.2% | 4.18 µs ± 0.3% | *199 µs ± 0.3%* | *12.4 ms ± 0.4%* | *787 ms ± 0.6%* |  |  |
| Binary insertion | 346 ns ± 0.4% | 6.5 µs ± 0.7% | *95.8 µs ± 0.3%* | *2.85 ms ± 0.2%* | *151 ms ± 2.5%* |  |  |
| Shell sort | 369 ns ± 0.2% | 5.17 µs ± 0.6% | 71.6 µs ± 0.5% | *1.21 ms ± 0.2%* | *13.3 ms ± 0.6%* | *134 ms ± 0.2%* | *2.64 s ± 0.4%* |

**At n = 8,388,608**, the largest size: time and counts divided by n log₂ n.

| Sort | Time / (n log₂ n) | Comparisons / (n log₂ n) | Moves / (n log₂ n) | Rounds |
|---|---:|---:|---:|---:|
| Quicksort | 4.25 ns | 1.416 | 0.695 | 50 |
| Quicksort (iterative) | 4.63 ns | 1.412 | 0.696 | 50 |
| BFS (queue) sort | 5.05 ns | 1.412 | 0.695 | 50 |
| Merge sort | 5.72 ns | 1.000 | 2.000 | 50 |
| Heap sort | 7.93 ns | 2.914 | 1.179 | 50 |
| Shell sort | 13.70 ns | 5.083 | 9.409 | 50 |

328 Pilot sessions, 26,558 rounds, 1.4 hours. Every session converged.

<!-- /tables -->

### What the numbers say

The order of each sort is known from its analysis; the benchmark measures
the constants. The time of a sort is c · f(n) plus terms of lower order,
where f(n) is n² or n log₂ n, and c is the time per unit of f(n) for that
sort on this machine. It is never 1, it differs from sort to sort, and it
can change with n, as the keys outgrow a cache. Time divided by f(n), in
the figures and in the table at the largest size, is c when n is large
enough for the terms of lower order not to matter.

- **Where the quadratic sorts stop.** Bubble sort and shaker sort were
  slower than the slowest O(n log n) sort from n = 32, min sort from 91,
  and insertion sort and binary insertion from 362. At those sizes the
  slowest O(n log n) sort is merge sort. Against quicksort, insertion sort
  is faster up to n = 128, binary insertion up to 23, min sort up to 16 (but not at n = 3),
  and bubble sort and shaker sort up to 11. Insertion sort is the fastest
  of all the sorts from n = 2 to 128.
- **Past where they stop.** The counts are what the analysis says they
  are (see the last item): bubble sort makes n²/2 comparisons at every
  size. What changes with n is c, the time per n². At n = 1,024, 8,192 and
  65,536 it was 0.19, 0.185 and 0.183 ns for insertion sort, and 0.23,
  0.185 and 0.179 ns for min sort; for bubble sort it was 0.78, 0.89 and
  1.29 ns, and for shaker sort 0.66, 0.75 and 1.01 ns. Bubble sort and
  shaker sort go over the whole array on every pass, and at n = 65,536 the
  array is 256 KB, as large as the L2 cache of dmz; the counters of the
  cache were not measured for them, so that is not shown to be the cause.
  At n = 65,536 bubble sort takes 5.55 s, where quicksort takes 4.7 ms.
- **Binary insertion** makes few comparisons, 0.91 n log₂ n at n = 65,536,
  but it still moves about n²/4 keys, as insertion sort does, so it is
  Θ(n²) in time on random keys. It stopped at the same size as insertion
  sort, and past it the difference widens: it is 2.1 times as fast
  as insertion sort at n = 1,024, and 5.2 times at 65,536. Its time per n²
  was 0.091, 0.042 and 0.035 ns at n = 1,024, 8,192 and 65,536: the
  n log₂ n comparisons are of lower order, but at these sizes they are not
  small beside the n²/4 moves, so time per n² is still falling toward c.
- **Shell sort** kept up with the O(n log n) sorts until n = 1,024, where it
  took 1.38 times as long as quicksort and was slower than merge sort. It
  makes a pass for every gap of its table below n, and its comparisons
  divided by n log₂ n rise from 3.5 at n = 1,024 to 5.4 at 524,288. Past the
  largest gap, 472,392, the number of passes is fixed at 100. Its time
  divided by n log₂ n was 13.5 ns at n = 524,288 and 13.7 ns at 8,388,608.
  Two sizes do not establish an order.
- **Quicksort**, the recursive one, is the fastest sort from n = 181 to the
  largest size. The iterative one is 9 to 18% slower from n = 1,024 up, and
  52% slower at n = 16; it keeps its stack in memory that it allocates, and
  pushes and pops two entries for every partition. All three quicksorts
  make the same 1.41 n log₂ n comparisons.
- **BFS sort** takes 1.14 to 1.20 times as long as quicksort from n = 1,024
  up, and 1.46 times at n = 16. Before the change to `succ` (see below) it
  took 1.33 to 1.97 times as long, and it was the slowest of the O(n log n)
  sorts at every size at which a quadratic sort stopped. The time is not
  in the allocation of its queue, which it does once for each sort:
  allocating and freeing the queue takes 27 ns at n = 16, at most 7% of
  the difference, and about 1% from n = 128 up. The hardware counters of
  dmz (`perf stat`), with `succ` as it was, divide the difference in two.

  | n | Cycles, quicksort | Cycles, BFS sort | Saved without the division | Cycles the divider is busy | L1 misses, quicksort / BFS | L2 misses, quicksort / BFS |
  |---:|---:|---:|---:|---:|---:|---:|
  | 16 | 1,576 | 3,007 | 761 (53%) | 613 | 1 / 1 | 2 / 2 |
  | 2,048 | 434 K | 616 K | 102 K (56%) | 83 K | 163 / 248 | 190 / 233 |
  | 65,536 | 18.4 M | 24.5 M | 3.2 M (52%) | 2.7 M | 24 K / 127 K | 14 K / 108 K |

  About half was the integer division in `succ`, `(n + 1) % q->size`, which
  ran for every `enqueue` and `dequeue`, four times for each partition. The
  divisions cannot overlap, since each index is computed from the one before
  it, and each takes about 26 cycles. `succ` now compares with the size and
  wraps to 0, `n + 1 == q->size ? 0 : n + 1`, which is what the sweep
  measured. The other half depends on n. Up to n = 2,048 the array is in
  the L1 cache and the misses are about the same; the other half is the work
  of the queue, 1,600 more instructions for each sort at n = 16. At
  n = 65,536 the array is as large as the L2 cache, and BFS sort, which goes
  over the whole array at every level, has five times the L1 misses and
  eight times the L2 misses of quicksort, which finishes one part of the
  array while that part is in the cache.
- **Heap sort** is the fastest of the O(n log n) sorts from n = 3 to 91, and
  the slowest from n = 1,048,576. It makes the most comparisons,
  2.9 n log₂ n, but that number hardly changes with n; its time per
  n log₂ n rises from 5.3 ns at n = 65,536 to 7.9 ns at 8,388,608. The
  array is larger than the 6 MB cache from 1.5 million keys, and heap sort
  goes from a parent to its children, far away in the array, where the
  others go through it in order.
- **Merge sort** makes the fewest comparisons, n log₂ n, and 2 n log₂ n
  moves, because it copies both halves at every level, and it allocates
  them with `malloc`. It takes 1.30 to 1.38 times as long as quicksort from
  n = 128 up, and is the slowest of the O(n log n) sorts from n = 16 to
  741,455.
- **The counts agree with the theory.** At n = 65,536, divided by n²,
  insertion sort's comparisons and moves are 1/4, min sort's comparisons
  1/2 and its moves 0, and bubble sort's comparisons 1/2 and its moves 3/4,
  three moves for each of the n²/4 swaps. Shaker sort makes the same moves
  as bubble sort, and 3/8 n² comparisons.

## Reproducing

You need [Pilot](https://github.com/darrelllong/pilot-bench), at commit
`f01eec4` or later, built in `~/pilot-bench` (or set `PILOT_BENCH_CLI` to its
`build/cli/bench`), and Python 3 for the scripts, which use nothing outside
its standard library.

```
make pilot_sort
taskset -c 3 scripts/bench_pilot.py      # writes bench/results.csv
scripts/plot.py                          # writes figures/*.svg
scripts/tables.py                        # writes the tables of README.md
taskset -c 9 scripts/bench_shell_gaps.py # writes bench/shell_gaps.csv
```

`bench_pilot.py` runs the sweep and then the sessions past the stops for
the tables. It can be stopped and started again: it does not repeat a
session that is already in `bench/results.csv`. Pin it to a core of the
kind that you want to measure; on vinge, CPU 9 is a Cortex-X925. `graph.sh` is the older script,
which counts comparisons and moves with `sorting` and plots them with
gnuplot.

## Changes made for the benchmark

- `bfssort.c`: the queue had room for n − 1 entries. The subarrays waiting
  in it can need n, and one more slot is kept empty, so `enqueue` failed,
  silently and halfway through a pair; from then on every pair that was
  taken out was wrong. The sort did not finish for n = 5, and for n = 1 the
  queue had no room at all and `succ` divided by zero. It now has room for
  2n + 2.
- `Makefile`: `-Ofast` is deprecated in clang 21, and with `-Werror` it
  stopped the build; the sorts use no floating point, so `-O3` is the same.
  The target `pilot_sort` is new.
- `sorting.c`, `stack.h`, `stack.c`: prototypes, which C23 requires and
  clang 21 enforces. `heapSort` takes a `uint32_t` length and the table of
  sorts an `int`, so it is called through a wrapper that converts it.
- `queue.c`: `succ` found the next slot with `%`, a division on every
  enqueue and dequeue; it now compares with the size and wraps to 0.
- `shellsort.c`: the comment named the sequence for Platt; it is Pratt's.
- `pratt.c` is new: Shell sort with the whole sequence of Pratt, which
  `pilot_sort` times as `pratt`, for comparison with the table of
  `shellsort.c`.
- `pilot_sort.c`, `scripts/`, `bench/`, and `figures/` are new.
