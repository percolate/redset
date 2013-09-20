
.. _api:

API
===

.. module:: redset
 
Introduction
------------

Redset offers a narrow interface consisting of a few objects. Most often,
you'll be using an object that resembles a set.

There are two interesting components to the sets in redset: *scorers* and
*serializers*.

Scorers determine what score the inserted item will be assigned (lower means
popped sooner). Serializers determine what transformations happen on an item
going into and coming out of redis.

.. note::
    If an Exception is thrown while deserialization is attempted on a 
    particular item, ``None`` will be returned in its stead
    and an exception will be logged. In the case of :func:`SortedSet.take`,
    the failed item will simply be filtered from the returned list.

            
Sets
----

.. autoclass:: SortedSet
   :members:

   .. automethod:: __init__
   .. automethod:: __len__
   .. automethod:: __contains__


Specialized sets
----------------

The only builtin concrete subclass of :class:`SortedSet <SortedSet>` is 
:class:`TimeSortedSet`, which we've found to be the most common usecase.


.. autoclass:: TimeSortedSet
   :show-inheritance:
   :members:

   .. automethod:: __init__


Interfaces
----------

The :class:`Serializer` interface is included as a guideline for end-users.
It need not be subclassed for concrete serializers.

.. autoclass:: redset.interfaces.Serializer
   :members:

