#include "bfssort.h"
#include "queue.h"
#include <stdint.h>

static int partition(uint32_t a[], int32_t low, int32_t high) {
  uint32_t pivotValue = a[(low + high) / 2];

  int32_t i = low - 1;
  int32_t j = high + 1;
  do {
    do {
      i += 1;
    } while (++compares && a[i] < pivotValue);
    do {
      j -= 1;
    } while (++compares && a[j] > pivotValue);
    if (i < j) {
      SWAP(a[i], a[j]);
    }
  } while (i < j);
  return j;
}

void BFSSortI(uint32_t a[], int left, int right) {
  queue *s = newQueue(1000000);

  enqueue(s, left);
  enqueue(s, right);
  while (!emptyQ(s)) {
    int low; dequeue(s, &low);
    int high; dequeue(s, &high);
    int p = partition(a, low, high);
    if (p + 1 < high) {
      enqueue(s, p + 1);
      enqueue(s, high);
    }
    if (low < p) {
      enqueue(s, low);
      enqueue(s, p);
    }
  }
  delQueue(s);
  return;
}

void BFSSort(uint32_t a[], int length) {
  BFSSortI(a, 0, length - 1);
}
