import inspect
import new
from functools import wraps
from logging import getLogger
from os import environ

from typing import Optional

from roro_ioc.ast_injection import rewrite_ast
from roro_ioc.container import IOCContainer
from roro_ioc.exceptions import NoSourceForArgument, NoDefaultValueForArgument, DoubleProvidingProhibited
from roro_ioc.exceptions import NoValuesProvided
from roro_ioc.factory_inspection import extract_factory_specification, FactorySpecification
from roro_ioc.injected_tag import INJECTED

_USE_WRAPPING_INJECTOR = environ.get('TWG_WRAPPING_INJECTOR')

_logger = getLogger()


def __get_class_name():
    stack_frame = inspect.currentframe().f_back.f_back
    self = stack_frame.f_locals.get('self', None)
    if stack_frame.f_code.co_name == '<module>' or '__module__' not in stack_frame.f_locals:
        # only classes have this:
        return None
    else:
        return stack_frame.f_code.co_name


def inject(*injectors):
    return __inject_internal('', injectors, __get_class_name())


def inject_(*injectors):
    return __inject_internal('_', injectors, __get_class_name())


def inject_methods(*injectors):
    return __inject_methods_internal('', injectors)


def inject_methods_(*injectors):
    return __inject_methods_internal('_', injectors)


def __member_condition(x):
    return inspect.ismethod(x) or inspect.isfunction(x)


def __unbind(method):
    # TODO: python2 specific code
    # See: http://stackoverflow.com/questions/14574641/python-get-unbound-class-method
    if not inspect.ismethod(method) or method.im_self is None:
        return method
    return new.instancemethod(method.im_func, None, method.im_class)


def __inject_methods_internal(suffix, injectors):
    assert all(isinstance(injector, IOCContainer) for injector in injectors)

    def treat(subject_class, function_object):
        unbound = __unbind(function_object)
        result = __inject_internal(suffix, injectors, subject_class.__name__)(unbound)
        if result == unbound:  # but always different than the original for bound methods
            return function_object
        else:
            return result

    def decorate(subject_class):
        patch_list = tuple((name,
                            inspect.isfunction(method),
                            inspect.ismethod(method) and method.__self__ is subject_class,
                            method,
                            treat(subject_class, method))
                           for (name, method) in inspect.getmembers(subject_class, __member_condition))
        for (name, is_static, is_class, original_value, value) in patch_list:
            # If we hadn't decorated the method, it does not need re-decoration
            if original_value == value:
                continue
            if is_static:
                value = staticmethod(value)
            elif is_class:
                value = classmethod(value)
            setattr(subject_class, name, value)

        return subject_class

    return decorate


def __inject_internal(suffix, injectors, class_name):
    suffix_length = len(suffix) if suffix else 0

    arg_to_ioc_container = {name: injector
                            for injector in injectors
                            for name in injector.provides}

    # Reverse order - first injector overrides
    already_seen = set()
    for injector in injectors:
        for name in injector.provides:
            if name in already_seen:
                raise DoubleProvidingProhibited('Resource %s provided twice, injectors %s',
                                                name, arg_to_ioc_container)
            already_seen.add(name)

    def correspondence(argument_name):
        # type: (basestring) -> Optional[basestring]
        # Matches 'mydata_' to 'mydata'
        if suffix:
            if not argument_name.endswith(suffix):
                return None  # is not marked for replacement
            result = argument_name[:-suffix_length]
        else:
            result = argument_name
        if result in arg_to_ioc_container:
            return result
        else:
            return None  # is not provided

    def decorate(type_or_callable):
        factory_specification = extract_factory_specification(type_or_callable)  # type: FactorySpecification

        injectable_arguments = {argument: corresponding
                                for (argument, corresponding) in
                                ((argument, correspondence(argument)) for argument in
                                 factory_specification.argument_names)
                                if corresponding is not None}

        # This is a mapping to e.g. 'mydata_' to 'mydata'

        def validate_treatment(argument_name):
            # type: (basestring)->bool
            _NULL = []
            result = factory_specification.argument_default_values.get(argument_name, _NULL)
            if result is _NULL:
                if argument_name in injectable_arguments:
                    raise NoDefaultValueForArgument(
                        'Argument {} in callable {} implied to be injectable, but no default value was specified'.
                            format(argument_name, type_or_callable))
            else:
                if result is INJECTED and argument_name not in injectable_arguments:
                    raise NoSourceForArgument('Cannot inject argument {} into callable {}, injectable arguments {}'.
                                              format(argument_name, type_or_callable,
                                                     injectable_arguments.keys()))

        for element in factory_specification.argument_names:
            validate_treatment(element)

        # We do this only after calculating injection_treatment, so we can catch variables marked as INJECT who do not
        # have a source
        if len(injectable_arguments) == 0:
            return type_or_callable  # Nothing to do here

        arg_to_position = {arg_name: index
                           for (index, arg_name) in enumerate(factory_specification.argument_names)
                           if arg_name in injectable_arguments}

        # optimize for retrieval
        injectable_arguments_tuple = tuple((argument, corresponding, arg_to_position[argument])
                                           for (argument, corresponding) in injectable_arguments.iteritems())

        def _raise_missing(argument, corresponding):
            if argument not in factory_specification.argument_default_values or \
                    factory_specification.argument_default_values[argument] is INJECTED:
                raise NoValuesProvided('Cannot provide for value {}'.format(corresponding))

        if not _USE_WRAPPING_INJECTOR:
            if inspect.isfunction(type_or_callable) or \
                    inspect.ismethod(type_or_callable) or inspect.ismethoddescriptor(type_or_callable):
                return rewrite_ast(type_or_callable,
                                   class_name,
                                   injectable_arguments_tuple,
                                   arg_to_ioc_container)

        @wraps(type_or_callable)
        def substitute_parameters(*args, **kwargs):
            for (argument, corresponding, position_for_argument) in injectable_arguments_tuple:
                if position_for_argument < len(args) or argument in kwargs:
                    continue  # do not override this variable
                provided = arg_to_ioc_container[corresponding].provided
                try:
                    kwargs[argument] = getattr(provided, corresponding)
                except AttributeError:  # provided is None
                    # If it has a default, and no provider is available for the data, let the default be used implicitly
                    _raise_missing(argument, corresponding)

            return type_or_callable(*args, **kwargs)

        return substitute_parameters

    return decorate
