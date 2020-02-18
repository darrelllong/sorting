CFLAGS=-Wall -Werror -Wextra -pedantic -Ofast
CC=clang
OBJS=sorting.o bubblesort.o minsort.o insertionsort.o quicksort.o schlubsort.o \
mergesort.o shellsort.o heapsort.o stack.o binsert.o shakersort.o semaphore.o \
tiniklingsort.o

UNAME=$(shell uname -s)
ifeq ($(UNAME), Linux)
	CFLAGS+=-DLAME
endif

sorting	: Makefile $(OBJS)
	$(CC) -o sorting $(OBJS)

sorting.o	:	sorting.c
	$(CC) $(CFLAGS) -c sorting.c

clean	:
	rm -rf $(OBJS) sorting infer-out
infer	:
	make clean; infer-capture -- make; infer-analyze -- make
