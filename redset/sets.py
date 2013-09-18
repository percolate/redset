
import time

from redset.interfaces import Serializer
from redset.locks import Lock

import logging
log = logging.getLogger(__name__)


__all__ = (
    'SortedSet',
    'TimeSortedSet',
)


class SortedSet(object):
    """
    A Redis-backed sorted set safe for multiprocess consumption.

    By default, items are stored and returned as `str`s. Scores default to 0.

    A serializer can be specified to ease packing/unpacking of items.
    Otherwise, items are cast to and returned as strings.

    """
    def __init__(self,
                 redis_client,
                 name,
                 scorer=None,
                 serializer=None,
                 ):
        """
        Args:
            redis_client (Redis.Redis instance): an instance of the redis
                python client to use to communicate with a Redis server.
            name (str): used to identify the storage location for this set.

        Kwargs:
            scorer (Callable, arity 1): takes in a single argument, which is
                the item to be stored, and returns a score which will be used
                for the item.
            serializer (Serializer instance): must match the interface defined
                by `redset.interfaces.Serializer`. Defines how objects are
                marshalled into redis.

        """
        if not isinstance(name, (str, unicode)):
            raise ValueError("name must be a str")

        self._name = name
        self.redis = redis_client
        self.scorer = scorer or _default_scorer
        self.serializer = serializer or _DefaultSerializer()
        self.lock = Lock(self.redis, '%s__lock' % self.name)

    def __repr__(self):
        return (
            "<%s name='%s', length=%s>" %
            (self.__class__.__name__, self.name, len(self))
        )

    __str__ = __repr__

    def __len__(self):
        """
        How many values are the in the set?

        Returns:
            int.

        """
        return int(self.redis.zcard(self.name))

    def __contains__(self, item):
        return (self.score(item) is not None)

    @property
    def name(self):
        """
        The name of this set and the string that identifies the redis key
        where this set is stored.

        Returns:
            str.

        """
        return self._name

    def add(self, item, score=None):
        """
        Add the item to the set. It the item is already in the set, update
        its score.

        Args:
            item (str)

        Kwargs:
            score (float): optionally specify the score for the item
                to be added.

        Returns:
            float. score the item was added with

        """
        score = score or self.scorer(item)

        log.debug(
            'Adding %s to set %s with score: %s' % (item, self.name, score)
        )
        self.redis.zadd(self.name, self._dump_item(item), score)

        return score

    def pop(self):
        """
        Atomically remove and return the next item eligible for processing in
        the set.

        If, for some reason, deserializing the object fails, None is returned
        and the object is deleted from redis.

        Raises:
            KeyError -- if no items left

        Returns:
            object.

        """
        with self.lock:
            res = self._pop_item()

        return res

    def take(self, num):
        """
        Atomically remove and return the next `num` items for processing in the
        set.

        Will return `min(num, len(self))` items.

        Returns:
            list of objects.

        """
        with self.lock:
            items = [self._pop_item() for __ in range(min(num, len(self)))]

        return items

    def clear(self):
        """
        Empty the set of all scores and ID strings.

        Returns:
            bool.

        """
        log.debug('Flushing set %s' % self.name)

        with self.lock:
            result = self.redis.delete(self.name)

        return result

    def discard(self, item):
        """
        Remove a given item from the set.

        Args:
            item (object)

        Returns:
            bool. success of removal

        """
        return self._discard_by_str(self._dump_item(item))

    def peek(self):
        """
        Return the next item eligible for processing without removing it.

        Raises:
            KeyError -- if no items left

        Returns:
            str.

        """
        return self._load_item(self._peek_str())

    def score(self, item):
        """
        See what the score for an item is.

        Returns:
            Number or None.

        """
        return self.redis.zscore(self.name, self._dump_item(item))

    def peek_score(self):
        """
        What is the score of the next item to be processed? This is interesting
        if you are trying to keep your set at real-time consumption.

        Returns:
            type(serializer.load).

        """
        res = self._get_next_item(with_score=True)

        return res[0][1] if res else None

    def _peek_str(self):
        """
        Internal peek to allow peeking by str.

        """
        results = self._get_next_item()

        if not results:
            raise KeyError("%s is empty" % self.name)

        with open('foo.txt', 'a') as f:
            f.write(str(results) + '\n')
        return results[0]

    def _pop_item(self):
        """
        Internal method for returning the next item without locking.

        """
        res = None
        item_str = self._peek_str()

        try:
            res = self._load_item(item_str)
        except Exception:
            log.exception("Could not deserialize '%s'" % res)
        finally:
            self._discard_by_str(item_str)

        return res

    def _discard_by_str(self, item_str):
        """
        Internal discard to allow discarding by the str representation of
        an item.

        """
        return self.redis.zrem(self.name, item_str)

    def _get_next_item(self, with_score=False):
        """
        Returns:
            [str] or [str, float]. item optionally with score

        """
        return self.redis.zrangebyscore(
            self.name,
            '-inf',
            '+inf',
            start=0,
            num=1,
            withscores=with_score,
        )

    def _load_item(self, item):
        """
        Conditionally deserialize if a routine was specified.

        """
        try:
            self.serializer.load
        except AttributeError:
            return item

        return self.serializer.load(item)

    def _dump_item(self, item):
        """
        Conditionally serialize if a routine was specified.

        """
        try:
            self.serializer.dump
        except AttributeError:
            return item

        return self.serializer.dump(item)


class TimeSortedSet(SortedSet):
    """
    A distributed, FIFO-by-default, time-sorted set that's safe for
    multiprocess consumption.

    Implemented in terms of a redis ZSET where UNIX timestamps are used as
    the score.

    """
    def __init__(self, *args, **kwargs):
        """
        See `redset.sets.SortedSet`. Default scorer will return the current
        time when an item is added.

        """
        if not kwargs.get('scorer'):
            kwargs['scorer'] = lambda i: time.time()

        super(TimeSortedSet, self).__init__(*args, **kwargs)


class _DefaultSerializer(Serializer):

    def load(self, str_from_redis):
        return str_from_redis

    def dump(self, obj):
        return obj


_default_scorer = lambda i: 0

