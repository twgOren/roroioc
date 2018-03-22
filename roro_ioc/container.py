from abc import ABCMeta, abstractproperty

from typing import FrozenSet


class CannotBeProvided(ValueError):
    pass


class IOCContainer(object):
    __metaclass__ = ABCMeta

    @abstractproperty
    def provides(self):
        # type: ()->FrozenSet[basestring]
        pass

    @abstractproperty
    def provided(self):
        # type: ()->object
        pass
