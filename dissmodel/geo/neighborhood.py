from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional, Type, Union

import geopandas as gpd
from libpysal.weights import W

# A strategy is any libpysal weight class that implements from_dataframe,
# e.g. Queen, Rook — we type it as the class itself, not an instance.
StrategyType = Type[W]
NeighborsDict = dict[Any, list[Any]]


def attach_neighbors(
    gdf: gpd.GeoDataFrame,
    strategy: Optional[StrategyType] = None,
    neighbors_dict: Optional[Union[NeighborsDict, str]] = None,
    *args: Any,
    **kwargs: Any,
) -> gpd.GeoDataFrame:
    """
    Attach neighbors to a GeoDataFrame using a neighborhood strategy or a
    precomputed neighbors mapping.

    Mutates and returns the GeoDataFrame with a '_neighs' column where each
    cell holds the list of neighbor indices.

    Args:
        gdf:            Input GeoDataFrame.
        strategy:       A libpysal weight class (e.g. Queen, Rook) whose
                        ``from_dataframe`` class method will be called.
        neighbors_dict: Either a ``{id: [neighbor_ids]}`` mapping or a path
                        to a JSON file with the same structure.
        *args:          Extra positional arguments forwarded to
                        ``strategy.from_dataframe``.
        **kwargs:       Extra keyword arguments forwarded to
                        ``strategy.from_dataframe``.

    Returns:
        The same GeoDataFrame with the '_neighs' column added.

    Raises:
        ValueError: If ``neighbors_dict`` is neither a dict nor a valid JSON
                    file path, or if neither ``strategy`` nor
                    ``neighbors_dict`` is provided.
    """
    resolved: Optional[NeighborsDict] = _resolve_neighbors_dict(neighbors_dict)

    w: W
    if resolved is not None:
        w = W(resolved)
    elif strategy is not None:
        w = strategy.from_dataframe(gdf, *args, **kwargs)
    else:
        raise ValueError("Provide either `strategy` or `neighbors_dict`.")

    gdf["_neighs"] = gdf.index.map(lambda idx: w.neighbors.get(idx, []))
    return gdf


def _resolve_neighbors_dict(
    neighbors_dict: Optional[Union[NeighborsDict, str]],
) -> Optional[NeighborsDict]:
    """
    Resolve ``neighbors_dict`` to a plain dict, loading from JSON if needed.

    Args:
        neighbors_dict: A dict, a path string to a JSON file, or None.

    Returns:
        A resolved dict, or None if the input was None.

    Raises:
        ValueError: If the value is not a dict, None, or a valid JSON file path.
    """
    if neighbors_dict is None:
        return None
    if isinstance(neighbors_dict, dict):
        return neighbors_dict
    if isinstance(neighbors_dict, str) and Path(neighbors_dict).is_file():
        with open(neighbors_dict) as f:
            return json.load(f)
    raise ValueError(
        "`neighbors_dict` must be a dictionary or a path to a JSON file."
    )


