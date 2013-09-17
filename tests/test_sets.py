
import unittest
import time
import json

import mockredis

from redset import SortedSet, TimeSortedSet
from redset.interfaces import Serializer
from redset.exceptions import EmptyException


class SortedSetTest(unittest.TestCase):

    def setUp(self):
        self.key = 'ss_test'
        r = mockredis.mock_redis_client()

        self.ss = SortedSet(r, self.key)

    def tearDown(self):
        self.ss.clear()

    def test_length(self):
        for i in range(5):
            self.ss.add(i)

        self.assertEquals(
            len(self.ss),
            5,
        )

    def test_contains(self):
        for i in range(5):
            self.ss.add(i)

        self.assertTrue(
           0 in self.ss
        )

        self.assertFalse(
            -1 in self.ss
        )

    def test_ordering(self):
        for i in range(5):
            self.ss.add(i, score=i)

        self.assertEquals(
            [str(i) for i in range(5)],
            [self.ss.pop() for __ in range(5)],
        )

    def test_add_dup(self):
        for i in range(5):
            self.ss.add(i)

        dup_added_at = 10
        self.ss.add(0, score=dup_added_at)

        self.assertEquals(
            len(self.ss),
            5,
        )

        self.assertEquals(
            self.ss.score(0),
            dup_added_at,
        )

    def test_clear(self):
        self.assertFalse(self.ss.clear())

        for i in range(5):
            self.ss.add(i)

        self.assertTrue(self.ss.clear())
        self.assertEquals(
            len(self.ss),
            0,
        )

    def test_discard(self):
        self.ss.add(0)

        self.assertTrue(self.ss.discard(0))
        self.assertFalse(self.ss.discard(0))

    def test_peek(self):
        with self.assertRaises(EmptyException):
            self.ss.peek()

        self.ss.add(0)

        for __ in range(2):
            self.assertEquals(
                self.ss.peek(),
                '0',
            )

    def test_take(self):
        for i in range(5):
            self.ss.add(i)

        self.assertEquals(
            set([str(i) for i in range(2)]),
            set(self.ss.take(2)),
        )

        self.assertEquals(
            set([str(i + 2) for i in range(3)]),
            set(self.ss.take(100)),
        )

        self.assertEquals(
            len(self.ss),
            0,
        )


class SerializerTest(unittest.TestCase):

    class FakeJsonSerializer(Serializer):
        """
        Handles JSON serialization.

        """
        def dump(self, item):
            return json.dumps(item)

        def load(self, item):
            print item
            if 'uhoh' in item:
                raise Exception("omg unserializing failed!")
            return json.loads(item)

    def setUp(self):
        self.key = 'json_ss_test'
        r = mockredis.mock_redis_client()

        self.ss = SortedSet(r, self.key, serializer=self.FakeJsonSerializer())

    def tearDown(self):
        self.ss.clear()

    def test_add_and_pop(self):
        self.ss.add({'yo': 'json'}, score=1)
        self.ss.add({'yo': 'yaml'}, score=0)

        self.assertTrue(
            {'yo': 'json'} in self.ss
        )

        self.assertEqual(
            self.ss.pop(),
            {'yo': 'yaml'},
        )

        self.assertEqual(
            self.ss.pop(),
            {'yo': 'json'},
        )

        self.assertEqual(
            0,
            len(self.ss),
        )

    def test_cant_deserialize(self):
        self.ss.add({'yo': 'foo'}, score=0)
        self.ss.add({'yo': 'uhoh!'}, score=1)
        self.ss.add({'yo': 'hey'}, score=2)

        self.assertEquals(
            self.ss.take(3),
            [{'yo': 'foo'},
             None,
             {'yo': 'hey'}],
        )


class ScorerTest(unittest.TestCase):

    def setUp(self):
        self.key = 'scorer_ss_test'
        r = mockredis.mock_redis_client()

        class Ser(Serializer):
            load = int
            dump = str

        self.ss = SortedSet(
            r,
            self.key,
            scorer=lambda i: i * -1,
            serializer=Ser(),
        )

    def tearDown(self):
        self.ss.clear()

    def test_scorer(self):
        for i in range(5):
            self.ss.add(i)

        self.assertEqual(
            [4, 3, 2, 1, 0],
            self.ss.take(5),
        )


class TimeSortedSetTest(unittest.TestCase):

    def setUp(self):
        self.key = 'tss_test'
        self.now = time.time()
        r = mockredis.mock_redis_client()

        self.tss = TimeSortedSet(r, self.key)

    def tearDown(self):
        self.tss.clear()

    def test_length(self):
        for i in range(5):
            self.tss.add(i)

        self.assertEquals(
            len(self.tss),
            5,
        )

    def test_contains(self):
        for i in range(5):
            self.tss.add(i)

        self.assertTrue(
           0 in self.tss
        )

        self.assertFalse(
            -1 in self.tss
        )

    def test_add_at(self):
        for i in range(5):
            self.tss.add(i, score=(self.now - i))

        self.assertEquals(
            [str(i) for i in reversed(range(5))],
            [self.tss.pop() for __ in range(5)],
        )

    def test_add_dup(self):
        for i in range(5):
            self.tss.add(i)

        dup_added_at = self.now + 10
        self.tss.add(0, score=dup_added_at)

        self.assertEquals(
            len(self.tss),
            5,
        )

        self.assertEquals(
            self.tss.score(0),
            dup_added_at,
        )

    def test_clear(self):
        self.assertFalse(self.tss.clear())

        for i in range(5):
            self.tss.add(i)

        self.assertTrue(self.tss.clear())
        self.assertEquals(
            len(self.tss),
            0,
        )

    def test_discard(self):
        self.tss.add(0)

        self.assertTrue(self.tss.discard(0))
        self.assertFalse(self.tss.discard(0))

    def test_peek(self):
        with self.assertRaises(EmptyException):
            self.tss.peek()

        self.tss.add(0)

        for __ in range(2):
            self.assertEquals(
                self.tss.peek(),
                '0',
            )

    def test_score(self):
        self.assertEquals(
            None,
            self.tss.score(0),
        )

        self.tss.add(0, self.now)

        self.assertEquals(
            self.now,
            self.tss.score(0),
        )

    def test_oldest_time(self):
        self.assertEquals(
            None,
            self.tss.peek_score(),
        )

        for i in range(3):
            self.tss.add(i, self.now - i)

        self.assertEquals(
            self.now - 2,
            self.tss.peek_score(),
        )

        self.tss.pop()

        self.assertEquals(
            self.now - 1,
            self.tss.peek_score(),
        )


