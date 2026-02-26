from __future__ import annotations

from dissmodel.core import Model
from dissmodel.visualization import track_plot


@track_plot("X", "blue")
@track_plot("Y", "orange")
@track_plot("Z", "red")
class Lorenz(Model):
    """
    Lorenz system — deterministic chaos model.

    Models the Lorenz attractor, a system of three coupled ordinary
    differential equations originally derived from atmospheric convection.
    Despite being fully deterministic, the system exhibits chaotic
    behavior: tiny differences in initial conditions lead to vastly
    different trajectories over time.

    Parameters
    ----------
    x : float, optional
        Initial value of the X variable, by default 1.0.
    y : float, optional
        Initial value of the Y variable, by default 1.0.
    z : float, optional
        Initial value of the Z variable, by default 1.0.
    delta : float, optional
        Integration time step (Euler method), by default 0.01.
        Smaller values increase accuracy but require more steps.
    sigma : float, optional
        Prandtl number — controls the rate of rotation, by default 10.0.
    rho : float, optional
        Rayleigh number — controls convection intensity, by default 28.0.
    beta : float, optional
        Geometric factor, by default 8/3.

    Notes
    -----
    The ``@track_plot`` decorators register ``x``, ``y``, and ``z``
    for automatic live plotting. Any :class:`~dissmodel.visualization.Chart`
    connected to the same environment will plot all three variables at
    every step without any extra configuration.

    The system is integrated using the forward Euler method:

    .. math::

        \\dot{x} = \\sigma (y - x)

        \\dot{y} = x (\\rho - z) - y

        \\dot{z} = x y - \\beta z

    Examples
    --------
    >>> from dissmodel.core import Environment
    >>> env = Environment(end_time=3000)
    >>> model = Lorenz()
    >>> env.run()
    """

    #: Current value of the X variable.
    x: float

    #: Current value of the Y variable.
    y: float

    #: Current value of the Z variable.
    z: float

    #: Integration time step.
    delta: float

    #: Prandtl number.
    sigma: float

    #: Rayleigh number.
    rho: float

    #: Geometric factor.
    beta: float

    def setup(
        self,
        x: float = 1.0,
        y: float = 1.0,
        z: float = 1.0,
        delta: float = 0.01,
        sigma: float = 10.0,
        rho: float = 28.0,
        beta: float = 8.0 / 3.0,
    ) -> None:
        """
        Configure the model parameters.

        Parameters
        ----------
        x : float, optional
            Initial value of X, by default 1.0.
        y : float, optional
            Initial value of Y, by default 1.0.
        z : float, optional
            Initial value of Z, by default 1.0.
        delta : float, optional
            Integration time step, by default 0.01.
        sigma : float, optional
            Prandtl number, by default 10.0.
        rho : float, optional
            Rayleigh number, by default 28.0.
        beta : float, optional
            Geometric factor, by default 8/3.
        """
        self.x     = x
        self.y     = y
        self.z     = z
        self.delta = delta
        self.sigma = sigma
        self.rho   = rho
        self.beta  = beta

    def execute(self) -> None:
        """
        Advance the system by one time step using the Euler method.

        Computes the derivatives from the Lorenz equations and updates
        x, y, z by the integration step :attr:`delta`.
        """
        dx = self.sigma * (self.y - self.x)
        dy = self.x * (self.rho - self.z) - self.y
        dz = self.x * self.y - self.beta * self.z

        self.x += self.delta * dx
        self.y += self.delta * dy
        self.z += self.delta * dz


__all__ = ["Lorenz"]
