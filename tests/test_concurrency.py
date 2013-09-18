"""
Test the use of redset from multiple processeses.

"""

import unittest
import multiprocessing
import itertools

import redis
from redis.connection import ConnectionError

from redset import SortedSet

client = redis.Redis()


def _is_redis_available():
    try:
        client.set('foo', 1)
    except ConnectionError:
        return False
    else:
        client.delete('foo')

    return True


@unittest.skipIf(not _is_redis_available(), "Redis process isn't available")
class MultiprocessTest(unittest.TestCase):
    """
    Ensure that we can bang on the sorted set from multiple processes without
    trouble.

    """

    def setUp(self):
        self.r = redis.Redis()
        self.set_name = 'MultiprocessTest'
        self.ss = self._make_ss()
        self.ss.clear()

    def _make_ss(self):
        class Serializer(object):
            load = int
            dump = str

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
