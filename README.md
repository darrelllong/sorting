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

**Shell sort.** The gaps are numbers of the form 2ᵖ3ᵍ, as in the sequence of
Pratt, for which Shell sort is O(n log² n). The table in `shellsort.c` is
not the whole sequence: it leaves out 32 of those numbers below 629,856,
from 2,048 on (2,048, 4,096, 6,144, 8,192, …), and the loop uses the first
100 of its 102 entries. Pratt's bound needs all of them. On random keys the
table as it is does less work than the whole sequence: in one run each at
n = 8,388,608 on an Apple M4, it made 0.98 × 10⁹ comparisons in 1.07 s, against 1.51 × 10⁹
in 1.48 s for the whole sequence, because fewer gaps are fewer passes. It
is kept as it is.

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

**One measurement.** `pilot_sort` fills an array with n random 30-bit keys
from a fresh seed, sorts it, counts its comparisons and moves, and checks
the result against `qsort` of the same keys; a sort that does not sort ends
the session. A sort of a few keys is too fast to time, so it then times a
batch of sorts, each of other random keys, doubling the batch until it takes
at least 2 ms, and prints the mean time of one sort in the batch.

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

**The machine.** A benchmark can be no steadier than the machine it runs on.
These results are from `dmz`:

```
machine: dmz, Intel(R) Core(TM) i5-8259U CPU @ 2.30GHz, 8 threads, 30 GB
system: Ubuntu 26.04.1 LTS, Linux 7.0.0-31-generic
compiler: Ubuntu clang version 21.1.8 (6ubuntu1), -O3
pilot: f01eec4 Replace the changepoint detection; document the revisions since 2016, preset normal
pinned: taskset -c 3; frequency governor powersave, turbo on
date: 2026-09-27
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

**Where each sort stopped.** It was slower than the slowest O(n log n) sort at this n, and was not run at larger n.

| Sort | Stopped at n | Its time | Slowest O(n log n) sort at n | Its time |
|---|---:|---:|---|---:|
| Min sort | 128 | 8.11 µs | BFS (queue) sort | 7.98 µs |
| Bubble sort | 45 | 2.91 µs | BFS (queue) sort | 2.53 µs |
| Shaker sort | 45 | 2.76 µs | BFS (queue) sort | 2.53 µs |
| Insertion sort | 362 | 27.4 µs | BFS (queue) sort | 24.7 µs |
| Binary insertion | 512 | 37.4 µs | BFS (queue) sort | 35.8 µs |
| Shell sort | 2,048 | 167 µs | BFS (queue) sort | 158 µs |

**Mean time of one sort**, with the half-width of its 95% confidence interval. A blank is a size at which the sort was not run.

| Sort | n = 16 | n = 128 | n = 1,024 | n = 8,192 | n = 65,536 | n = 524,288 | n = 8,388,608 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Quicksort | 390 ns ± 0.4% | 5.01 µs ± 0.5% | 51.7 µs ± 0.2% | 506 µs ± 0.4% | 4.75 ms ± 0.6% | 43.8 ms ± 1.2% | 821 ms ± 1.0% |
| Quicksort (iterative) | 592 ns ± 0.2% | 6.25 µs ± 0.3% | 60.9 µs ± 0.7% | 574 µs ± 0.3% | 5.41 ms ± 4.2% | 48 ms ± 0.2% | 896 ms ± 1.1% |
| BFS (queue) sort | 770 ns ± 0.2% | 7.98 µs ± 0.3% | 75.3 µs ± 0.3% | 703 µs ± 0.7% | 6.43 ms ± 0.6% | 58.1 ms ± 3.3% | 1.09 s ± 0.9% |
| Merge sort | 592 ns ± 0.2% | 6.72 µs ± 0.2% | 68.3 µs ± 0.4% | 655 µs ± 0.2% | 6.24 ms ± 0.2% | 59.1 ms ± 3.8% | 1.11 s ± 1.1% |
| Heap sort | 343 ns ± 0.2% | 5.08 µs ± 0.3% | 56.4 µs ± 0.4% | 557 µs ± 0.2% | 5.56 ms ± 0.1% | 56.7 ms ± 0.1% | 1.53 s ± 0.7% |
| Min sort | 389 ns ± 0.2% | 8.11 µs ± 0.3% |  |  |  |  |  |
| Bubble sort | 425 ns ± 0.5% |  |  |  |  |  |  |
| Shaker sort | 421 ns ± 0.1% |  |  |  |  |  |  |
| Insertion sort | 183 ns ± 0.5% | 4.17 µs ± 0.1% |  |  |  |  |  |
| Binary insertion | 344 ns ± 0.2% | 6.46 µs ± 0.1% |  |  |  |  |  |
| Shell sort | 368 ns ± 0.2% | 5.16 µs ± 0.3% | 71.1 µs ± 0.6% |  |  |  |  |

**At n = 8,388,608**, the largest size: time and counts divided by n log₂ n.

| Sort | Time / (n log₂ n) | Comparisons / (n log₂ n) | Moves / (n log₂ n) | Rounds |
|---|---:|---:|---:|---:|
| Quicksort | 4.26 ns | 1.416 | 0.695 | 50 |
| Quicksort (iterative) | 4.64 ns | 1.414 | 0.696 | 50 |
| BFS (queue) sort | 5.66 ns | 1.415 | 0.696 | 50 |
| Merge sort | 5.74 ns | 1.000 | 2.000 | 50 |
| Heap sort | 7.95 ns | 2.914 | 1.179 | 58 |

312 Pilot sessions, 28,111 rounds, 0.9 hours. Every session converged.

<!-- /tables -->

### What the numbers say

- **Where the quadratic sorts stop.** Bubble sort and shaker sort were
  slower than the slowest O(n log n) sort from n = 45, min sort from 128,
  insertion sort from 362, and binary insertion from 512. At those sizes the
  slowest O(n log n) sort is BFS sort (see below). Against quicksort, the fastest, insertion sort is faster up to
  n = 128 and min sort up to n = 11.
- **Binary insertion** makes few comparisons, about n log₂ n, but it still
  moves about n²/4 keys, as insertion sort does, so it is quadratic in time.
  The comparisons it saves let it run a little further than insertion sort.
- **Shell sort** kept up with the O(n log n) sorts until n = 2,048. With
  these gaps it makes a pass for every 2ᵖ3ᵍ below n, so its time grows as
  n log² n; at n = 2,048 it took 1.5 times as long as quicksort, and was
  slower than BFS sort.
- **Quicksort**, the recursive one, is the fastest sort from n = 128 to the
  largest size. The iterative one is 9 to 18% slower from n = 1,024 up, and
  52% slower at n = 16; it keeps its stack in memory that it allocates, and
  pushes and pops two entries for every partition. All three quicksorts
  make the same 1.41 n log₂ n comparisons.
- **BFS sort** is 1.3 to 1.9 times as slow as quicksort, and it is not for
  the allocation of its queue, which it does once for each sort: allocating
  and freeing the queue takes 27 ns at n = 16, at most 7% of the difference,
  and about 1% from n = 128 up. More than half of the difference is the
  integer division in `succ`, `(n + 1) % q->size`, which runs for every
  `enqueue` and `dequeue`, four times for each partition. With a comparison
  in its place, in a copy that was only measured, BFS sort took 1.41 times
  as long as quicksort at n = 16 in place of 1.88, and 1.16 times at
  n = 65,536 in place of 1.33. The rest is the other work of the queue, and
  the breadth-first order, which goes over the whole array at every level
  where quicksort finishes one part of it while that part is in the cache.
- **Heap sort** is the fastest from n = 3 to 91, and the slowest from about a
  million keys. It makes the most comparisons, 2.9 n log₂ n, but that
  number hardly changes with n; its time per n log₂ n rises from 5.3 ns at
  n = 65,536 to 8.0 ns at 8,388,608. The array is larger than the 6 MB cache
  from 1.5 million keys, and heap sort goes from a parent to its children,
  far away in the array, where the others go through it in order.
- **Merge sort** makes the fewest comparisons, n log₂ n, and 2 n log₂ n moves,
  because it copies both halves at every level, and it allocates them with
  `malloc`. It is in the middle.
- **The counts agree with the theory.** Divided by n², insertion sort's
  comparisons and moves go to 1/4, min sort's comparisons to 1/2 and its
  moves to 0, and bubble sort's comparisons to 1/2 and its moves to 3/4, three
  moves for each of the n²/4 swaps.

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
```

The sweep can be stopped and started again: it does not repeat a session
that is already in `bench/results.csv`. `graph.sh` is the older script,
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
- `pilot_sort.c`, `scripts/`, `bench/`, and `figures/` are new.
