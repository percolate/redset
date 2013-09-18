"""
Locks used to synchronize mutations on queues.

"""

import time

from redset.exceptions import LockTimeout

__all__ = (
    'Lock',
)


class Lock(object):
    """
    Context manager that implements a distributed lock with redis.

    Based on Chris Lamb's version
    (https://chris-lamb.co.uk/posts/distributing-locking-python-and-redis)

    """
    def __init__(self, redis, key, expires=20, timeout=10):
        """
        Distributed locking using Redis SETNX and GETSET.

        Usage::

            with Lock('my_lock'):
                print "Critical section"

        :param  expires     We consider any existing lock older than
                            ``expires`` seconds to be invalid in order to
                            detect crashed clients. This value must be higher
                            than it takes the critical section to execute.
        :param  timeout     If another client has already obtained the lock,
                            sleep for a maximum of ``timeout`` seconds before
                            giving up. A value of 0 means we never wait.
        """
        self.redis = redis
        self.key = key
        self.timeout = timeout
        self.expires = expires

    def __enter__(self):
        timeout = self.timeout
        poll_interval = 0.2

        while timeout >= 0:
            expires = time.time() + self.expires + 1

            if self.redis.setnx(self.key, expires):
                # We gained the lock; enter critical section
                return

            current_value = self.redis.get(self.key)

            # We found an expired lock and nobody raced us to replacing it
            has_expired = (
                current_value and
                float(current_value) < time.time() and
                self.redis.getset(self.key, expires) == current_value
            )
            if has_expired:
                return

            timeout -= poll_interval
            time.sleep(poll_interval)

        raise LockTimeout("Timeout while waiting for lock '%s'" % self.key)

    def __exit__(self, exc_type, exc_value, traceback):
        self.redis.delete(self.key)


