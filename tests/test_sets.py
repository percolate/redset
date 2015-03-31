
import unittest
import time
import json
import redis

from redset import SortedSet, TimeSortedSet, ScheduledSet
from redset.interfaces import Serializer


class SortedSetTest(unittest.TestCase):

    def setUp(self):
        self.key = 'ss_test'
        self.ss = SortedSet(redis.Redis(), self.key)

    def tearDown(self):
        self.ss.clear()

    def test_repr(self):
        """Just make sure it doesn't blow up."""
        str(self.ss)

    def test_length(self):
        for i in range(5):
            self.ss.add(i)

        self.assertEquals(
            len(self.ss),
            5,
        )

    def test_add_with_score(self):
        item = 'samere'
        score = 123
        self.ss.add(item, score)

        assert self.ss.score(item) == score

    def test_and_and_update_score(self):
        item = 'samere'
        score = 123
        self.ss.add(item, score)

        new_score = 456
        self.ss.add(item, new_score)

        assert self.ss.score(item) == new_score

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

    def test_empty_pop(self):
        with self.assertRaises(KeyError):
            self.ss.pop()

    def test_empty_peek(self):
        with self.assertRaises(KeyError):
            self.ss.peek()

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
            int(self.ss.score(0)),
            int(dup_added_at),
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
        with self.assertRaises(KeyError):
            self.ss.peek()

        self.ss.add(0)

        for __ in range(2):
            self.assertEquals(
                self.ss.peek(),
                '0',
            )

        with self.assertRaises(KeyError):
            self.ss.peek(position=1)

        self.ss.add(1)

        for __ in range(2):
            self.assertEquals(
                self.ss.peek(position=1),
                '1',
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

        self.assertEquals(
            self.ss.take(0),
            [],
        )

        self.assertEquals(
            self.ss.take(-1),
            [],
        )


class SerializerTest(unittest.TestCase):

    class FakeJsonSerializer(Serializer):
        """
        Handles JSON serialization.

        """
        def dumps(self, item):
            return json.dumps(item)

        def loads(self, item):
            if 'uhoh' in item:
                raise Exception("omg unserializing failed!")
            return json.loads(item)

    def setUp(self):
        self.key = 'json_ss_test'
        self.ss = SortedSet(
            redis.Redis(),
            self.key,
            serializer=self.FakeJsonSerializer(),
        )

        # has a bad serializer
        self.ss2 = SortedSet(
            redis.Redis(),
            self.key + '2',
            serializer=object(),
        )

    def tearDown(self):
        self.ss.clear()
        self.ss2.clear()

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
             {'yo': 'hey'}],
        )

    def test_bad_serializer(self):
        self.ss2.add(1, score=0)
        self.ss2.add(2, score=1)

        assert '2' in self.ss2

        # gets deserialied as a str, not an int
        self.assertEquals(
            '1',
            self.ss2.pop(),
        )


class ScorerTest(unittest.TestCase):

    def setUp(self):
        self.key = 'scorer_ss_test'

        class Ser(Serializer):
            loads = int
            dumps = str

        self.ss = SortedSet(
            redis.Redis(),
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

        self.tss = TimeSortedSet(redis.Redis(), self.key)

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
            int(self.tss.score(0)),
            int(dup_added_at),
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
        with self.assertRaises(KeyError):
            self.tss.peek()

        self.tss.add(0)

        for __ in range(2):
            self.assertEquals(
                self.tss.peek(),
                '0',
            )

        with self.assertRaises(KeyError):
            self.tss.peek(position=1)

        self.tss.add(1)

        for __ in range(2):
            self.assertEquals(
                self.tss.peek(position=1),
                '1',
            )

    def test_score(self):
        self.assertEquals(
            None,
            self.tss.score(0),
        )

        self.tss.add(0, self.now)

        self.assertEquals(
            int(self.now),
            int(self.tss.score(0)),
        )

    def test_oldest_time(self):
        self.assertEquals(
            None,
            self.tss.peek_score(),
        )

        for i in range(3):
            self.tss.add(i, self.now - i)

        self.assertEquals(
            int(self.now - 2),
            int(self.tss.peek_score()),
        )

        self.tss.pop()

        self.assertEquals(
            int(self.now - 1),
            int(self.tss.peek_score()),
        )


class ScheduledSetTest(unittest.TestCase):

    def setUp(self):
        self.key = 'scheduled_set_test'
        self.now = time.time() - 1  # offset to avoid having to sleep

        self.ss = ScheduledSet(redis.Redis(), self.key)

    def tearDown(self):
        self.ss.clear()

    def test_schedule(self):
        self.ss.add(1, self.now)
        self.ss.add(2, self.now + 1000)

        next_item = self.ss.pop()
        self.assertEquals(next_item, '1')

        with self.assertRaises(KeyError):
            self.ss.pop()

        self.assertEquals(len(self.ss), 1)

    def test_peek(self):
        with self.assertRaises(KeyError):
            self.ss.peek()

        self.ss.add(1, self.now - 1000)
        self.ss.add(2, self.now)
        self.ss.add(3, self.now + 1000)

        self.assertEquals(
            self.ss.peek(),
            '1',
        )

        self.assertEquals(
            self.ss.peek(position=1),
            '2',
        )

        with self.assertRaises(KeyError):
            self.ss.peek(position=2)

        self.ss.pop()
        self.ss.pop()

        with self.assertRaises(KeyError):
            self.ss.peek()

        self.assertEquals(len(self.ss), 1)

    def test_take(self):
        self.ss.add('1', self.now - 3)
        self.ss.add('2', self.now - 2)
        self.ss.add('3', self.now - 1)

        items = self.ss.take(2)
        self.assertEquals(len(items), 2)
        self.assertEquals(['1', '2'], items)

        self.assertEquals(self.ss.pop(), '3')

        self.assertEquals(
            len(self.ss),
            0,
        )

        self.assertEquals(
            self.ss.take(0),
            [],
        )

        self.assertEquals(
            self.ss.take(-1),
            [],
        )

    def test_length(self):
        for i in range(2):
            self.ss.add(i, self.now + 50)

        for i in range(3):
            self.ss.add(i + 2, self.now - 50)

        self.assertEquals(
            len(self.ss),
            5,
        )

    def test_length_available(self):
        for i in range(2):
            self.ss.add(i, self.now + 50)

        for i in range(3):
            self.ss.add(i + 2, self.now - 50)

        self.assertEquals(
            self.ss.available(),
            3,
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
            int(self.ss.score(0)),
            int(dup_added_at),
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
        self.ss.add(1, self.now + 50)

        self.assertTrue(self.ss.discard(0))
        self.assertFalse(self.ss.discard(0))

        self.assertTrue(self.ss.discard(1))
        self.assertFalse(self.ss.discard(1))

    def test_peek_score(self):
        self.assertEquals(
            None,
            self.ss.peek_score(),
        )

        for i in range(3):
            self.ss.add(i, self.now - i)

        self.assertEquals(
            int(self.now - 2),
            int(self.ss.peek_score()),
        )

        self.ss.pop()

        self.assertEquals(
            int(self.now - 1),
            int(self.ss.peek_score()),
        )
