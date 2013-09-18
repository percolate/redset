
import abc


class Serializer(object):
    """
    This is a guideline for implementing a serializer for redset. Serializers
    need not subclass this directly, but should match the interface defined
    here.

    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def load(self, str_from_redis):
        """
        Deserialize a str item from redis into a Python object.

        Args:
            str_from_redis (str): the str corresponding with an item in redis

        Returns:
            object.

        """

    @abc.abstractmethod
    def dump(self, obj):
        """
        Serialize a Python object into a `str`

        Args:
            obj (object): the Python object to be stored in a sorted set

        Returns:
            str.

        """


