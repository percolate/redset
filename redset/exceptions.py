

class EmptyException(Exception):
    """
    Raised when attempting to get from an empty queue.

    """
    pass


class LockTimeout(Exception):
    """
    Raised when waiting too long on a queue lock.

    """
    pass

