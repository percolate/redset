"""
Builtin serializers.

"""

import json

from redset.interfaces import Serializer


class NamedtupleSerializer(Serializer):
    """
    Serialize namedtuple classes.

    """
    def __init__(self, NTClass):
        """
        :param NTClass: the namedtuple class that you'd like to marshal to and
            from.
        :type NTClass: type

        """
        self.NTClass = NTClass

    def loads(self, str_from_redis):
        return self.NTClass(**json.loads(str_from_redis))

    def dumps(self, nt_instance):
        return json.dumps(nt_instance._asdict())
