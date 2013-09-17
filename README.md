redset
=========

`redset`: Simple, generic sorted sets backed by Redis that can be used to 
coordinate distributed systems.

## Features

- Safe for multiple producers and consumers
- Seamless use with Python objects using serializers
- No worker daemons to run, no client processes to maintain
- Simple, easy-to-read implementation
- Mimics Python's native set interface
- Well tested

## About

This software was developed at [Percolate](https://percolate.com), where we use
it for all sorts of things that involve maintaining synchronized sets of things
across process boundaries. A common use-case is to use redset for coordinating 
time-sensitive tasks where duplicate requests may be generated.

Redset is unopinionated about how consumers look or behave. Want to have a
plain 'ol Python consumer managed by supervisor? Fine. Want to be able to pop
off items from within a celery job? Great. Redset has no say in where or how it
is used: mechanism, not policy.

## Simple example

```python
import json
import redis

from redset import TimeSortedSet


class JsonSerializer(object):
    load = json.loads
    dump = json.dumps


r = redis.Redis()
ss = TimeSortedSet(r, 'important_json_biz', serializer=JsonSerializer())

ss.add({'foo': 'bar1'})
ss.add({'foo': 'bar2'})
ss.add({'foo': 'bar3'})

len(ss)
# 3


# ...some other process


ss.peek()
# {'foo': 'bar1'}

ss.pop()
# {'foo': 'bar1'}

ss.take(2)
# [{'foo': 'bar2'}, {'foo': 'bar3'}]
```
 
## Installing

Download this directory, and install it using pip with setup.py:

```
pip install .
```

## Related projects (sort of)

- [celery](https://github.com/celery/celery)
- [RQ](http://python-rq.org/)

