quedis
=========

`quedis`: A simple way to get use Redis sorted sets as task queues.

quedis does not do anything except for queue IDs sorted by time. There is no worker daemon to run, or any client process to maintain. It is not designed to compete with projects like celery, instead this is for workflows where two properties are interesting:

- 1) The queue is a set where each unique ID can only be queued once.
- 2) The queue is time-sensitive.

The queues are sorted using a UNIX timstamp, where using the queue as an iterable returns a stream of values where the timestamp is greater than or equal to a value (by default it is time.time()). The Queue class contained within quedis is designed to be a small part of a larger system, where you will build something to both produce and consume IDs. Many distributed systems can use the techniques that we designed quedis to help us with.

This software was developed at [Percolate](https://percolate.com), where we use it for all sorts of things where our RabbitMQ server doesn't fit the bill due to the 2 properties above being useful to us.

## Installing

download this directory, and install it using pip with setup.py:

```
pip install .
```

## Features

- Easy Monitoring, by checking the age of the timestamps in the queue. If you
  are interested in consuming a queue in real-time, you can monitor the delay
  as fast as redis can respond to your query (FAST!!).
- Easy customization: you can configure all the important behavior.

## Related projects

- [celery](https://github.com/celery/celery)
- [RQ](http://python-rq.org/)

## Example

```python
>>> import quedis
# assumes a Redis server running on 127.0.0.1:6379
>>> queue = quedis.Queue()
>>> queue.enqueue(123)

>>> for _id in queue:
>>>    print _id
    123
```

You should implement some interesting features in your code to do something with the ID.

```python
# if we want to check the ID again
>>> queue.enqueue(123)
# if we don't
>>> import this
```
