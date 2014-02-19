"""
Locks used to synchronize mutations on queues.

"""

import time

from redset.exceptions import LockTimeout

__all__ = (
    'Lock',
)


# redis or redis-py truncates timestamps to the hundredth
REDIS_TIME_PRECISION = 0.01


class Lock(object):
    """
    Context manager that implements a distributed lock with redis.

    Based on Chris Lamb's version
    (https://chris-lamb.co.uk/posts/distributing-locking-python-and-redis)

    """
    def __init__(self,
                 redis,
                 key,
                 expires=None,
                 timeout=None,
                 poll_interval=None,
                 ):
        """
        Distributed locking using Redis SETNX and GETSET.

        Usage::

            with Lock('my_lock'):
                print "Critical section"

        :param redis: the redis client
        :param key: the key the lock is labeled with
        :param timeout: If another client has already obtained the lock,
            sleep for a maximum of ``timeout`` seconds before
            giving up. A value of 0 means we never wait. Defaults to 10.
        :param expires: We consider any existing lock older than
            ``expires`` seconds to be invalid in order to
            detect crashed clients. This value must be higher
            than it takes the critical section to execute. Defaults to 20.
        :param poll_interval: How often we should poll for lock acquisition.
            Note that poll intervals below 0.01 don't make sense since
            timestamps stored in redis are truncated to the hundredth.
            Defaults to 0.2.
        :raises: LockTimeout

        """
        self.redis = redis
        self.key = key
        self.timeout = timeout or 10
        self.expires = expires or 20
        self.poll_interval = poll_interval or 0.2

    def __enter__(self):
        timeout = self.timeout

        while timeout >= 0:
            expires = time.time() + self.expires

            if self.redis.setnx(self.key, expires):
                # We gained the lock; enter critical section
                return

            current_value = self.redis.get(self.key)

            # We found an expired lock and nobody raced us to replacing it
            has_expired = (
                current_value and
                # bump the retrieved time by redis' precision so that we don't
                # erroneously consider a recently acquired lock as expired
                (float(current_value) + REDIS_TIME_PRECISION) < time.time() and
                self.redis.getset(self.key, expires) == current_value
            )
            if has_expired:
                return

            timeout -= self.poll_interval
            time.sleep(self.poll_interval)

        raise LockTimeout("Timeout while waiting for lock '%s'" % self.key)

    def __exit__(self, exc_type, exc_value, traceback):
        self.redis.delete(self.key)
