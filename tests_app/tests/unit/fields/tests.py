from rest_framework_extensions import fields
from rest_framework.tests.test_fields import FieldValues


class TestMappingFieldWithIntKeys(FieldValues):
    """
    Valid and invalid values for `MappingField`.
    """
    valid_inputs = {
        'one': 1,
        'two': 2,
        3: 'three',
        4: 'four'
    }
    invalid_inputs = {
        5: ['"5" not found in "mapping" values'],
        'abc': ['"abc" not found in "mapping" values']
    }
    outputs = {
        1: 'one',
        2: 'two',
        'three': 3,
        'four': 4
    }
    field = fields.MappingField(
        mapping={
            1: 'one',
            2: 'two',
            'three': 3,
            'four': 4
        }
    )
