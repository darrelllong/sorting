CFLAGS=-Wall -Werror -Wextra -pedantic -O3
CC=clang
SORTS=bubblesort.o minsort.o insertionsort.o quicksort.o mergesort.o \
shellsort.o heapsort.o stack.o binsert.o shakersort.o bfssort.o queue.o
OBJS=sorting.o semaphore.o $(SORTS)

UNAME=$(shell uname -s)
ifeq ($(UNAME), Linux)
	CFLAGS+=-DLAME
endif

sorting	: Makefile $(OBJS)
	$(CC) -o sorting $(OBJS)

sorting.o	:	sorting.c
	$(CC) $(CFLAGS) -c sorting.c

pilot_sort	: Makefile pilot_sort.o $(SORTS)
	$(CC) -o pilot_sort pilot_sort.o $(SORTS)

clean	:
	rm -rf $(OBJS) pilot_sort.o sorting pilot_sort infer-out *.png
infer	:
	make clean; infer-capture -- make; infer-analyze -- make
