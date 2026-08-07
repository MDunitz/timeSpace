"""Static configuration for the reference-object explorer."""

# Match main figure axis ranges (from plotting.py's create_space_time_figure)
# TODO: move to constants.py so plotting.py and the explorer share a single source
X_RANGE = (1e-3, 1e12)
Y_RANGE = (1e-22, 1e20)

# Number of vertices per half-ellipse for reference objects.
# Main figure uses 1000; 100 keeps the static HTML under 1 MB of data
# while still rendering smooth curves on a log-log plot.
EXPLORER_N_POINTS = 100

# Category colors — explorer-specific (main figure uses per-process colors from CSV)
CATEGORY_COLORS = {
    "Molecular": "#33CCCC",
    "Cellular": "#009999",
    "Organism": "#0F793D",
    "Ecosystem": "#6ABD45",
    "Ocean": "#006666",
    "Atmosphere": "#99CC33",
    "Geographic": "#669933",
    "Geological": "#CC9933",
    "Human-built": "#FF9900",
    "Planetary": "#996600",
}

FONT_SIZE = "11pt"
LABEL_FONT_SIZE = "9pt"
