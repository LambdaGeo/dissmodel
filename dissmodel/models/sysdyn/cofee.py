from __future__ import annotations

from dissmodel.core import Model
from dissmodel.visualization import track_plot


@track_plot("Temperature", "blue")
class Coffee(Model):
    """
    Newton's Law of Cooling model.

    Simulates the cooling of a hot beverage towards room temperature.
    At each step, the temperature decreases proportionally to the
    difference between the current temperature and room temperature.

    Parameters
    ----------
    temperature : float, optional
        Initial temperature of the beverage in degrees, by default 80.
    room_temperature : float, optional
        Ambient room temperature in degrees, by default 20.
    cooling_rate : float, optional
        Proportionality constant controlling cooling speed,
        by default 0.1.

    Notes
    -----
    The ``@track_plot`` decorator registers ``temperature`` for automatic
    live plotting. Any :class:`~dissmodel.visualization.Chart` connected
    to the same environment will plot it at every step without any extra
    configuration.

    The temperature update at each step follows Newton's Law of Cooling:

    .. math::

        T_{t+1} = T_t - k \\times (T_t - T_{room})

    Examples
    --------
    >>> from dissmodel.core import Environment
    >>> env = Environment(end_time=30)
    >>> coffee = Coffee()
    >>> env.run()
    """

    #: Current temperature of the beverage.
    temperature: float

    #: Ambient room temperature.
    room_temperature: float

    #: Proportionality constant controlling cooling speed.
    cooling_rate: float

    def setup(
        self,
        temperature: float = 80.0,
        room_temperature: float = 20.0,
        cooling_rate: float = 0.1,
    ) -> None:
        """
        Configure the model parameters.

        Parameters
        ----------
        temperature : float, optional
            Initial temperature of the beverage, by default 80.0.
        room_temperature : float, optional
            Ambient room temperature, by default 20.0.
        cooling_rate : float, optional
            Proportionality constant controlling cooling speed,
            by default 0.1.
        """
        self.temperature = temperature
        self.room_temperature = room_temperature
        self.cooling_rate = cooling_rate

    def execute(self) -> None:
        """
        Advance the model by one time step.

        Updates the temperature according to Newton's Law of Cooling.
        """
        self.temperature -= self.cooling_rate * (self.temperature - self.room_temperature)


__all__ = ["Coffee"]
