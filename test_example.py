import pytest


def test_example_pass():
    x = 1
    assert x == 1

def test_example_fail():
    y = 2
    with pytest.raises(AssertionError):
        assert y == 1
