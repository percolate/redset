
import time

from redset.interfaces import Serializer
from redset.locks import Lock

import logging
log = logging.getLogger(__name__)


__all__ = (
    'SortedSet',
    'TimeSortedSet',
    'ScheduledSet',
)


class SortedSet(object):
    """
    A Redis-backed sorted set safe for multiprocess consumption.

    By default, items are stored and returned as str. Scores default to 0.

    A serializer can be specified to ease packing/unpacking of items.
    Otherwise, items are cast to and returned as strings.

    """
    def __init__(self,
                 redis_client,
                 name,
                 scorer=None,
                 serializer=None,
                 lock_timeout=None,
                 lock_expires=None,
                 ):
        """
        :param redis_client: an object matching the interface of the
            redis.Redis client. Used to communicate with a Redis server.
        :type redis_client: redis.Redis instance
        :param name: used to identify the storage location for this
            set.
        :type name: str
        :param scorer: takes in a single argument, which is
            the item to be stored, and returns a score which will be used
            for the item.
        :type scorer: Callable, arity 1
        :param serializer: must match the interface defined
            by `redset.interfaces.Serializer`.
            Defines how objects are marshalled into redis.
        :type serializer: :class:`interfaces.Serializer
            <interfaces.Serializer>`
        :param lock_timeout: maximum time we should wait on a lock in seconds.
            Defaults to value set in :class:`locks.Lock <locks.Lock>`
        :type lock_timeout: Number
        :param lock_expires: maximum time we should hold the lock in seconds
            Defaults to value set in :class:`locks.Lock <locks.Lock>`
        :type lock_expires: Number

        """
        self._name = name
        self.redis = redis_client
        self.scorer = scorer or _default_scorer
        self.serializer = serializer or _DefaultSerializer()
        self.lock = Lock(
            self.redis,
            '%s__lock' % self.name,
            expires=lock_expires,
            timeout=lock_timeout)

    def __repr__(self):
        return (
            "<%s name='%s', length=%s>" %
            (self.__class__.__name__, self.name, len(self))
        )

    __str__ = __repr__

    def __len__(self):
        """
        How many values are the in the set?

        :returns: int

        """
        return int(self.redis.zcard(self.name))

    def __contains__(self, item):
        return (self.score(item) is not None)

    @property
    def name(self):
        """
        The name of this set and the string that identifies the redis key
        where this set is stored.

        :returns: str

        """
        return self._name

    def add(self, item, score=None):
        """
        Add the item to the set. If the item is already in the set, update its
        score.

        :param item:
        :type item: str
        :param score: optionally specify the score for the item
            to be added.
        :type score: Number

        :returns: Number -- score the item was added with

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

        :raises: KeyError -- if no items left

        :returns: object.

        """
        item = self._pop_item()

        if not item:
            raise KeyError('%s is empty' % self)

        return item

    def take(self, num):
        """
        Atomically remove and return the next ``num`` items for processing in
        the set.

        Will return at most ``min(num, len(self))`` items. If certain items
        fail to deserialize, the falsey value returned will be filtered out.

        :returns: list of objects

        """
        num = int(num)

        if num < 1:
            return []

        return self._pop_items(num)

    def clear(self):
        """
        Empty the set of all scores and ID strings.

        :returns: bool

        """
        log.debug('Flushing set %s' % self.name)
        return self.redis.delete(self.name)

    def discard(self, item):
        """
        Remove a given item from the set.

        :param item:
        :type item: object
        :returns: bool -- success of removal

        """
        return self._discard_by_str(self._dump_item(item))

    def peek(self, position=0):
        """
        Return the an item without removing it.

        :param position:
        :type position: int
        :raises: KeyError -- if no items found at the specified position
        :returns: object

        """
        return self._load_item(self._peek_str(position))

    def score(self, item):
        """
        See what the score for an item is.

        :returns: Number or None.

        """
        return self.redis.zscore(self.name, self._dump_item(item))

    def peek_score(self):
        """
        What is the score of the next item to be processed? This is interesting
        if you are trying to keep your set at real-time consumption.

        :returns: Number

        """
        res = self._get_next_item(with_score=True)

        return res[0][1] if res else None

    def _peek_str(self, position=0):
        """
        Internal peek to allow peeking by str.

        """
        results = self._get_item(position)

        if not results:
            raise KeyError("%s is empty" % self.name)

        return results[0]

    def _pop_item(self):
        """
        Internal method for returning the next item without locking.

        """
        res_list = self._pop_items(1)
        return res_list[0] if res_list else None

    def _pop_items(self, num_items):
        """
        Internal method for poping items atomically from redis.

        :returns: [loaded_item, ...]. if we can't deserialize a particular
            item, just skip it.

        """
        res = []

        item_strs = self._get_and_remove_items(num_items)

        for item_str in item_strs:
            item_str = _py3_compat_decode(item_str)
            try:
                res.append(self._load_item(item_str))
            except Exception:
                log.exception("Could not deserialize '%s'" % res)

        return res

    def _get_and_remove_items(self, num_items):
        """
        get and remove items from the redis store.

        :returns: [str, ...]

        """
        pipe = self.redis.pipeline()

        (pipe
         .zrange(
             self.name,
             0,
             num_items - 1,
             withscores=False)
         .zremrangebyrank(
             self.name,
             0,
             num_items - 1)
         )

        return pipe.execute()[0]

    def _discard_by_str(self, *item_strs):
        """
        Internal discard to allow discarding by the str representation of
        an item.

        """
        pipe = self.redis.pipeline()

        for item in item_strs:
            pipe.zrem(self.name, item)

        return all(pipe.execute())

    def _get_item(self, position, with_score=False):
        """
        Returns a specific element from the redis store

        :param position:
        :type position: int
        :returns: [str] or [str, float]. item optionally with score, without
            removing it.
        """
        return self.redis.zrange(
            self.name,
            position,
            position,
            withscores=with_score,
        )

    def _get_next_item(self, with_score=False):
        """
        :returns: [str] or [str, float]. item optionally with score, without
            removing it.

        """
        return self._get_item(0, with_score)

    def _load_item(self, item):
        """
        Conditionally deserialize if a routine was specified.

        """
        try:
            self.serializer.loads
        except AttributeError:
            return _py3_compat_decode(item)

        return self.serializer.loads(item)

    def _dump_item(self, item):
        """
        Conditionally serialize if a routine was specified.

        """
        try:
            self.serializer.dumps
        except AttributeError:
            return item

        return self.serializer.dumps(item)


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


