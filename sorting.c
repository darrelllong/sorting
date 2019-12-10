#include <inttypes.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/sem.h>
#include <sys/wait.h>
#include <sys/ipc.h>
#include <unistd.h>

#include "binsert.h"
#include "bubblesort.h"
#include "bv.h"
#include "heapsort.h"
#include "insertionsort.h"
#include "mergesort.h"
#include "minsort.h"
#include "quicksort.h"
#include "shakersort.h"
#include "shellsort.h"
#include "stack.h"
#include "semwrapper.h"

#define RANDOM random
#define SRANDOM srandom

#ifndef MASK
#define MASK 0x00ffffff
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
  MergeSort,
  HeapSort,
  EndSort
} sorts;


#define MAX 100
#define SEED 8062022
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
    printf("%10d", a[i]);
    if ((i + 1) % WIDTH == 0) {
      printf("\n");
    }
  }
  if (printMax % WIDTH != 0 || length % WIDTH != 0) {
    printf("\n");
  }
  return;
}

#define OPTIONS "-uAmbSBisqQMhzp:r:n:"

static char *names[] = { "Min Sort", "Bubble Sort", "Shaker Sort", "Insertion Sort",
                         "Binary Insertion Sort", "Shell Sort", "Quick Sort", 
                         "Quick Sort (Iterative)", "Merge Sort", "Heap Sort" };

int main(int argc, char **argv) {
  int c = 0;
  int seed = SEED; // Default random seed
  int count = MAX; // Sort 100 by default

  uint32_t *a; // Array to be sorted

  bitV *sortSet = newVec(EndSort); // Set of sorts to perform

  int sem = sem_create(ftok("/tmp/ddel", 0xc0c0d00d), 1);


  while ((c = getopt(argc, argv, OPTIONS)) != -1) {
    switch (c) {
    case 'A': {
      for (sorts s = MinSort; s < EndSort; s += 1) {
        setBit(sortSet, s);
      }
      break;
    }
    case 'u': {
      setBit(sortSet, EndSort);
      break;
    }
    case 'm': {
      setBit(sortSet, MinSort);
      break;
    }
    case 'b': {
      setBit(sortSet, BubbleSort);
      break;
    }
    case 'S': {
      setBit(sortSet, ShakerSort);
      break;
    }
    case 'B': {
      setBit(sortSet, BinaryInsertion);
      break;
    }
    case 'i': {
      setBit(sortSet, InsertionSort);
      break;
    }
    case 's': {
      setBit(sortSet, ShellSort);
      break;
    }
    case 'q': {
      setBit(sortSet, QuickSort);
      break;
    }
    case 'M': {
      setBit(sortSet, MergeSort);
      break;
    }
    case 'Q': {
      setBit(sortSet, QSI);
      break;
    }
    case 'h': {
      setBit(sortSet, HeapSort);
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

  if (valBit(sortSet, EndSort) == 1) {
    SRANDOM(seed); // Where shall we start?
    fillArray(a, count); // Random numbers
    printf("Unsorted\n");
    printArray(a, count);
  }

  int pid;
  sorts t;

  for (sorts s = MinSort; s < EndSort; s += 1) {
    if (valBit(sortSet, s) == 1) {
      t = s;
      if ((pid = fork()) == 0) {
        break;
      }
    }
  }

  if (pid == 0) {
    compares = 0; moves = 0; // Reset statistics
    SRANDOM(seed); // Where shall we start?
    fillArray(a, count); // Random numbers

    switch (t) {
    case MinSort:         { minSort(a, count); break; }
    case BubbleSort:      { bubbleSort(a, count); break; }
    case ShakerSort:      { shakerSort(a, count); break; }
    case InsertionSort:   { insertionSort(a, count); break; }
    case BinaryInsertion: { binaryInsertionSort(a, count); break; }
    case ShellSort:       { shellSort(a, count); break; }
    case QuickSort:       { qSort(a, count); break; }
    case QSI:             { qSortI(a, count); break; }
    case MergeSort:       { mergeSort(a, count); break; }
    case HeapSort:        { heapSort(a, count); break; }
    case EndSort:         { break; } // Nothing
    }

    // P the semaphore
    sem_wait(sem, 0);
    printf("%s\n", names[t]); fflush(stdout);

    printf("%" PRIu32 " elements %" PRIu64 " moves %" PRIu64 " compares\n",
        count, moves, compares); fflush(stdout);
    printArray(a, count);
    // V the semaphore
    sem_signal(sem, 0);
  } else {
    for (sorts s = MinSort; s < EndSort; s += 1) {
      if (valBit(sortSet, s) == 1) {
        wait((int *)0);
      }
    }
  }
  free(a);
  delVec(sortSet);

  return 0;
}
