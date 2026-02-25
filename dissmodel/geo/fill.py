from __future__ import annotations

import random
from enum import Enum
from typing import Any, Callable, Optional, Union

import geopandas as gpd
import numpy as np
from affine import Affine
from rasterstats import zonal_stats


# ---------------------------------------------------------------------------
# Strategy enum
# ---------------------------------------------------------------------------

class FillStrategy(str, Enum):
    ZONAL_STATS = "zonal_stats"
    MIN_DISTANCE = "min_distance"
    RANDOM_SAMPLE = "random_sample"
    PATTERN = "pattern"


# ---------------------------------------------------------------------------
# Internal registry
# ---------------------------------------------------------------------------

_fill_strategies: dict[FillStrategy, Callable[..., Any]] = {}


def register_strategy(name: FillStrategy) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Register a fill strategy under the given name."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        _fill_strategies[name] = func
        return func
    return decorator


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

# Acceptable inputs for generate_sample:
#   list  → uniform random choice among items
#   dict  → either {"min": int, "max": int} or {option: weight, ...}
_SampleData = Union[list[Any], dict[str, Any]]


def _generate_sample(data: _SampleData, size: int = 1) -> list[Any]:
    """
    Draw ``size`` random samples from ``data``.

    Args:
        data: Either a list (uniform sampling) or a dict. Dict can be either
              ``{"min": int, "max": int}`` for integer ranges, or a mapping of
              ``{option: probability_weight}`` for weighted sampling.
        size: Number of samples to draw.

    Returns:
        List of sampled values.

    Raises:
        ValueError: If ``data`` is not a list or dict.
    """
    if isinstance(data, dict):
        if "min" in data and "max" in data:
            return [random.randint(data["min"], data["max"]) for _ in range(size)]
        options = list(data.keys())
        weights = list(data.values())
        return random.choices(options, weights=weights, k=size)

    if isinstance(data, list):
        return random.choices(data, k=size)

    raise ValueError("`data` must be a list or a dictionary.")


# ---------------------------------------------------------------------------
# Strategy implementations
# ---------------------------------------------------------------------------

@register_strategy(FillStrategy.PATTERN)
def _fill_pattern(
    gdf: gpd.GeoDataFrame,
    attr: str,
    pattern: list[list[Any]],
    start_x: int = 0,
    start_y: int = 0,
) -> None:
    """
    Fill a GeoDataFrame attribute using a 2-D pattern (regular grid).

    Args:
        gdf:     GeoDataFrame whose cells will be filled.
        attr:    Name of the attribute column to fill.
        pattern: 2-D list representing the pattern to apply.
        start_x: Initial offset in the x direction.
        start_y: Initial offset in the y direction.
    """
    w = len(pattern)
    h = len(pattern[0])
    for i in range(w):
        for j in range(h):
            idx = f"{start_x + i}-{start_y + j}"
            gdf.loc[idx, attr] = pattern[w - i - 1][j]


@register_strategy(FillStrategy.RANDOM_SAMPLE)
def _fill_random_sample(
    gdf: gpd.GeoDataFrame,
    attr: str,
    data: _SampleData,
    seed: Optional[int] = None,
) -> None:
    """
    Fill a GeoDataFrame attribute with random samples drawn from ``data``.

    Args:
        gdf:  GeoDataFrame to fill.
        attr: Name of the attribute column to fill.
        data: Sampling source — see :func:`_generate_sample`.
        seed: Optional random seed for reproducibility.
    """
    if seed is not None:
        random.seed(seed)
    gdf[attr] = _generate_sample(data, size=len(gdf))


@register_strategy(FillStrategy.ZONAL_STATS)
def _fill_zonal_stats(
    vectors: gpd.GeoDataFrame,
    raster_data: np.ndarray,
    affine: Affine,
    stats: list[str],
    prefix: str = "attr_",
    nodata: float = -999,
) -> None:
    """
    Fill a GeoDataFrame with zonal statistics computed from a raster.

    Args:
        vectors:     GeoDataFrame with the zones.
        raster_data: 2-D numpy array with raster values.
        affine:      Affine transform of the raster.
        stats:       Statistics to compute (e.g. ``["mean", "sum"]``).
        prefix:      Column name prefix for each statistic.
        nodata:      Value in the raster to treat as no-data.
    """
    stats_output: list[dict[str, Any]] = zonal_stats(
        vectors, raster_data, affine=affine, nodata=nodata, stats=stats
    )
    for stat in stats:
        vectors[f"{prefix}{stat}"] = [row[stat] for row in stats_output]


@register_strategy(FillStrategy.MIN_DISTANCE)
def _fill_min_distance(
    from_gdf: gpd.GeoDataFrame,
    to_gdf: gpd.GeoDataFrame,
    attr_name: str = "min_distance",
) -> None:
    """
    Fill each row in ``from_gdf`` with the minimum distance to any geometry
    in ``to_gdf``.

    Args:
        from_gdf:  GeoDataFrame whose rows will be annotated.
        to_gdf:    GeoDataFrame used as the distance target.
        attr_name: Name of the column to store the distances.
    """
    from_gdf[attr_name] = from_gdf.geometry.apply(
        lambda geom: to_gdf.geometry.distance(geom).min()
    )


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def fill(strategy: FillStrategy | str, **kwargs: Any) -> Any:
    """
    Execute a fill strategy by name.

    Args:
        strategy: A :class:`FillStrategy` value or its string equivalent.
        **kwargs: Arguments forwarded to the chosen strategy function.

    Returns:
        Whatever the strategy function returns (usually ``None``, as most
        strategies mutate the GeoDataFrame in place).

    Raises:
        ValueError: If ``strategy`` is not registered.
    """
    key = FillStrategy(strategy)
    if key not in _fill_strategies:
        raise ValueError(f"Unknown strategy: {strategy!r}")
    return _fill_strategies[key](**kwargs)


__all__ = ["fill", "FillStrategy", "register_strategy"]
