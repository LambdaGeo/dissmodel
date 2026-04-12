from __future__ import annotations

from dissmodel.core import Model
from dissmodel.visualization import track_plot


@track_plot("Prey", "green")
@track_plot("Predator", "red")
class PredatorPrey(Model):
    """
    Lotka-Volterra predator-prey model.

    Models the dynamic interaction between a prey population and a
    predator population. Prey grow exponentially in the absence of
    predators; predators decline without prey. Their interaction drives
    cyclic oscillations in both populations.

    Parameters
    ----------
    predator : float, optional
        Initial predator population, by default 40.
    prey : float, optional
        Initial prey population, by default 1000.
    prey_growth : float, optional
        Intrinsic prey growth rate, by default 0.08.
    prey_death_pred : float, optional
        Rate at which predators kill prey per encounter, by default 0.001.
    pred_death : float, optional
        Intrinsic predator death rate, by default 0.02.
    pred_growth_kills : float, optional
        Rate at which predators reproduce per kill, by default 0.00002.

    Notes
    -----
    The ``@track_plot`` decorators register ``prey`` and ``predator``
    for automatic live plotting. Any :class:`~dissmodel.visualization.Chart`
    connected to the same environment will plot both variables at every
    step without any extra configuration.

    The update equations follow the discrete Lotka-Volterra model:

    .. math::

        P_{t+1} = P_t + r_P \\cdot P_t - d_{PP} \\cdot P_t \\cdot Q_t

        Q_{t+1} = Q_t - d_Q \\cdot Q_t + g_Q \\cdot P_t \\cdot Q_t

    Where :math:`P` is prey, :math:`Q` is predator.

    Examples
    --------
    >>> from dissmodel.core import Environment
    >>> env = Environment(end_time=100)
    >>> model = PredatorPrey()
    >>> env.run()
    """

    #: Current predator population.
    predator: float

    #: Current prey population.
    prey: float

    #: Intrinsic prey growth rate.
    prey_growth: float

    #: Rate at which predators kill prey per encounter.
    prey_death_pred: float

    #: Intrinsic predator death rate.
    pred_death: float

    #: Rate at which predators reproduce per kill.
    pred_growth_kills: float

    def setup(
        self,
        predator: float = 40.0,
        prey: float = 1000.0,
        prey_growth: float = 0.08,
        prey_death_pred: float = 0.001,
        pred_death: float = 0.02,
        pred_growth_kills: float = 0.00002,
    ) -> None:
        """
        Configure the model parameters.

        Parameters
        ----------
        predator : float, optional
            Initial predator population, by default 40.
        prey : float, optional
            Initial prey population, by default 1000.
        prey_growth : float, optional
            Intrinsic prey growth rate, by default 0.08.
        prey_death_pred : float, optional
            Rate at which predators kill prey per encounter,
            by default 0.001.
        pred_death : float, optional
            Intrinsic predator death rate, by default 0.02.
        pred_growth_kills : float, optional
            Rate at which predators reproduce per kill,
            by default 0.00002.
        """
        self.predator       = predator
        self.prey           = prey
        self.prey_growth    = prey_growth
        self.prey_death_pred = prey_death_pred
        self.pred_death     = pred_death
        self.pred_growth_kills = pred_growth_kills

    def execute(self) -> None:
        """
        Advance the model by one time step.

        Updates prey and predator populations according to the
        discrete Lotka-Volterra equations.
        """
        self.prey += (
            self.prey_growth * self.prey
            - self.prey_death_pred * self.prey * self.predator
        )
        self.predator += (
            -self.pred_death * self.predator
            + self.pred_growth_kills * self.prey * self.predator
        )


__all__ = ["PredatorPrey"]
