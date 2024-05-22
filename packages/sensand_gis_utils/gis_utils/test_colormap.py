import unittest

from gis_utils.colormap import create_levels, get_colormap

def test_create_levels():
    # Test with default parameters
    levels = create_levels()
    assert len(levels) == 21
    assert levels[0] == 0
    assert levels[-1] == 1

    # Test with custom levels
    custom_levels = [0, 5, 10]
    levels = create_levels(custom_levels, 5)
    assert len(levels) == 5
    assert levels[0] == 0
    assert levels[-1] == 10

    # Test with different color count
    levels = create_levels(color_count=10)
    assert len(levels) == 10
    assert levels[0] == 0
    assert levels[-1] == 1

class TestGetColormap(unittest.TestCase):
    def test_continuous_default(self):
        """Test colormap generation with default continuous settings."""
        result = get_colormap()
        self.assertEqual(len(result), 21)  # Expecting 21 colors

    def test_discrete_custom_levels(self):
        """Test colormap generation with custom discrete levels."""
        custom_levels = [-1, 0, 1]
        result = get_colormap(custom_levels=custom_levels, color_count=21)
        self.assertEqual(len(result), 21)  # Expecting 21 colors based on color_count

    def test_invalid_input(self):
        """Test the function with invalid input."""
        with self.assertRaises(ValueError):
            get_colormap(custom_levels=[], color_count=21)  # Expecting a ValueError for empty levels list

    def test_custom_levels_min_max_and_count(self):
        """Test that the colormap correctly uses custom levels for min, max, and color count."""
        color_name = 'viridis'
        custom_levels = [-10, 0, 10]  # Define some custom levels
        color_count = 50  # Define a specific color count
        result = get_colormap(color_name=color_name, custom_levels=custom_levels, color_count=color_count)
       
        # Check the number of colors generated
        self.assertEqual(len(result), color_count, "The number of generated colors should match the color_count")
       
        # Extract level values from result (a list of [level, color] pairs)
        result_levels = [sublist[0] for sublist in result]
       
        # Check the minimum and maximum values
        self.assertAlmostEqual(min(result_levels), min(custom_levels), places=2, msg="The minimum level should match the minimum custom level")
        self.assertAlmostEqual(max(result_levels), max(custom_levels), places=2, msg="The maximum level should match the maximum custom level")
