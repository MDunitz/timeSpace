"""Dominant-energy taxonomy for colouring Stommel diagrams.

A process is tagged with the energy form that dominates it, which is a coarser
question than an energy budget: photosynthesis is Radiative even though the
products are chemical, and a paddlewheel is Mechanical even though the motor
draws electrical power. The tag answers "what has to be supplied for this to
happen", not "where does the energy end up".

The four-way split (Chemical / Radiative / Thermal / Mechanical) is empirical -
it is what the desert-farm dataset actually needed, and it is what
docs/build_desert_farm.py has been using since that figure was built. It is not
the classical kinetic/potential decomposition, which cuts across it: a mesoscale
eddy carries both and is Mechanical here.
"""

ENERGY_COLORS = {
    "Chemical": "#7A8C5C",  # olive — bonds, reactions, metabolism
    "Radiative": "#E5C16E",  # warm sand — photons, solar
    "Thermal": "#7B3F3F",  # deep rust — heat, evaporation, climate
    "Mechanical": "#4F6B82",  # slate — kinetic, mixing, pumping
}

# Legend order: roughly the order a photon's energy moves through a farm.
ENERGY_ORDER = ("Radiative", "Chemical", "Thermal", "Mechanical")

ENERGY_COLUMN = "Energy_type"


def validate_energy_types(df, column=ENERGY_COLUMN):
    """Return the energy tags in `df` that are not in the taxonomy.

    Empty return means every tag is known. Kept separate from
    `assign_energy_colors` so a caller can decide whether an unknown tag is a
    typo to fix or a category to add.
    """
    if column not in df.columns:
        raise ValueError(f"DataFrame has no {column!r} column; cannot colour by energy.")
    return sorted(set(df[column].dropna().unique()) - set(ENERGY_COLORS))


def assign_energy_colors(df, column=ENERGY_COLUMN, default=None):
    """Return a copy of `df` with a Color column mapped from its energy tags.

    Parameters
    ----------
    df : DataFrame
        Must carry `column`.
    column : str
        Energy tag column. Default 'Energy_type'.
    default : str or None
        Hex colour for tags outside the taxonomy. None raises instead, which is
        the right default: a silently grey process is worse than a stopped build.

    Returns
    -------
    DataFrame
        Copy with Color added or overwritten.
    """
    unknown = validate_energy_types(df, column=column)
    if unknown and default is None:
        raise ValueError(
            f"Unknown energy types {unknown}; expected one of {sorted(ENERGY_COLORS)}. "
            f"Pass default='#hex' to colour them anyway."
        )
    out = df.copy()
    colors = out[column].map(ENERGY_COLORS)
    # fillna(None) raises on pandas < 2.2; unknown tags already raised above when
    # default is None, so there is nothing to fill in that branch.
    out["Color"] = colors if default is None else colors.fillna(default)
    return out


def energy_types_present(df, column=ENERGY_COLUMN):
    """Return the taxonomy's energy types that appear in `df`, in legend order.

    Preserves ENERGY_ORDER rather than dataset order, so the legend is stable
    across datasets that happen to list processes in a different sequence.
    """
    present = set(df[column].dropna().unique())
    return [etype for etype in ENERGY_ORDER if etype in present]
