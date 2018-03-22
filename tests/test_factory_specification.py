from unittest import TestCase

from roro_ioc.factory_inspection import extract_factory_specification, FactorySpecification


def _mock_func(x):
    return x


def _mock_func_with_kwargs(x, y=1, z='foo'):
    return x


class TestFactorySpecification(TestCase):
    def test_degenerate(self):
        specification = extract_factory_specification(_mock_func)
        self.assertIsInstance(specification, FactorySpecification)
        self.assertIs(_mock_func, specification.constructing_function)

    def test_argument_names(self):
        specification = extract_factory_specification(_mock_func)
        self.assertItemsEqual(['x'], specification.argument_names)

    def test_kwargs(self):
        specification = extract_factory_specification(_mock_func_with_kwargs)
        self.assertItemsEqual(['x', 'y', 'z'], specification.argument_names)
        self.assertEqual({'y': 1, 'z': 'foo'}, specification.argument_default_values)

    def test_specification_for_init_if_type(self):
        class _MockClass(object):
            pass

        specification = extract_factory_specification(_MockClass)
        self.assertIsNot(_MockClass, specification.constructing_function)
        self.assertIs(_MockClass.__init__, specification.constructing_function)

    def test_degenerate_specification_for_non_callable(self):
        # noinspection PyTypeChecker
        specification = extract_factory_specification('Not a callable object')
        self.assertFalse(specification.argument_default_values)
        self.assertFalse(specification.argument_names)
