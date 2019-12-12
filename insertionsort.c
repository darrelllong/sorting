#include "insertionsort.h"
#include <stdint.h>

void insertionSort(uint32_t a[], int length) {
  for (int i = 1; i < length; i += 1) {
    int j = i;
    uint32_t tmp = a[i];
    while (++compares && j > 0 && a[j - 1] > tmp) { // Linear search and move to the position
      a[j] = a[j - 1];
      j -= 1;
      moves += 1;
    }
    a[j] = tmp; // Put it in place
    moves += 1;
  }
  return;
}
