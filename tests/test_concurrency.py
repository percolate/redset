"""
Test the use of redset from multiple processeses.

"""

import unittest
import multiprocessing
import itertools

import redis

from redset import SortedSet, ScheduledSet
from redset.exceptions import LockTimeout

client = redis.Redis()


class MultiprocessTest(unittest.TestCase):
    """
    Ensure that we can bang on the sorted set from multiple processes without
    trouble.

    """

    def setUp(self):
        self.r = redis.Redis()
        self.set_name = 'MultiprocessTest'
        self.ss = self._make_ss()

    def _make_ss(self):
        class Serializer(object):
            loads = int
            dumps = str

        return SortedSet(
            redis.Redis(), self.set_name, serializer=Serializer(),
        )

    def tearDown(self):
        self.ss.clear()

    def test_multiprocessing(self):
        """
        Add a bunch of items to a sorted set; attempt to take simulataneously
        from multiple processes. Ensure that we end up taking all elements
        added without duplication.

        """
        num_procs = 10
        num_items = num_procs * 100

        # prime the sortedset with stuff
        for i in range(num_items):
            self.ss.add(i)

        # utility for running functions within TestCase using multiprocess
        def parmap(f, X):
            def spawn(f):
                def fun(pipe, x):
                    pipe.send(f(x))
                    pipe.close()
                return fun

            pipe = [multiprocessing.Pipe() for x in X]
            proc = [multiprocessing.Process(target=spawn(f), args=(c, x))
                    for x, (p, c) in itertools.izip(X, pipe)]
            [p.start() for p in proc]
            [p.join() for p in proc]
            return [p.recv() for (p, c) in pipe]

        def take_subset(process_num):
            ss = self._make_ss()
            return ss.take(num_items / num_procs)

        taken_items = list(itertools.chain.from_iterable(
            parmap(take_subset, range(num_procs))))

        # assert that no duplicates resulted from taking from the set
        # concurrently
        self.assertEquals(
            list(sorted(taken_items)),
            range(num_items),
        )

        self.assertEquals(
            0,
            len(self.ss),
        )


class ScheduledMultiprocessTest(unittest.TestCase):
    """
    ScheduledSet has slightly different concurrency semantics.

    """
    def _make_ss(self):
        class Serializer(object):
            loads = int
            dumps = str

        return ScheduledSet(
            redis.Redis(), self.set_name, serializer=Serializer(),
        )


class LockExpiryTest(unittest.TestCase):
    """
    Ensure that we can bang on the sorted set from multiple processes without
    trouble.

    """

    def setUp(self):
        self.r = redis.Redis()
        self.set_name = self.__class__.__name__
        self.timeout_length = 0.001
        self.holder = SortedSet(redis.Redis(), self.set_name, lock_expires=10)
        self.chump = SortedSet(
            redis.Redis(),
            self.set_name,
            lock_timeout=self.timeout_length,
            lock_expires=self.timeout_length,
        )

    def tearDown(self):
        self.holder.clear()
        self.chump.clear()

    def test_lock_timeout(self):
        """
        One process holds the lock while the other times out.

        """
        with self.holder.lock:
            with self.assertRaises(LockTimeout):
                with self.chump.lock:
                    assert False, "shouldn't be able to acquire the lock"

    def test_lock_expires(self):
        """
        One process holds the lock, times out, and the other scoopes the lock.

        """
        got_the_lock = False

        # chump's acquisition should timeout, get picked up by holder
        with self.chump.lock:
            with self.holder.lock:
                got_the_lock = True

        assert got_the_lock, "`holder` should have acquired the lock"
