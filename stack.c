#include "stack.h"

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static int depth = 0, max_depth = 0;

stack *newStack() {
    stack *s = (stack *) calloc(MIN_STACK, sizeof(stack));
    if (s) {
        s->size = MIN_STACK;
        s->top = 0;
        s->entries = (item *) calloc(MIN_STACK, sizeof(item));
        return s;
    } else {
        return (stack *) 0;
    }
}

void delStack(stack *s) {
    if (s && s->entries) {
        free(s->entries);
        free(s);
    }
    printf("stack depth = %d\n", max_depth);
    return;
}

item pop(stack *s) {
    if (s && s->top > 0) {
        depth -= 1;
        s->top -= 1;
        return s->entries[s->top];
    } else {
        return INVALID;
    }
}

void push(stack *s, item i) {
    if (s) {
        if (s->top == s->size) {
            s->size *= 2;
            s->entries = (item *) realloc(s->entries, s->size * sizeof(item));
        }
        if (s->entries) {
            s->entries[s->top] = i;
            s->top += 1;
        }
    }
    depth += 1;
    max_depth = depth > max_depth ? depth : max_depth;
    return;
}

bool empty(stack *s) {
    return s && s->top == 0;
}
