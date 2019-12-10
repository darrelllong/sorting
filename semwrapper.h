#ifndef __SEMWRAPPER_H__
#define __SEMWRAPPER_H__

#include <sys/sem.h>

//
// Returns the identifier of one initialized semaphore.
// The semaphore is generated using a key.
// The key can be generated using ftok() using a pathname.
//
// key:   The key to create a set of semaphores with.
//
int sem_create(key_t key);

//
// Removes the specified semaphore from the system.
//
// semid: The semaphore to remove.
//
int sem_delete(int semid);

//
// Increments a semaphore's value by 1.
//
// semid:   The semaphore to increment.
//
int sem_signal(int semid);

//
// Decrements a semaphore's value by 1.
//
// semid:   The semaphore to decrement.
//
int sem_wait(int semid);

#endif
