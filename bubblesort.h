#pragma once

#include <stdint.h>

#ifndef SWAP
#define SWAP(x, y) { \
 uint32_t t = x;     \
 x = y;              \
 y = t;              \
 moves += 3;         \
}
#endif

extern uint64_t moves, compares;

void bubbleSort(uint32_t[], int);
