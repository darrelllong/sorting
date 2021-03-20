#pragma once

#include <stdbool.h>
#include <stdint.h>

typedef struct queue {
    uint32_t head;
    uint32_t tail;
    uint32_t size;
    int *Q;
} queue;

queue *newQueue(uint32_t);

void delQueue(queue *);

bool emptyQ(queue *);

bool fullQ(queue *);

bool enqueue(queue *, int);

bool dequeue(queue *, int *);
