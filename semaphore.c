#include "semaphore.h"

#include <errno.h>
#include <stdio.h>
#include <sys/ipc.h>
#include <sys/sem.h>

//
// Definition of union used by semctl() if on Linux.
//
// val:   Value for SETVAL
// buf:   Buffer for IPC_STAT, IPC_SET
// array: Array for GETALL, SETALL
// _buf: Buffer for IPC_INFO (Linux-specific)
//
#ifdef LAME
union semun {
    int val;
    struct semid_ds *buf;
    unsigned short *array;
    struct seminfo *_buf;
};
#endif

//
// Returns the identifier of one initialized semaphore.
//
int sem_create(void) {
    int semid = semget(IPC_PRIVATE, 1, 0600);
    if (semid < 0) {
        perror("sem_create:semget");
        return -1;
    }

    union semun arg = { .val = 1 };
    if (semctl(semid, 0, SETVAL, arg) < 0) {
        perror("sem_create:semctl");
        return -1;
    }

    return semid;
}

//
// Removes the specified semaphore set from the system.
//
// semid: The semaphore to remove.
//
int sem_delete(int semid) {
    union semun arg = { .val = 0 };
    return semctl(semid, 0, IPC_RMID, arg);
}

//
// Increments a semaphore's value by 1.
//
// semid:   The semaphore to increment.
//
int sem_signal(int semid) {
    struct sembuf sops = { 0, 1, SEM_UNDO };
    return semop(semid, &sops, 1);
}

//
// Decrements a semaphore's value by 1.
//
// semid:   The semaphore to decrement.
//
int sem_wait(int semid) {
    struct sembuf sops = { 0, -1, SEM_UNDO };
    return semop(semid, &sops, 1);
}
