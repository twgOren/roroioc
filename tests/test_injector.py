from unittest import TestCase

from attr import attrib, attrs

from roro_ioc import create_ioc_container, inject, INJECTED


@attrs
class MockParameters(object):
    injected_parameter = attrib()


MOCK_CONTEXT = create_ioc_container(MockParameters)


@inject(MOCK_CONTEXT)
def _identity(injected_parameter=INJECTED):
    return injected_parameter


class TestFunctionInjection(TestCase):
    def test_one_parameter_injection(self):

        with MOCK_CONTEXT.arm(MockParameters(injected_parameter=4)):
            self.assertEqual(4, _identity())

    def test_call_parameter_supersedes_injection(self):

        with MOCK_CONTEXT.arm(MockParameters(injected_parameter=4)):
            self.assertEqual(5, _identity(5))

    @skip
    def test_call_without_context_is_possible(self):
        self.assertEqual(5, _identity(5))
