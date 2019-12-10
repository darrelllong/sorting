#include <sys/sem.h>

//
// Returns the identifier of a set of semaphores based.
// The set of semaphores is generated using a key and the number of semaphores.
// The key can be generated using ftok() using a pathname.
//
// key:   The key to create a set of semaphores with.
// nsems: The number of semaphores to create (0 if a set isn't desired).
//
int sem_create(key_t key, int nsems) {
  return semget(key, nsems, 0666);
}

//
// Removes the specified semaphore set from the system.
//
// semid: The semaphore set to remove.
//
int sem_delete(int semid) {
  union semun arg = { 0 };
  return semctl(semid, 0, IPC_RMID, arg);
}

//
// Increments a semaphore value by 1.
//
// semid:   The semaphore set containing the semaphore to increment.
// semnum:  The semaphore number within the set to increment.
//
int sem_signal(int semid, int semnum) {
  struct sembuf sops = { semnum, 1, SEM_UNDO };
  return semop(semid, &sops, 1);
}

//
// Decrements a semaphore value by 1.
//
// semid:   The semaphore set containing the semaphore to decrement.
// semnum:  The semaphore number within the set to decrement.
//
int sem_wait(int semid, int semnum) {
  struct sembuf sops = { semnum, -1, SEM_UNDO };
  return semop(semid, &sops, 1);
}
