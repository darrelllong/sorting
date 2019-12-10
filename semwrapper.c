#include <errno.h>
#include <stdio.h>
#include <sys/ipc.h>
#include <sys/sem.h>

//
// Returns the identifier of one initialized semaphore.
// The semaphore is generated using a key.
// The key can be generated using ftok() using a pathname.
//
// key:   The key to create a set of semaphores with.
//
int sem_create(key_t key) {
  int semid = semget(key, 1, 0600);
  if (semid < 0) {
    perror("sem_create:semget");
    return -1;
  }

  union semun arg = { 1 };
  if (semctl(semid, 0, SETVAL, arg) < 0) {
    perror("semcreate:semctl");
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
  union semun arg = { 0 };
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
