import itertools
from inspect import getargspec
from logging import getLogger

import attr
from typing import Callable

frozendict = dict  # todo: change to immutable dict

_logger = getLogger(__name__)


@attr.attrs
class FactorySpecification(object):
    constructing_function = attr.attrib()  # type: Callable
    argument_names = attr.attrib(validator=attr.validators.instance_of(tuple))  # type: Tuple[basestring, ...]
    argument_default_values = attr.attrib(validator=attr.validators.instance_of(
        frozendict))  # type: Dict[basestring, Any]


def _format_defaults(arg_names, defaults):
    defaults = defaults or ()
    defaults_matching = (attr.NOTHING,) * (len(arg_names) - len(defaults)) + defaults
    return frozendict((arg_name, default_value) for (arg_name, default_value)
                      in zip(arg_names, defaults_matching)
                      if default_value != attr.NOTHING)


def extract_factory_specification_for_attrs(type, allow_defaults):
    fields = (field for field in attr.fields(type)
              if allow_defaults or field.default == attr.NOTHING)
    (fields_for_names, fields_for_defaults) = itertools.tee(fields, 2)

    argument_names = tuple(field.name for field in fields_for_names)
    defaults = frozendict((field.name, field.default) for field in fields_for_defaults
                          if field.default != attr.NOTHING)
    subject_callable = type
    return FactorySpecification(subject_callable, argument_names, defaults)


def _extract_factory_specification_for_functions(functional_object):
    argument_names = ()
    defaults = frozendict()
    try:
        argspec = getargspec(functional_object)
        argument_names = tuple(argspec.args)
        defaults = _format_defaults(argument_names, argspec.defaults)
    except TypeError:
        _logger.exception('Could not get argument specs for %s', functional_object)

    return FactorySpecification(functional_object, argument_names, defaults)


def extract_factory_specification(type_or_factory, allow_defaults=True):
    if isinstance(type_or_factory, type):
        try:
            return extract_factory_specification_for_attrs(type_or_factory, allow_defaults)
        except attr.exceptions.NotAnAttrsClassError:
            subject_callable = type_or_factory.__init__
            # May still fail for built-in objects/slots/...
    else:
        subject_callable = type_or_factory

    return _extract_factory_specification_for_functions(subject_callable)
