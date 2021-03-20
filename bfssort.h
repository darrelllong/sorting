#pragma once
#include <stdint.h>

extern uint64_t moves, compares;

#ifndef SWAP
#define SWAP(x, y)                                                             \
  {                                                                            \
    uint32_t t = x;                                                            \
    x = y;                                                                     \
    y = t;                                                                     \
    moves += 3;                                                                \
  }
#endif

void BFSSort(uint32_t a[], int length);
