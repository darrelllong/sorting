#include "pratt.h"

#include <stdint.h>

//
// shellSortPratt
//
// Shell sort with the whole sequence of Pratt: every number 2^p 3^q up to
// 472,392, the largest gap that shellSort uses. It is here only to be timed
// against shellSort, whose table leaves 28 of these out.
//

#define LARGEST 472392

void shellSortPratt(uint32_t data[], int length) {
    int h[128], hl = 0;

    // The numbers 2^p 3^q, in increasing order, by merging the multiples
    // of 2 and of 3 of the numbers already found
    int i2 = 0, i3 = 0;
    h[hl++] = 1;
    for (;;) {
        int a = 2 * h[i2], b = 3 * h[i3];
        int next = a < b ? a : b;
        if (next > LARGEST) {
            break;
        }
        h[hl++] = next;
        i2 += a == next;
        i3 += b == next;
    }

    for (int s = hl - 1; s >= 0; s -= 1) {
        int step = h[s];

        for (int j = step; j < length; j += 1) {
            uint32_t key = data[j]; moves += 1;
            int i = j - step;

            while (++compares && i >= 0 && data[i] > key) {
                data[i + step] = data[i]; moves += 1;
                i -= step;
            }
            data[i + step] = key; moves += 1;
        }
    }
    return;
}
