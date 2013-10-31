redset
======

|PyPI version| |build status| |Coverage Status|

Simple, generic sorted sets backed by Redis that can be used to
coordinate distributed systems.

Features
--------

-  Safe for multiple producers and consumers
-  Seamless use with Python objects using serializers
-  No worker daemons to run, no client processes to maintain
-  Simple, easy-to-read implementation
-  Mimics Python's native set interface
-  99% test coverage

Simple example
--------------

.. code:: python

    import json
    import redis

    from redset import TimeSortedSet

    r = redis.Redis()
    ss = TimeSortedSet(r, 'important_json_biz', serializer=json)

    ss.add({'foo': 'bar1'})
    ss.add({'foo': 'bar2'})
     
    ss.add({'foo': 'bar3'})
    ss.add({'foo': 'bar3'})

    len(ss)
    # 3


    # ...some other process A

    ss.peek()
    # {'foo': 'bar1'}

    ss.pop()
    # {'foo': 'bar1'}


    # ...meanwhile in process B (at exactly same time as A's pop)

    ss.take(2)
    # [{'foo': 'bar2'}, {'foo': 'bar3'}]

Docs
----

`Here <http://redset.readthedocs.org/en/latest/>`__

About
-----

This software was developed at `Percolate <https://percolate.com>`__,
where we use it for all sorts of things that involve maintaining
synchronized sets of things across process boundaries. A common use-case
is to use redset for coordinating time-sensitive tasks where duplicate
requests may be generated.

Redset is unopinionated about how consumers look or behave. Want to have
a plain 'ol Python consumer managed by supervisor? Fine. Want to be able
to pop off items from within a celery job? Great. Redset has no say in
where or how it is used: mechanism, not policy.

Usage concepts
--------------

``redset.SortedSet`` and its subclasses can be instantiated with a few
paramters that are notable.

Specifying a serializer
~~~~~~~~~~~~~~~~~~~~~~~

Since Redis only stores primitive numbers and strings, handling
serialization and deserialization is a key part of making redset set
usage simple in Python.

A ``serializer`` instance can be passed (which adheres to the
``redset.interfaces.Serializer`` interface, though it need not subclass
it) to automatically handle packing and unpacking items managed with
redset.

Specifying a scorer
~~~~~~~~~~~~~~~~~~~

A callable that specifies how to generate a score for items being added
can also be passed to SortedSet's constructor as ``scorer``. This
callable takes one argument, which is the item *object* (i.e. the item
before serialization) to be "scored."

Related projects
----------------

-  `redis-py <https://github.com/andymccurdy/redis-py>`__
-  `celery <https://github.com/celery/celery>`__
-  `RQ <http://python-rq.org/>`__

.. |PyPI version| image:: https://badge.fury.io/py/redset.png
   :target: http://badge.fury.io/py/redset
.. |build status| image:: https://travis-ci.org/percolate/redset.png?branch=master
   :target: https://travis-ci.org/percolate/redset
.. |Coverage Status| image:: https://coveralls.io/repos/percolate/redset/badge.png?branch=master
   :target: https://coveralls.io/r/percolate/redset?branch=master
