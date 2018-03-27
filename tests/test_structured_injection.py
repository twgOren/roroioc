from traceback import format_stack
from unittest import TestCase, skip

import attr
from cached_property import cached_property

from roro_ioc import (NoSourceForArgument,
                      create_ioc_container,
                      inject_methods,
                      inject_methods_,
                      NoValuesProvided,
                      INJECTED, inject_)


@attr.attrs
class Parameters(object):
    a = attr.attrib()
    b = attr.attrib()

    @cached_property
    def c(self):
        return 11


TEST_PARAMETERS_IOC_CONTAINER = create_ioc_container(Parameters)


@inject_methods(TEST_PARAMETERS_IOC_CONTAINER)
class AppliedInjection(object):
    x = 3

    def test(self, a=INJECTED, b=INJECTED):
        return self.x - 3 + a + b

    def test_c(self, c=None):
        return c ** 2


@inject_methods_(TEST_PARAMETERS_IOC_CONTAINER)
class AppliedInjectionUnderscore(object):
    def __init__(self):
        self.x = 3

    def test(self, a_=INJECTED, b_=INJECTED):
        return self.x - 3 + a_ + b_

    def not_to_be_wrapped(self, limit):
        return format_stack(limit=limit)


@attr.attrs
class InjectConstructorAttrs(object):
    a_ = attr.attrib(default=None)


class InjectConstructor(object):
    def __init__(self, a_=None):
        self.a = a_


@inject_methods(TEST_PARAMETERS_IOC_CONTAINER)
class MockWithMangledNames(object):
    def foo(self, a=INJECTED):
        return self.__foo() + a

    def __foo(self):
        return 0


class TestErrorHandling(TestCase):
    @skip("TODO: the wrong exception is raised because no injector was ever armed")
    def test_no_values_provided_first_injection(self):
        a = AppliedInjection()
        with self.assertRaises(NoValuesProvided):
            a.test()

    def test_no_values_provided(self):
        a = AppliedInjection()
        with TEST_PARAMETERS_IOC_CONTAINER.arm(Parameters(1, 2)):
            a.test()
        with self.assertRaises(NoValuesProvided):
            a.test()

    def test_no_values_provided_underscore(self):
        a = AppliedInjectionUnderscore()
        with TEST_PARAMETERS_IOC_CONTAINER.arm(Parameters(1, 2)):
            a.test()
        with self.assertRaises(NoValuesProvided):
            a.test()

    def test_invalid_argument(self):
        with self.assertRaises(NoSourceForArgument):
            @inject_methods(TEST_PARAMETERS_IOC_CONTAINER)
            class Test(object):
                def test(self, z=INJECTED):
                    return z


class TestStructuredInjection(TestCase):
    def test_sanity(self):
        with self._arm():
            a = AppliedInjection()
            self.assertEqual(5, a.test())
            self.assertEqual(8 + 3, a.test(8))
            self.assertEqual(8 + 9, a.test(8, 9))
            self.assertEqual(2 + 10, a.test(b=10))
            self.assertEqual(11 ** 2, a.test_c())

        with self.assertRaises(NoValuesProvided):
            a.test()

    def test_sanity_underscore(self):
        with self._arm():
            a = AppliedInjectionUnderscore()
            self.assertEqual(2 + 3, a.test())
            self.assertEqual(8 + 3, a.test(8))
            self.assertEqual(8 + 9, a.test(8, 9))
            self.assertEqual(2 + 9, a.test(b_=9))
            # Should be something like
            # TestStructuredInjection.test_sanity_ in /home/uri/source/shopymate/tests/shared_tests
            # File "/home/uri/source/shopymate/tests/shared_tests/test_structured_injection.py", line , in test_sanity_
            self.assertIn('test_structured_injection.py', a.not_to_be_wrapped(2)[0].split()[1])

    def test_inject_constructor(self):
        with self._arm():
            x = inject_(TEST_PARAMETERS_IOC_CONTAINER)(InjectConstructor)()
            self.assertEqual(2, x.a)

    def test_inject_constructor_attrs(self):
        with self._arm():
            x = inject_(TEST_PARAMETERS_IOC_CONTAINER)(InjectConstructorAttrs)()
            self.assertEqual(2, x.a_)

    def test_injected_mangled_name(self):
        with self._arm():
            self.assertEqual(2, MockWithMangledNames().foo())

    def test_inject_method_to_underscored_class_name(self):
        @inject_methods(TEST_PARAMETERS_IOC_CONTAINER)
        class _MockWithMangledNames(object):
            def foo(self, a=INJECTED):
                return self.__foo() + a

            def __foo(self):
                return 0

        with self._arm():
            self.assertEqual(2, _MockWithMangledNames().foo())

    def test_inject_method_to_mangled_class_name(self):
        @inject_methods(TEST_PARAMETERS_IOC_CONTAINER)
        class __MockWithMangledNames(object):
            def foo(self, a=INJECTED):
                return self.__foo() + a

            def __foo(self):
                return 0

        with self._arm():
            self.assertEqual(2, __MockWithMangledNames().foo())

    def _arm(self):
        return TEST_PARAMETERS_IOC_CONTAINER.arm(Parameters(2, 3))
