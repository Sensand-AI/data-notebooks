import pytest
from gis_utils.colormap import create_levels

def test_example_pass():
    x = 1
    assert x == 1

def test_example_fail():
    y = 2
    with pytest.raises(AssertionError):
        assert y == 1

levels = create_levels()
print(levels)
