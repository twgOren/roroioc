class NoSourceForArgument(TypeError):
    pass


class NoValuesProvided(ValueError):
    pass


class NoDefaultValueForArgument(ValueError):
    pass


class DoubleProvidingProhibited(TypeError):
    pass


class InvalidPayload(ValueError):
    pass


class CannotArmTwice(Exception):
    pass
