from __future__ import annotations

import random
from typing import Any

from libpysal.weights import Queen

from dissmodel.geo import CellularAutomaton
from dissmodel.models.ca.fire_model import FireState


class FireModelProb(CellularAutomaton):
    """
    Probabilistic forest fire cellular automaton.

    Extends the basic fire model with two stochastic processes:

    - **Spontaneous combustion** — a forest cell can catch fire randomly,
      even without burning neighbors.
    - **Regrowth** — a burned cell can recover and become forest again.

    This creates a dynamic equilibrium between forest growth and fire,
    producing complex spatial patterns over time.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame with geometries and a ``state`` attribute.
    **kwargs :
        Extra keyword arguments forwarded to
        :class:`~dissmodel.geo.CellularAutomaton`.

    Examples
    --------
    >>> from dissmodel.geo import regular_grid
    >>> from dissmodel.core import Environment
    >>> gdf = regular_grid(dimension=(10, 10), resolution=1, attrs={"state": 0})
    >>> env = Environment(end_time=20)
    >>> fire = FireModelProb(gdf=gdf)
    """

    #: Probability of a forest cell spontaneously catching fire each step.
    prob_combustion: float

    #: Probability of a burned cell regrowing as forest each step.
    prob_regrowth: float

    def setup(
        self,
        prob_combustion: float = 0.001,
        prob_regrowth: float = 0.1,
    ) -> None:
        """
        Configure the model and build the neighborhood.

        Parameters
        ----------
        prob_combustion : float, optional
            Probability of spontaneous combustion per step, by default 0.001.
        prob_regrowth : float, optional
            Probability of regrowth from burned to forest per step,
            by default 0.1.
        """
        self.prob_combustion = prob_combustion
        self.prob_regrowth = prob_regrowth
        self.create_neighborhood(strategy=Queen, use_index=True)


    def rule(self, idx: Any) -> int:
        """
        Apply the probabilistic fire transition rule to cell ``idx``.

        Parameters
        ----------
        idx : any
            Index of the cell being evaluated.

        Returns
        -------
        int
            New state for the cell:

            - Forest → ``BURNING`` if a neighbor is burning, or with
              probability :attr:`prob_combustion`.
            - Forest → ``FOREST`` otherwise.
            - Burning → ``BURNED`` always.
            - Burned → ``FOREST`` with probability :attr:`prob_regrowth`,
              or ``BURNED`` otherwise.
        """
        state = self.gdf.loc[idx, self.state_attr]

        if state == FireState.FOREST:
            if (self.neighbor_values(idx, self.state_attr) == FireState.BURNING).any():
                return FireState.BURNING
            return (
                FireState.BURNING
                if random.random() <= self.prob_combustion
                else FireState.FOREST
            )

        if state == FireState.BURNING:
            return FireState.BURNED

        # BURNED
        return (
            FireState.FOREST
            if random.random() <= self.prob_regrowth
            else FireState.BURNED
        )


__all__ = ["FireModelProb"]