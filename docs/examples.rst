
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

    Task = namedtuple('Task', 'foo,bar,priority')

    class TaskSerializer(redset.interfaces.Serializer):
        
        def loads(self, incoming_str):
            d = json.loads(incoming_str) 
            return Task(d['foo'], d['bar'], d['priority'])

        def dumps(self, task):
            return json.dumps(task._asdict)

    task_set = redset.SortedSet(
        redis.Redis(),
        'tasks',
        scorer=lambda task: task.priority,
        serializer=TaskSerializer(),
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
                do_something(task)
            sleep(1)

