import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from IPython.core.display import HTML, display_html

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

def get_colormap(color_name='viridis', custom_levels=None, color_count=21, decimals=2):
    """
    Generates a dictionary of colors from a specified colormap, using either a provided custom level range or a default continuous range.
    """
    # Determine the colormap
    colormap_name = color_name
    cmap = plt.get_cmap(colormap_name)

    # Create levels
    levels = create_levels(custom_levels, color_count)

    # Generate colors for each level
    normalized_levels = np.interp(levels, (min(levels), max(levels)), (0, 1))
    colors = [cmap(level) for level in normalized_levels]
    hex_colors = [matplotlib.colors.rgb2hex(color) for color in colors]

    # Create list of levels and colors
    format_string = f"{{:.{decimals}f}}"
    custom_color_array = [[float(format_string.format(level)), color] for level, color in zip(levels, hex_colors)]

    return custom_color_array

def display_colormap_as_html(color_array):
    """
    Displays a colormap as HTML content.
    """
    # Create HTML content
    html_content = '<div style="display: flex;">'
    for level, color in color_array:
        html_content += f'<div style="background-color: {color}; width: 50px; height: 50px;" title="{level}"></div>'
    html_content += '</div>'

    # Display the HTML content in the notebook
    display_html(HTML(html_content))