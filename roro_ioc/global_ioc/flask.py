from __future__ import absolute_import

from flask import Blueprint

from roro_ioc.global_ioc.ioc import Bootstrapper


def register_bootstrapped_blueprint(blueprint, bootstrapper):
    # type: (Blueprint, Bootstrapper) -> None
    @bootstrapper.on_bootstrap
    def on_bootstrap():
        deferred_funcs = list(blueprint.deferred_functions)

        @bootstrapper.on_unbootstrap
        def restore_state():
            blueprint.deferred_functions = deferred_funcs
