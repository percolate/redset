
import abc


class Serializer(object):
    """
    This is a guideline for implementing a serializer for redset. Serializers
    need not subclass this directly, but should match the interface defined
    here.

    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def loads(self, str_from_redis):
        """
        Deserialize a str item from redis into a Python object.

        :param str_from_redis: the str corresponding with an item in redis
        :type str_from_redis: str
        :returns: object

        """

    @abc.abstractmethod
    def dumps(self, obj):
        """
        Serialize a Python object into a `str`

        :param obj: the Python object to be stored in a sorted set
        :returns: str

        """