class ScheduledSet(TimeSortedSet):
    """
    A distributed, FIFO-by-default, time-sorted set that's safe for
    multiprocess consumption. Supports scheduling item consumption for the
    future.

    Implemented in terms of a redis ZSET where UNIX timestamps are used as
    the score.

    A ScheduledSet will only return results with a score less than
    time.time() - to enable you to schedule jobs for the future and let redis
    do the work of defering them until they are ready for consumption.

    """
    def _get_and_remove_items(self, num_items):
        with self.lock:
            item_strs = self.redis.zrangebyscore(
                self.name,
                '-inf',
                time.time(),
                start=0,
                num=num_items,
                withscores=False
            )

            if item_strs:
                self._discard_by_str(*item_strs)

        return item_strs

    def _get_item(self, position=0, with_score=False):
        return self.redis.zrangebyscore(
            self.name,
            '-inf',
            time.time(),
            # start/num combination is effectively a limit=1
            start=position,
            num=position+1,
            withscores=with_score,
        )

    def _get_next_item(self, with_score=False):
        return self._get_item(with_score=with_score)

    def available(self):
        """
        The count of items with a score less than now.

        """
        return self.redis.zcount(self.name, '-inf', time.time())


class _DefaultSerializer(Serializer):

    loads = lambda self, i: _py3_compat_decode(i)
    dumps = lambda self, i: i


_default_scorer = lambda i: 0


def _py3_compat_decode(item_out_of_redis):
    """Py3 redis returns bytes, so we must handle the decode."""
    if not isinstance(item_out_of_redis, str):
        return item_out_of_redis.decode('utf-8')
    return item_out_of_redis
