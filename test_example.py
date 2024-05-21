import pytest

def test_example_pass():
    """
    Use assert to ensure test result is as expected
    """
    x = 0
    x =+ 1
    assert x == 1

def test_example_fail():
    """
    Use pytest.raises() to ensure test result fails as expected
    """
    y = 2
    with pytest.raises(AssertionError):
        assert y == 1
