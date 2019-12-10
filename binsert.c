#include "binsert.h"
#include <stdint.h>

void binaryInsertionSort(uint32_t a[], int length) {
  for (int i = 1; i < length; i += 1) {
    int left = 0, right = i - 1;
    uint32_t temporary = a[i];
    while (++compares && right >= left) {
      int middle = (left + right) / 2;
      if (temporary < a[middle]) {
        right = middle - 1;
      } else {
        left = middle + 1;
      }
    }
    for (int j = i - 1; left <= j; j -= 1) {
      a[j + 1] = a[j];
      moves += 1;
    }
    a[left] = temporary;
    moves += 1;
  }
  return;
}
