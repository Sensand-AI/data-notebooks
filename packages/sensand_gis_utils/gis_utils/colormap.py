import matplotlib.colors
import matplotlib.pyplot as plt
import numpy as np

def create_levels(custom_levels=None, color_count=21):
    """
    Creates a range of levels for colormap generation.
    
    Parameters:
    - custom_levels (list): Optional. A list of custom level values.
    - color_count (int): Optional. The number of levels to generate. Default is 21.
    
    Returns:
    - levels (ndarray): An array of levels.
    """
    if custom_levels is None:
        levels = np.linspace(0, 1, color_count)
    else:
        min_level = min(custom_levels)
        max_level = max(custom_levels)
        levels = np.linspace(min_level, max_level, color_count)
    return levels

def get_colormap(parameters: dict, custom_levels=None, color_count=21):
    """
    Generates a dictionary of colors from a specified colormap, using either a provided custom level range or a default continuous range.
    """
    # Determine the colormap
    colormap_name = parameters.get('colormap', 'viridis')
    cmap = plt.get_cmap(colormap_name)

    # Create levels
    levels = create_levels(custom_levels, color_count)

    # Generate colors for each level
    normalized_levels = np.interp(levels, (min(levels), max(levels)), (0, 1))
    colors = [cmap(level) for level in normalized_levels]
    hex_colors = [matplotlib.colors.rgb2hex(color) for color in colors]

    # Create dictionary with formatted level keys
    custom_color_dict = {f"{level:.2f}": color for level, color in zip(levels, hex_colors)}

    return custom_color_dict