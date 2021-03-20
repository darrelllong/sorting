#ifndef _TINIKLINGSORT_H
#define _TINIKLINGSORT_H

#include <stdint.h>

#ifndef SWAP
#define SWAP(x, y)                                                                                 \
    {                                                                                              \
        uint32_t t = x;                                                                            \
        x = y;                                                                                     \
        y = t;                                                                                     \
        moves += 3;                                                                                \
    }
#endif

extern uint64_t moves, compares;

void tiniklingSort(uint32_t[], uint32_t);

#endif
