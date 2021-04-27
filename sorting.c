#include "bfssort.h"
#include "binsert.h"
#include "bubblesort.h"
#include "heapsort.h"
#include "insertionsort.h"
#include "mergesort.h"
#include "minsort.h"
#include "quicksort.h"
#include "semaphore.h"
#include "sets.h"
#include "shakersort.h"
#include "shellsort.h"

#include <inttypes.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/ipc.h>
#include <sys/sem.h>
#include <sys/time.h>
#include <sys/wait.h>
#include <unistd.h>

#define RANDOM  random
#define SRANDOM srandom

#ifndef MASK
#define MASK ((1 << 30) - 1)
#endif

typedef enum sorts {
    MinSort,
    BubbleSort,
    ShakerSort,
    InsertionSort,
    BinaryInsertion,
    ShellSort,
    QuickSort,
    QSI,
    QueueSort,
    MergeSort,
    HeapSort,
    EndSort
} sorts;

#define MAX   100
#define SEED  8062022
#define WIDTH 7

uint64_t moves, compares;

static int printMax = MAX;

static bool sortedData = false;

void fillArray(uint32_t a[], int length) {
    for (int i = 0; i < length; i += 1) {
        a[i] = sortedData ? i : RANDOM() & MASK;
    }
    return;
}

void printArray(uint32_t a[], int length) {
    for (int i = 0; i < length && i < printMax; i += 1) {
        printf("%12d", a[i]);
        if ((i + 1) % WIDTH == 0) {
            putchar('\n');
        }
    }
    if (length % WIDTH != 0) {
        putchar('\n');
    }
    putchar('\n');
    return;
}

#define OPTIONS "-dAmbSBisqQXMHhzp:r:n:"

static char *names[] = { "Min Sort", "Bubble Sort", "Shaker Sort", "Insertion Sort",
    "Binary Insertion Sort", "Shell Sort", "Quick Sort", "Quick Sort (Iterative)",
    "BFS (queue) Sort", "Merge Sort", "Heap Sort" };

static void (*sort[EndSort])();

double hickoryDickory(void) {
    struct timeval t;
    gettimeofday(&t, (struct timezone *) 0);
    return t.tv_sec + t.tv_usec / 1000000.0;
}

int main(int argc, char **argv) {
    int c = 0;
    int seed = SEED; // Default random seed
    int count = MAX; // Sort 100 by default
    bool dataMode = false;

    uint32_t *a; // Array to be sorted

    set sortSet = 0;

    sort[MinSort] = minSort;
    sort[BubbleSort] = bubbleSort;
    sort[ShakerSort] = shakerSort;
    sort[InsertionSort] = insertionSort;
    sort[BinaryInsertion] = binaryInsertionSort;
    sort[ShellSort] = shellSort;
    sort[QuickSort] = qSort;
    sort[QSI] = qSortI;
    sort[QueueSort] = BFSSort;
    sort[MergeSort] = mergeSort;
    sort[HeapSort] = heapSort;

    int sem = sem_create();

    while ((c = getopt(argc, argv, OPTIONS)) != -1) {
        switch (c) {
        case 'd': {
            dataMode = true;
            break;
        }
        case 'A': {
            for (sorts s = MinSort; s < EndSort; s += 1) {
                sortSet = insertSet(s, sortSet);
            }
            break;
        }
        case 'm': {
            sortSet = insertSet(MinSort, sortSet);
            break;
        }
        case 'b': {
            sortSet = insertSet(BubbleSort, sortSet);
            break;
        }
        case 'S': {
            sortSet = insertSet(ShakerSort, sortSet);
            break;
        }
        case 'B': {
            sortSet = insertSet(BinaryInsertion, sortSet);
            break;
        }
        case 'i': {
            sortSet = insertSet(InsertionSort, sortSet);
            break;
        }
        case 's': {
            sortSet = insertSet(ShellSort, sortSet);
            break;
        }
        case 'q': {
            sortSet = insertSet(QuickSort, sortSet);
            break;
        }
        case 'M': {
            sortSet = insertSet(MergeSort, sortSet);
            break;
        }
        case 'Q': {
            sortSet = insertSet(QSI, sortSet);
            break;
        }
        case 'X': {
            sortSet = insertSet(QueueSort, sortSet);
            break;
        }
        case 'h': {
            sortSet = insertSet(HeapSort, sortSet);
            break;
        }
        case 'H': {
            printf("Usage: sorting -options\n"
                   "\t-d data only mode\n"
                   "\t-n <length>\n"
                   "\t-p <number to print>\n"
                   "\t-A All sorts\n"
                   "\t-m Minimum sort\n"
                   "\t-b Bubble sort\n"
                   "\t-B Binary insertion sort\n"
                   "\t-M Merge Sort\n"
                   "\t-q QuickSort (recursive)\n"
                   "\t-Q QuickSort (iterative)\n"
                   "\t-X BFS Sort (iterative)\n"
                   "\t-h HeapSort\n"
                   "\t-i Insertion sort\n"
                   "\t-s Shell sort\n"
                   "\t-S Shaker sort\n");
            break;
        }
        case 'z': {
            sortedData = true;
            break;
        }
        case 'p': {
            printMax = atoi(optarg);
            printMax = printMax >= 0 ? printMax : MAX;
            break;
        }
        case 'r': {
            seed = atoi(optarg);
            break;
        }
        case 'n': {
            count = atoi(optarg);
            count = count > 0 ? count : MAX;
            break;
        }
        }
    }

    a = calloc(count, sizeof(uint32_t));

    int pid;
    sorts t;

    // Spawn a process for each sort
    for (sorts s = MinSort; s < EndSort; s += 1) {
        if (memberSet(s, sortSet)) {
            t = s;
            if ((pid = fork()) == 0) {
                break;
            }
        }
    }

    if (pid == 0) {
        compares = 0;
        moves = 0; // Reset statistics
        SRANDOM(seed); // Starting position

        fillArray(a, count); // Load the array
        double before = hickoryDickory();
        sort[t](a, count); // Perform the sort
        double after = hickoryDickory();

        sem_wait(sem); // P the semaphore
        if (dataMode) {
            printf("%" PRIu32 " %" PRIu64 " %" PRIu64 " %lf %s\n", count, moves, compares,
                after - before, names[t]);

        } else {
            printf("%s\n", names[t]);
            fflush(stdout);

            printf("%" PRIu32 " elements %" PRIu64 " moves %" PRIu64 " compares\n", count, moves,
                compares);
            fflush(stdout);
            printArray(a, count);
        }
        sem_signal(sem); // V the semaphore
    } else {
        // Reap what we have sown
        for (sorts s = MinSort; s < EndSort; s += 1) {
            if (memberSet(s, sortSet)) {
                wait((int *) 0);
            }
        }
        sem_delete(sem); // Let the parent delete it once all children are dead
    }
    free(a);

    return 0;
}
