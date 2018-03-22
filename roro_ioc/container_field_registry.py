import threading
from abc import ABCMeta

import attr
from typing import Dict, Any

from roro_ioc.container import IOCContainer
from roro_ioc.exceptions import NoValuesProvided


@attr.attrs
class _ContainerFieldRegistry(object):
    _mapping = attr.attrib(
        validator=attr.validators.instance_of(dict),
        default=attr.Factory(dict))  # type: Dict[Tuple[IOCContainer, basestring], int]

    # TODO: handle the leakage of IOC Containers Contexts (not their contents - those should not leak!)
    def add(self, ioc_container):
        for resource_name in ioc_container.provides:
            self._mapping[(ioc_container, resource_name)] = len(self._mapping)

    def get(self, ioc_container, field):
        return self._mapping[(ioc_container, field)]


_IOC_CONTAINER_FIELD_REGISTRY = _ContainerFieldRegistry()


def get_fast_retrieval_resource_handle(ioc_container, resource_name):
    return _IOC_CONTAINER_FIELD_REGISTRY.get(ioc_container, resource_name)


class ResourcesHolder(object):
    __metaclass__ = ABCMeta

    resources = {}  # type: Dict[basestring, Any]


_CONTAINER_FIELDS = threading.local()  # type: ResourcesHolder


def _flag_missing(field_name):
    raise NoValuesProvided('Mandatory field <{}> was not provided'.format(field_name))


_CONTAINER_FIELDS.flag_missing = _flag_missing


def register_ioc_container(ioc_container):
    _IOC_CONTAINER_FIELD_REGISTRY.add(ioc_container)


def get_fast_retrieval_context():
    # type: ()->ResourcesHolder
    return _CONTAINER_FIELDS
