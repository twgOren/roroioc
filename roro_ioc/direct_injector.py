import attr
from decorator import contextmanager
from roro_ioc.caching import static_memoize_weak_result
from typing import Any

from roro_ioc.instance_ioc_container import create_ioc_container, InstanceIOCContainer


@static_memoize_weak_result
def create_direct_injector(injected_type, injected_instance):
    # type: (type, Any)->DirectInjector
    assert isinstance(injected_instance, injected_type)
    return DirectInjector(create_ioc_container(injected_type),
                          injected_instance)


@attr.attrs
class DirectInjector(object):
    __structured_injector = attr.attrib(validator=attr.validators.instance_of(InstanceIOCContainer))
    __injector_configuration = attr.attrib()

    @contextmanager
    def arm(self):
        with self.__structured_injector.arm(self.__injector_configuration):
            yield

    def inject(self, to_decorate):
        def decorated(*args, **kwargs):
            with self.__structured_injector.arm(self.__injector_configuration):
                return self.__structured_injector.inject(to_decorate)(*args, **kwargs)

        return decorated
