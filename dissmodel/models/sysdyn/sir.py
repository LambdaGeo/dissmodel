from __future__ import annotations

from dissmodel.core import Model
from dissmodel.visualization import track_plot


@track_plot("Susceptible", "green")
@track_plot("Infected", "red")
@track_plot("Recovered", "blue")
class SIR(Model):
    """
    Deterministic SIR epidemiological model.

    Tracks the spread of an infectious disease through three compartments:
    susceptible, infected, and recovered. At each step, new infections and
    recoveries are computed based on contact rate, transmission probability,
    and disease duration.

    Parameters
    ----------
    susceptible : int, optional
        Initial number of susceptible individuals, by default 9998.
    infected : int, optional
        Initial number of infected individuals, by default 2.
    recovered : int, optional
        Initial number of recovered individuals, by default 0.
    duration : int, optional
        Average number of steps an individual remains infectious,
        by default 2.
    contacts : int, optional
        Average number of contacts per individual per step, by default 6.
    probability : float, optional
        Probability of transmission per contact with an infected individual,
        by default 0.25.

    Notes
    -----
    The ``@track_plot`` decorators register ``susceptible``, ``infected``,
    and ``recovered`` for automatic live plotting. Any
    :class:`~dissmodel.visualization.Chart` connected to the same environment
    will plot these variables at every step without any extra configuration.

    The force of infection at each step is computed as:

    .. math::

        \\alpha = contacts \\times probability

        \\Delta I = I \\times \\alpha \\times \\frac{S}{N}

        \\Delta R = \\frac{I}{duration}

    Examples
    --------
    >>> from dissmodel.core import Environment
    >>> env = Environment(end_time=30)
    >>> sir = SIR()
    >>> env.run()
    """

    #: Number of susceptible individuals.
    susceptible: float

    #: Number of infected individuals.
    infected: float

    #: Number of recovered individuals.
    recovered: float

    #: Average number of steps an individual remains infectious.
    duration: int

    #: Average number of contacts per individual per step.
    contacts: int

    #: Probability of transmission per contact.
    probability: float

    def setup(
        self,
        susceptible: int = 9998,
        infected: int = 2,
        recovered: int = 0,
        duration: int = 2,
        contacts: int = 6,
        probability: float = 0.25,
    ) -> None:
        """
        Configure the model parameters.

        Parameters
        ----------
        susceptible : int, optional
            Initial number of susceptible individuals, by default 9998.
        infected : int, optional
            Initial number of infected individuals, by default 2.
        recovered : int, optional
            Initial number of recovered individuals, by default 0.
        duration : int, optional
            Average number of steps an individual remains infectious,
            by default 2.
        contacts : int, optional
            Average number of contacts per individual per step,
            by default 6.
        probability : float, optional
            Probability of transmission per contact, by default 0.25.
        """
        self.susceptible = susceptible
        self.infected    = infected
        self.recovered   = recovered
        self.duration    = duration
        self.contacts    = contacts
        self.probability = probability

    def execute(self) -> None:
        """
        Advance the model by one time step.

        Computes new infections and recoveries, then updates the
        susceptible, infected, and recovered compartments.
        """
        total = self.susceptible + self.infected + self.recovered
        alpha = self.contacts * self.probability

        new_infected  = self.infected * alpha * (self.susceptible / total)
        new_recovered = self.infected / self.duration

        self.susceptible -= new_infected
        self.infected    += new_infected - new_recovered
        self.recovered   += new_recovered


__all__ = ["SIR"]
