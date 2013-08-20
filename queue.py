"""
This module holds a queue class that provides an interface to manage a sorted
set of string values sorted by timestamp in an Redis server. It is designed to
be readily usable, but also easily customizable for specific implementations.
"""

import time
from numbers import Number

import redis

import logging
log = logging.getLogger(__name__)

__all__ = ('Queue', )


class Queue(object):
    """
    This is a queue to manage a time-sorted redis queue using a sorted
    set (ZSET). UNIX timstamps are used as the score.
    """

    def __init__(self,
                 redis_client=None,
                 destructive_poll=True,
                 eligibility_timestamp=None,
                 eligibility_offset=None):
        """
        Kwargs:
            redis_client (Redis.Redis instance): an instance of the redis
                python client to use to communicate with a Redis server. The
                default confiuration will be used if none is supplied.
            destructive_poll (bool): should we remove the values from the queue
                when we call next_id?
            eligibility_timestamp (UNIX timestamp): an absolute time when
                values become eligible to be pulled off of the queue.
            eligibility_offset (int): an offset in seconds to add to
                time.time() which determines when an ID is eiligible to be
                pulled off of the queue.
        """
        self.destructive_poll = destructive_poll
        self.eligibility_timestamp = eligibility_timestamp
        self.eligibility_offset = eligibility_offset

        if not self.queue_key:
            raise ValueError('Need a Queue Key for Redis.')

        # TODO: Configure here?
        self.redis = redis_client or redis.Redis()

    @property
    def queue_key(self):
        """
        This is the string key that will be used in redis to store the ZSET.
        """
        return self.__class__.__name__

    def __iter__(self):
        """
        Implement the python iterator protocol on an instance of this class.
        """
        return self

    def next(self):
        """
        Implement the python iterator protocol for next. Returns an ID of the
        ZSET where the score is less than or equal to time.time().
        """
        next_id = self.next_id
        if next_id:
            return next_id
        else:
            raise StopIteration

    def flush(self):
        """
        Empty the queue of all scores and ID strings.

        NB: Logging at INFO level.
        """
        log.info('About to flush queue: %s' % self.queue_key)
        return self.redis.delete(self.queue_key)

    def remove(self, queue_id):
        """
        Remove a given ID from the queue.
        """
        return self.redis.zrem(self.queue_key, queue_id)

    def enqueue(self, queue_id, check_time=None):
        """
        Add the ID to the queue. Delegates to update_queue_time.
        """
        return self.update_queue_time(queue_id, check_time)

    def update_queue_time(self, queue_id, check_time=None):
        """
        Update the time that a given ID will be next checked in the queue.

        Args:
            queue_id (string or Number): the value that you want to be returned
                when you call queue.next_id.

        Kwargs:
            check-time (timestamp int): the time to check next. defaults to now
                if None is passed.
        """
        check_time = check_time or time.time()
        log.debug('Adding ID (%s) to queue %s with time: %s.' %
                 (queue_id, self.queue_key, check_time))
        self.redis.zadd(self.queue_key, queue_id, check_time)
        return check_time

    def check_time_for_id(self, queue_id):
        """
        See what time an ID is next queued to be checked.

        Returns None if the ID is not in the queue.
        """
        return self.redis.zscore(self.queue_key, queue_id)

    @property
    def eligible_at(self):
        """
        At what time do IDs in the queue become eligible for retrieval?
        """
        if not isinstance(self.eligibility_timestamp, Number):
                raise ValueError("eligibility_offset must be a valid "
                                 "timestamp.")

        _time = self.eligibility_timestamp or time.time()

        if self.eligibility_offset:
            if not isinstance(self.eligibility_offset, Number):
                raise ValueError("eligibility_offset must be a Number.")

            _time = _time + self.eligibility_offset

        return _time

    @property
    def next_id(self):
        """
        Get the next id in the queue.

        Returns None if there is nothing in the queue.

        If destructive_poll was set to True at initilization time, this will
        remove the ID from the queue once the consumer retrieves it.
        """
        results = self.redis.zrangebyscore(self.queue_key,
                                           min=0,
                                           max=self.eligible_at,
                                           start=0,
                                           num=1)

        if not results:
            log.debug('No next_id for queue %s' % self.queue_key)
        else:
            _id = results[0]

            if self.destructive_poll:
                self.remove(_id)

            return _id

    @property
    def oldest_time(self):
        """
        What is the oldest time in the queue? This is interesting if you are
        trying to keep your queue at real-time consumption.
        """
        results = self.redis.zrangebyscore(self.queue_key,
                                           min=0,
                                           max=self.eligible_at,
                                           start=0,
                                           num=1,
                                           withscores=True)

        timestamp = None
        if len(results) > 0:
            (_id, timestamp) = results[0]

        return timestamp

    @property
    def length(self):
        """
        How many values are the in the queue?

        Returns a Number.
        """
        return self.redis.zcard(self.queue_key)
