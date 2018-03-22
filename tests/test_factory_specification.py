from unittest import TestCase

from attr import attrs, attrib, Factory

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
        @attrs
        class _MockAttrClass(object):
            no_default = attrib()
            string_default = attrib(default='default_string')
            factory_default = attrib(default=Factory(dict))

        specification = extract_factory_specification(_MockAttrClass)
        self.assertItemsEqual(('no_default', 'string_default', 'factory_default'), specification.argument_names)
        self.assertIn('factory_default', specification.argument_default_values)
        self.assertEqual('default_string', specification.argument_default_values['string_default'])

    def test_specification_for_attrs_object(self):
        class _MockClass(object):
            pass

        specification = extract_factory_specification(_MockClass)
        self.assertIs(_MockClass.__init__, specification.constructing_function)

    def test_degenerate_specification_for_non_callable(self):
        # noinspection PyTypeChecker
        specification = extract_factory_specification('Not a callable object')
        self.assertFalse(specification.argument_default_values)
        self.assertFalse(specification.argument_names)
