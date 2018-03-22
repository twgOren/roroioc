import copy
import inspect
from collections import defaultdict
from enum import Enum
from types import FunctionType

import inject as _inject
from typing import List, Dict


class _Hook(Enum):
    BOOTSTRAP = 'bootstrap'
    UNBOOTSTRAP = 'unbootstrap'
    POST_BOOTSTRAP = 'post_bootstrap'


class Bootstrapper(object):
    def __init__(self):
        self._hooks = defaultdict(list)  # type: Dict[_Hook, List[FunctionType]]
        self._initial_hooks = {}

    def bootstrap(self, **fundamentals):
        """ Performs a bootstrapping process by invoking bootstrap and post-bootstrap operations.

        Bootstrap operations can configure the injector by accepting a `binder` argument.
        They can optionally receive other external information by accepting arguments with names
        matching the keys given in `fundamentals`. Arguments missing from the fundamentals map
        and not given default values will result in a `ConfigurationError`.

        Post-bootstrap operations accept no arguments, but they are invoked after the injector
        has been configured and so can use injection. """

        self._initial_hooks = copy.deepcopy(self._hooks)

        def configure_injector(binder):
            kwargs_pool = dict(fundamentals)
            kwargs_pool.update(binder=binder)

            for bootstrap_func in self._hooks[_Hook.BOOTSTRAP]:
                argspec = inspect.getargspec(bootstrap_func)
                arg_names = argspec.args
                arg_defaults = dict(zip(reversed(arg_names), reversed(argspec.defaults or ())))

                supplied_kwargs = {name: kwargs_pool[name] for name in arg_names if name in kwargs_pool}
                missing_kwargs = [name for name in arg_names if name not in supplied_kwargs and name not in arg_defaults]
                if missing_kwargs:
                    raise KeyError("Bootstrap function '{}' ({}:{}) is missing fundamentals: {}".format(
                        bootstrap_func.func_name,
                        bootstrap_func.func_code.co_filename,
                        bootstrap_func.func_code.co_firstlineno,
                        missing_kwargs))

                bootstrap_func(**supplied_kwargs)

        _inject.configure(configure_injector)

        for post_bootstrap_func in self._hooks[_Hook.POST_BOOTSTRAP]:
            post_bootstrap_func()

    def unbootstrap(self):
        """ Performs registered un-bootstrap operations and clears the injector. """

        for unbootstrap_func in self._hooks[_Hook.UNBOOTSTRAP]:
            unbootstrap_func()

        self._hooks = self._initial_hooks
        _inject.clear()

    def on_bootstrap(self, f):
        """ Registers a function as a bootstrap operation.

        The target function will be called during bootstrapping, with its kwargs populated from the fundamentals
        provided to `bootstrap`, as well as an optional `binder` argument populated with the binder of the
        injector being configured. """

        return self._on_hook(_Hook.BOOTSTRAP, f)

    def post_bootstrap(self, f):
        """ Registers a function as an unbootstrap operation.

        The target function will be called during unbootstrapping, with no arguments (but can use injection). """

        return self._on_hook(_Hook.POST_BOOTSTRAP, f)

    def on_unbootstrap(self, f):
        """ Registers a function as a post-bootstrap operation.

        The target function will be called after all bootstrap functions have completed,
        with no arguments (but it can use injection). """

        return self._on_hook(_Hook.UNBOOTSTRAP, f)

    def _on_hook(self, hook, func):
        self._hooks[hook].append(func)
        return func


inject = _inject.params
Binder = _inject.Binder  # for type hinting

