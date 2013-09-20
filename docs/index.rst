.. redset documentation master file, created by
   sphinx-quickstart on Thu Sep 19 21:34:43 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Redset: Redis-backed sorted sets for Python
===========================================

Introduction
------------

Redset offers simple objects that mimic Python's builtin set, but are backed by
Redis and safe to use concurrently across process boundaries. Time-sorted 
sets come included and are particularly interesting for use when 
time-sensitive and duplicate tasks are being generated from multiple sources.

Traditional queuing solutions in Python don't easily allow users to ensure that
messages are unique; this is especially important when you're generating a lot
of time-consumptive tasks that may have overlap. Redset can help with this,
among other things.

Redset doesn't mandate the use of any particular consumer process or client.
Production and consumption can happen easily from any piece of Python, making
usage flexible and lightweight.

Quick example 
-------------

::
        
    class JsonSerializer(object):
        load = json.loads
        dump = json.dumps


    r = redis.Redis()
    ss = TimeSortedSet(r, 'important_json_biz', serializer=JsonSerializer())

    ss.add({'foo': 'bar1'}, score=123)

    {'foo': 'bar1'} in ss
    # True

    ss.score({'foo': 'bar1'})
    # 123

    ss.pop()
    # {'foo': 'bar1'}


Redset is designed to be simple and pleasant to use. It was
written at `Percolate <http://percolate.com>`_ where it's used for all sorts of
things, especially storing sets of time-sensitive tasks.


Contents
--------

.. toctree::
   :maxdepth: 2

   examples
   api


Authors
-------

Written by `jamesob <mailto:jamesob@percolate.com>`_ and 
`thekantian <mailto:zach@percolate.com>`_.

