from typing import Any

from roro_ioc.io import load_file


class Configuration(object):
    def __init__(self, config_source):
        assert isinstance(config_source, dict)
        self.config_source = config_source

    def get(self, path, default=None, required=False):
        # type: (str, Any, bool) -> dict
        val = self.config_source
        for segment in path.split('.'):
            if val is None or segment not in val:
                if required:
                    raise ValueError("Missing required configuration key: '{}'".format(path))
                else:
                    return default

            val = val.get(segment)

        return val

    @staticmethod
    def from_file(filename):
        return Configuration(load_file(filename))

    @staticmethod
    def bind_to_bootstrapper(bootstrapper):
        @bootstrapper.on_bootstrap
        def bind_configuration(binder, configuration):
            binder.bind(Configuration, configuration)

        ConfigurationAttribute.bootstrapper = bootstrapper


class ConfigurationError(Exception):
    pass


class ConfigurationAttribute(object):
    """ A descriptor that binds an attribute to a Configuration value, by fetching it at bootstrap time. """

    __slots__ = ('_value',)

    bootstrapper = None

    def __init__(self, config_key, default=None, required=False):
        self._value = default

        bootstrapper = self.bootstrapper
        if bootstrapper is None:
            raise ConfigurationError("ConfigurationAttribute must be created after Configuration has been bound to a Bootstrapper")

        @bootstrapper.on_bootstrap
        def load_value(configuration):
            self._value = configuration.get(config_key, default=default, required=required)

    def __get__(self, instance, owner):
        return self._value
