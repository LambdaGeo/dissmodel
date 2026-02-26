
from __future__ import annotations

from dissmodel.core import Model
from dissmodel.visualization import track_plot


@track_plot("Population", "green")
class PopulationGrowth(Model):
    """
    Exponential population growth model with variable growth rate.

    Models a population that grows at a rate that itself changes over
    time. This allows simulating both accelerating and decelerating
    growth depending on :attr:`growth_change`.

    Parameters
    ----------
    population : float, optional
        Initial population size, by default 60.
    growth : float, optional
        Initial growth rate (e.g. 0.5 = 50% per step), by default 0.5.
    growth_change : float, optional
        Multiplicative factor applied to the growth rate each step.
        Values > 1 accelerate growth, values < 1 decelerate it,
        by default 1.0 (constant growth rate).

    Notes
    -----
    The ``@track_plot`` decorator registers ``population`` for automatic
    live plotting. Any :class:`~dissmodel.visualization.Chart` connected
    to the same environment will plot it at every step without any extra
    configuration.

    The update equations at each step are:

    .. math::

        P_{t+1} = P_t \\times (1 + r_t)

        r_{t+1} = r_t \\times c

    Where :math:`P` is population, :math:`r` is growth rate and
    :math:`c` is :attr:`growth_change`.

    Examples
    --------
    >>> from dissmodel.core import Environment
    >>> env = Environment(end_time=20)
    >>> model = PopulationGrowth()
    >>> env.run()
    """

    #: Current population size.
    population: float

    #: Current growth rate.
    growth: float

    #: Multiplicative factor applied to the growth rate each step.
    growth_change: float

    def setup(
        self,
        population: float = 60.0,
        growth: float = 0.5,
        growth_change: float = 1.0,
    ) -> None:
        """
        Configure the model parameters.

        Parameters
        ----------
        population : float, optional
            Initial population size, by default 60.
        growth : float, optional
            Initial growth rate, by default 0.5.
        growth_change : float, optional
            Multiplicative factor applied to the growth rate each step,
            by default 1.0.
        """
        self.population    = population
        self.growth        = growth
        self.growth_change = growth_change

    def execute(self) -> None:
        """
        Advance the model by one time step.

        Updates the population and growth rate according to the
        variable-rate exponential growth equations.
        """
        self.population *= (1 + self.growth)
        self.growth     *= self.growth_change


__all__ = ["PopulationGrowth"]
