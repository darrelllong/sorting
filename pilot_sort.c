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
// If PILOT_SORT_EVENTS is set, it is a list of hardware events, separated by
// commas, that are counted over the timed batch, and the mean count of each
// for one sort is printed after the moves, in the same order. An event is
// cycles, instructions, branches, branch-misses, or rXXXX, a raw event in
// hexadecimal as perf(1) takes it. They are counted in user mode, as one
// group; if the kernel could not count them all for the whole batch, the
// run fails rather than print an estimate. This needs Linux, and
// kernel.perf_event_paranoid at 2 or less.
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

#ifdef __linux__
#include <linux/perf_event.h>
#include <sys/ioctl.h>
#include <sys/syscall.h>
#endif

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

#define MAX_EVENTS 8

static int events = 0;
static uint64_t counts[MAX_EVENTS];

#ifdef __linux__
static int fd[MAX_EVENTS];

static bool open_events(char *spec) {
    for (char *name = strtok(spec, ","); name; name = strtok(NULL, ",")) {
        if (events == MAX_EVENTS) {
            return false;
        }
        struct perf_event_attr a;
        memset(&a, 0, sizeof(a));
        a.size = sizeof(a);
        a.type = PERF_TYPE_HARDWARE;
        if (strcmp(name, "cycles") == 0) {
            a.config = PERF_COUNT_HW_CPU_CYCLES;
        } else if (strcmp(name, "instructions") == 0) {
            a.config = PERF_COUNT_HW_INSTRUCTIONS;
        } else if (strcmp(name, "branches") == 0) {
            a.config = PERF_COUNT_HW_BRANCH_INSTRUCTIONS;
        } else if (strcmp(name, "branch-misses") == 0) {
            a.config = PERF_COUNT_HW_BRANCH_MISSES;
        } else if (name[0] == 'r' && name[1]) {
            char *end;
            a.type = PERF_TYPE_RAW;
            a.config = strtoull(name + 1, &end, 16);
            if (*end) {
                return false;
            }
        } else {
            return false;
        }
        a.disabled = events == 0;
        a.exclude_kernel = 1;
        a.exclude_hv = 1;
        a.read_format = PERF_FORMAT_GROUP | PERF_FORMAT_TOTAL_TIME_ENABLED
            | PERF_FORMAT_TOTAL_TIME_RUNNING;
        fd[events] = (int) syscall(SYS_perf_event_open, &a, 0, -1, events ? fd[0] : -1, 0);
        if (fd[events] < 0) {
            perror(name);
            return false;
        }
        events += 1;
    }
    return events > 0;
}

static void start_events(void) {
    if (events) {
        ioctl(fd[0], PERF_EVENT_IOC_RESET, PERF_IOC_FLAG_GROUP);
        ioctl(fd[0], PERF_EVENT_IOC_ENABLE, PERF_IOC_FLAG_GROUP);
    }
}

static bool stop_events(void) {
    if (!events) {
        return true;
    }
    ioctl(fd[0], PERF_EVENT_IOC_DISABLE, PERF_IOC_FLAG_GROUP);
    uint64_t buf[3 + MAX_EVENTS];
    if (read(fd[0], buf, sizeof(buf)) < (ssize_t) ((3 + events) * sizeof(uint64_t))
        || buf[0] != (uint64_t) events || buf[1] == 0 || buf[1] != buf[2]) {
        return false; // not counted, or multiplexed with other events
    }
    memcpy(counts, buf + 3, events * sizeof(uint64_t));
    return true;
}
#else
static bool open_events(char *spec) {
    (void) spec;
    return false;
}

static void start_events(void) {
}

static bool stop_events(void) {
    return true;
}
#endif

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

    char *spec = getenv("PILOT_SORT_EVENTS");
    if (spec && *spec && !open_events(spec)) {
        fprintf(stderr, "%s: cannot count the events %s\n", argv[0], getenv("PILOT_SORT_EVENTS"));
        return 1;
    }

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
        start_events();
        double start = now_ns();
        for (long r = 0; r < reps; r += 1) {
            sort(pool + (size_t) r * n, n);
        }
        elapsed = now_ns() - start;
        if (!stop_events()) {
            fprintf(stderr, "%s: the events were not counted for the whole batch\n", argv[0]);
            return 1;
        }
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

    printf("%.3f,%.3f,%.3f", elapsed / reps, (double) compares / reps, (double) moves / reps);
    for (int e = 0; e < events; e += 1) {
        printf(",%.3f", (double) counts[e] / reps);
    }
    printf("\n");
    return 0;
}
