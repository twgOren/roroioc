import inspect
from ast import parse, NodeTransformer, copy_location, Attribute, Name, Load, Is, Store, Assign, Compare, If, \
    FunctionDef, arguments, fix_missing_locations, Param, Subscript, Index, Num, Str, Expr, Call
from functools import partial
from itertools import takewhile
from logging import getLogger

from typing import Callable, Tuple, Any, Dict, List, Union

from roro_ioc.container import IOCContainer
from roro_ioc.container_field_registry import get_fast_retrieval_context, get_fast_retrieval_resource_handle

_logger = getLogger(__name__)


class SourceCodeInaccessibleError(ValueError):
    pass


def _get_source(callable_arg):
    source = inspect.getsource(callable_arg)

    start_indent = ''.join(takewhile(lambda l: l.isspace(), source))
    len_start_indent = len(start_indent)

    first_line_no = callable_arg.func_code.co_firstlineno

    source_stripped_prefix = ('\n' * (first_line_no - 1)) + \
                             ('\n'.join(line[len_start_indent:] for line in source.split('\n')))

    try:
        return parse(source_stripped_prefix)
    except SyntaxError:
        raise SourceCodeInaccessibleError('Could not parse source code for function {}. Retrieved {}'.format(
            callable_arg, source))


class _ManglePrivateMembers(NodeTransformer):
    def __init__(self, class_name):
        self.class_name = class_name

    # noinspection PyPep8Naming
    def visit_Attribute(self, node):
        # Make sure descendants of this node are visited too
        self.generic_visit(node)

        attribute_name = node.attr
        if self._should_mangle(attribute_name):
            mangled_name = self._get_mangled_name(attribute_name)
            return copy_location(
                Attribute(value=node.value, attr=mangled_name, ctx=node.ctx),
                node
            )
        else:
            return node

    def _should_mangle(self, attribute_name):
        return attribute_name.startswith('__') and (not attribute_name.endswith('__')) and self.class_name

    def _get_mangled_name(self, attribute_name):
        mangled_class_name = '_{}'.format(self.class_name.lstrip('_'))
        mangled_name = '{}{}'.format(mangled_class_name, attribute_name)
        return mangled_name


class _InjectParameters(NodeTransformer):
    def __init__(self, parameters, default_argument_name):
        self.parameters = parameters  # type: Tuple[Tuple[basestring, int], ...]
        self.injected_arguments_set = frozenset(parameter[0] for parameter in self.parameters)
        # Schema: (argument_name, resource_name, resource_handle)
        self.default_argument_name = default_argument_name  # type: basestring

    # noinspection PyPep8Naming
    def visit_FunctionDef(self, node):
        function_name = node.name

        INTERNAL_CONTEXT_NAME = '___INJECT_CONTEXT_INTERNAL'
        INTERNAL_RESOURCES_NAME = '___INJECT_CONTEXT_INTERNAL_RESOURCES'

        last_existing_arg = node.args.args[-1]  # non-empty because we inject somewhere
        new_args = node.args.args + [copy_location(Name(id=INTERNAL_CONTEXT_NAME, ctx=Param()), last_existing_arg)]

        last_existing_default = node.args.defaults[-1]
        new_defaults = node.args.defaults + [copy_location(Name(id=self.default_argument_name, ctx=Load()),
                                                           last_existing_default)]

        # Format: (Name(id='a', ctx=Param()), Name(id='foo', ctx=Load()))
        def generate_default_nodes():
            for (argument, default_value) in zip(node.args.args[-len(node.args.defaults):], node.args.defaults):
                if argument.id in self.injected_arguments_set:
                    yield (argument.id, default_value)

        default_nodes_mapping = dict(generate_default_nodes())

        def _generate_assignment((arg_name, arg_resource_handle)):
            # type: (Tuple[basestring, int]) -> If
            """
            We have a function that looks like:
            def do_something(param, model_=INJECTED):
                <...>

            We insert into its beginning a statement like
                ___INJECT_CONTEXT_INTERNAL_RESOURCES = ___INJECT_CONTEXT_INTERNAL.resources
                if model_ is INJECTED:
                    model_ = ___INJECT_CONTEXT_INTERNAL_RESOURCES[3]
                    if model is ___INJECT_CONTEXT_INTERNAL:    # means that no resource is available
                        ___INJECT_CONTEXT_INTERNAL_RESOURCES.flag_missing('model_')

            Code outside of this function sets a global variable _INJECTED__model to point at the right thing.
            """
            target_attribute = Subscript(value=Name(id=INTERNAL_RESOURCES_NAME, ctx=Load()),
                                         slice=Index(value=Num(n=arg_resource_handle)), ctx=Load())

            consequence = [
                Assign(targets=[Name(id=arg_name, ctx=Store())],
                       value=target_attribute),
                If(test=Compare(left=Name(id=arg_name, ctx=Load()), ops=[Is()],
                                comparators=[Name(id=INTERNAL_CONTEXT_NAME, ctx=Load())]),
                   body=[Expr(value=Call(func=Attribute(value=Name(id=INTERNAL_CONTEXT_NAME, ctx=Load()),
                                                        attr='flag_missing', ctx=Load()),
                                         keywords=[],
                                         starargs=None,
                                         kwargs=None,
                                         args=[Str(s=arg_name)]))],
                   orelse=[])
            ]  # type: List[Union[Assign, If]

            return If(test=Compare(left=Name(id=arg_name, ctx=Load()), ops=[Is()],
                                   comparators=[default_nodes_mapping[arg_name]]),
                      body=consequence,
                      orelse=[])

        first_body_element = node.body[0]
        align_with_first_body_element = partial(copy_location, old_node=first_body_element)

        new_body = [align_with_first_body_element(
            Assign(targets=[Name(id=INTERNAL_RESOURCES_NAME, ctx=Store())],
                   value=Attribute(value=Name(id=INTERNAL_CONTEXT_NAME,
                                              ctx=Load()), attr='resources', ctx=Load())))]

        new_body.extend(map(align_with_first_body_element, map(_generate_assignment, self.parameters)))
        new_body.extend(node.body)

        result = copy_location(
            FunctionDef(name=function_name,
                        args=arguments(
                            args=new_args,
                            vararg=node.args.vararg,
                            kwarg=node.args.kwarg,
                            defaults=new_defaults),
                        body=new_body,
                        decorator_list=[]),  # Note that no decorators are applied, as @inject has to be the first
            node
        )
        return result


def rewrite_ast(type_or_callable, class_name, injectable_arguments_tuple, arg_to_ioc_container):
    # type: (Callable, basestring, Tuple[Tuple[basestring, basestring, Any], ...], Dict[basestring, IOCContainer])
    globals_dict = type_or_callable.func_globals
    ast_structure = _get_source(type_or_callable)
    function_name = ast_structure.body[0].name

    injected_arguments = tuple((argument_name,
                                get_fast_retrieval_resource_handle(arg_to_ioc_container[resource_name], resource_name))
                               for (argument_name, resource_name, _) in injectable_arguments_tuple)
    default_value_name = '__INJECT___FAST_RETRIEVAL_CONTEXT'
    _InjectParameters(injected_arguments, default_value_name).visit(ast_structure)
    _ManglePrivateMembers(class_name).visit(ast_structure)
    fix_missing_locations(ast_structure)

    locals_dict = {default_value_name: get_fast_retrieval_context()}
    eval(compile(ast_structure, filename=inspect.getfile(type_or_callable), mode="exec"),
         globals_dict, locals_dict)

    return locals_dict.get(function_name)
