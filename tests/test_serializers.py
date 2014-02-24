
import unittest
import redis
from collections import namedtuple

from redset import SortedSet
from redset.serializers import NamedtupleSerializer


DiscoTask = namedtuple('DiscoTask', 'tiger,woods')


class TestNTSerializer(unittest.TestCase):

    def setUp(self):
        self.ss = SortedSet(
            redis.Redis(),
            self.__class__.__name__,
            serializer=NamedtupleSerializer(DiscoTask),
        )

    def tearDown(self):
        self.ss.clear()

    def test_nt_serializer(self):
        dt = DiscoTask(tiger='larry', woods='david')

        self.ss.add(dt)

        assert len(self.ss) == 1
        assert dt in self.ss

        self.assertEqual(
            dt,
            self.ss.pop(),
        )
