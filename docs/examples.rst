
.. _examples:

Examples
========

Task system
-------------

Here's an example that shows how to construct a very basic multi-producer,
multi-consumer prioritized task system.

::

    import json
    from collections import namedtuple
    import redset, redis
    from redset.serializers import NamedtupleSerializer

    Task = namedtuple('Task', 'foo,bar,priority')

    task_set = redset.SortedSet(
        redis.Redis(),
        'tasks',
        scorer=lambda task: task.priority,
        serializer=NamedtupleSerializer(Task),
    )

Now we can produce from anywhere:

::

    task_set.add(Task('yo', 'baz', 1))
    task_set.add(Task('hey', 'roar', 0))

And maybe have a daemon that consumes:

::

    def process_tasks():
        while True:
            for task in task_set.take(10):
                do_work_on_task(task)
            sleep(1)

