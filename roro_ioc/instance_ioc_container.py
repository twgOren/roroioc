import inspect
import itertools
import threading
from contextlib import contextmanager

import attr
from attr.exceptions import NotAnAttrsClassError
from attr.validators import instance_of
from cached_property import cached_property
from typing import FrozenSet

from roro_ioc.container import IOCContainer
from roro_ioc.container_field_registry import get_fast_retrieval_context, register_ioc_container, \
    get_fast_retrieval_resource_handle
from roro_ioc.exceptions import InvalidPayload, CannotArmTwice


def _validate_condition(o, a, v):
    return attr.fields(v)


_STRUCTURED_LOCAL = threading.local()


@attr.attrs(hash=False)
class InstanceIOCContainer(IOCContainer):
    injected_resource_type = attr.attrib(validator=_validate_condition)  # type: type
    allow_idempotent_arming = attr.attrib(validator=instance_of(bool))  # type: bool

    @cached_property
    def provides(self):
        # type: () -> FrozenSet[basestring]
        try:
            iterable_attrs = (field.name for field in attr.fields(self.injected_resource_type))
        except NotAnAttrsClassError:
            iterable_attrs = ()

        def condition(p):
            return inspect.ismethoddescriptor(p) or inspect.ismemberdescriptor(p) or inspect.isdatadescriptor(p)

        iterable_method_descriptors = (name for (name, dontcare) in
                                       inspect.getmembers(self.injected_resource_type, condition)
                                       if not name.startswith('_'))

        result = frozenset(itertools.chain(iterable_attrs, iterable_method_descriptors))

        return result

    def _validate_payload(self, payload):
        if not isinstance(payload, self.injected_resource_type):
            raise InvalidPayload()
        return True

    @contextmanager
    def arm(self, payload):
        self._validate_payload(payload)

        fast_retrieval_context = get_fast_retrieval_context()
        existing = _STRUCTURED_LOCAL.__dict__.get(self)
        if existing is not None:
            if (self.allow_idempotent_arming and
                    existing is payload):
                yield
                # And do nothing else
            else:
                raise CannotArmTwice()
        else:  # Is currently empty
            _integrate_resources(self, fast_retrieval_context, payload)
            _STRUCTURED_LOCAL.__dict__[self] = payload
            try:
                yield

            finally:
                del _STRUCTURED_LOCAL.__dict__[self]
                _cleanup_resources(self, fast_retrieval_context)

    @property
    def provided(self):
        return _STRUCTURED_LOCAL.__dict__.get(self)


# fast_retrieval_context is used as a placeholder for resources that are not currently provided
def _integrate_resources(ioc_container, fast_retrieval_context, payload):
    if not hasattr(fast_retrieval_context, 'resources'):
        fast_retrieval_context.resources = []

    handles_to_resources = {
        get_fast_retrieval_resource_handle(ioc_container, resource_name): getattr(payload, resource_name)
        for resource_name in ioc_container.provides}

    max_handle = max(handles_to_resources)
    current_length = len(fast_retrieval_context.resources)
    if max_handle >= current_length:
        fast_retrieval_context.resources.extend([fast_retrieval_context] * (1 + max_handle - current_length))

    for handle, resource in handles_to_resources.iteritems():
        assert fast_retrieval_context.resources[handle] is fast_retrieval_context
        fast_retrieval_context.resources[handle] = resource

# fast_retrieval_context is used as a placeholder for resources that are not currently provided
def _cleanup_resources(ioc_container, fast_retrieval_context):
    for resource_name in ioc_container.provides:
        handle = get_fast_retrieval_resource_handle(ioc_container, resource_name)
        fast_retrieval_context.resources[handle] = fast_retrieval_context


def create_ioc_container(injected_resource_type, allow_idempotent_arming=False):
    # type: (type, bool)->InstanceIOCContainer
    result = InstanceIOCContainer(injected_resource_type,
                                  allow_idempotent_arming)
    register_ioc_container(result)
    return result
