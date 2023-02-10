"""Testing the simple_function."""
from template_python.example_endpoint.endpoint import Endpoint


def test_simple_function():
    endpoint = Endpoint()

    input_num = 1
    expected_output = 2
    actual_output = endpoint.simple_method(input_num)

    assert actual_output == expected_output
