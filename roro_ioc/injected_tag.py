import attr


@attr.attrs
class InjectedTag(object):
    pass


INJECTED = InjectedTag()

INJECTED_IF_AVAILABLE = InjectedTag()
