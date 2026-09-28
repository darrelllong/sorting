//
// pilot_sort: one measurement of one sort, for the Pilot benchmark framework
//
// Usage: pilot_sort sort n
//
// Each run sorts arrays of n random 30-bit keys from a fresh seed, checks
// that each is in order, and prints one line:
//
//     nanoseconds per sort,compares per sort,moves per sort
//
// Pilot runs it again and again, and each run is one reading, until the
// confidence interval of the mean is as narrow as it was asked to be.
//
// A sort of a few elements takes less time than the clock can resolve, so a
// batch of sorts is timed, and the number in the batch is doubled until the
// batch takes at least BATCH_NS. Every sort in the batch is of other random
// keys. A sort that is repeated on the same keys is faster than it should
// be, because the branch predictor learns the branches of those keys: for
// n = 181 on an Intel i5-8259U, quicksort and heap sort took a third as
// long, and insertion sort 91% as long.
//
// The compares and moves are counted by the sorts as they are timed, and are
// the means over the batch. Each array is checked to be in order after the
// timing.
//

#include "bfssort.h"
#include "binsert.h"
#include "bubblesort.h"
#include "heapsort.h"
#include "insertionsort.h"
#include "mergesort.h"
#include "minsort.h"
#include "pratt.h"
#include "quicksort.h"
#include "shakersort.h"
#include "shellsort.h"

#include <inttypes.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/random.h>
#include <time.h>
#include <unistd.h>

#define MASK     ((1u << 30) - 1)
#define BATCH_NS 2000000.0 // 2 ms

uint64_t moves, compares;

static void heapSortInt(uint32_t a[], int n) {
    heapSort(a, (uint32_t) n);
}

static const struct {
    const char *key;
    void (*sort)(uint32_t[], int);
} sorts[] = {
    { "min", minSort },
    { "bubble", bubbleSort },
    { "shaker", shakerSort },
    { "insertion", insertionSort },
    { "binsert", binaryInsertionSort },
    { "shell", shellSort },
    { "pratt", shellSortPratt },
    { "quick", qSort },
    { "quicki", qSortI },
    { "bfs", BFSSort },
    { "merge", mergeSort },
    { "heap", heapSortInt },
};

static double now_ns(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1e9 + t.tv_nsec;
}

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "Usage: %s sort n\n", argv[0]);
        return 2;
    }
    void (*sort)(uint32_t[], int) = NULL;
    for (size_t i = 0; i < sizeof(sorts) / sizeof(sorts[0]); i += 1) {
        if (strcmp(argv[1], sorts[i].key) == 0) {
            sort = sorts[i].sort;
        }
    }
    int n = atoi(argv[2]);
    if (!sort || n < 1) {
        fprintf(stderr, "%s: unknown sort or bad n\n", argv[0]);
        return 2;
    }

    // A fresh seed for every run, so that every reading is of another input
    uint32_t seed;
    if (getentropy(&seed, sizeof(seed)) != 0) {
        seed = (uint32_t) (time(NULL) ^ getpid());
    }
    srandom(seed);

    // As many sorts, each of other keys, as take at least BATCH_NS
    long reps = 1;
    double elapsed;
    uint32_t *pool = NULL;
    for (;;) {
        pool = realloc(pool, (size_t) reps * n * sizeof(uint32_t));
        if (!pool) {
            fprintf(stderr, "%s: out of memory\n", argv[0]);
            return 1;
        }
        for (size_t i = 0; i < (size_t) reps * n; i += 1) {
            pool[i] = random() & MASK;
        }
        compares = moves = 0;
        double start = now_ns();
        for (long r = 0; r < reps; r += 1) {
            sort(pool + (size_t) r * n, n);
        }
        elapsed = now_ns() - start;
        if (elapsed >= BATCH_NS) {
            break;
        }
        reps *= 2;
    }

    for (long r = 0; r < reps; r += 1) {
        const uint32_t *a = pool + (size_t) r * n;
        for (int i = 1; i < n; i += 1) {
            if (a[i - 1] > a[i]) {
                fprintf(stderr, "%s: %s did not sort %d elements (seed %" PRIu32 ")\n", argv[0],
                    argv[1], n, seed);
                return 1;
            }
        }
    }
    free(pool);

    printf("%.3f,%.3f,%.3f\n", elapsed / reps, (double) compares / reps, (double) moves / reps);
    return 0;
}
