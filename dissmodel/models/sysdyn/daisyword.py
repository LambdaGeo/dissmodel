from __future__ import annotations

import math

from dissmodel.core import Model
from dissmodel.visualization import track_plot

# ---------------------------------------------------------------------------
# Physical constants
# ---------------------------------------------------------------------------

#: Stefan-Boltzmann constant (W/m²·K⁴).
SIGMA = 5.67e-8

#: Solar flux used in the Daisyworld model (W/m²).
SOLAR_FLUX = 3668.0

#: Heat transfer coefficient between planet surface and daisy patches (K⁴).
HEAT_TRANSFER_COEF = 2.06e9


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def daisy_growth_rate(temp_k: float) -> float:
    """
    Compute the daisy growth rate as a function of temperature.

    Parameters
    ----------
    temp_k : float
        Local temperature in Kelvin.

    Returns
    -------
    float
        Growth rate in [0, 1]. Zero outside the viable range (5°C – 40°C).
    """
    temp_c = temp_k - 273.0
    if 5.0 < temp_c < 40.0:
        return 1.0 - 0.003265 * (22.5 - temp_c) ** 2
    return 0.0


def planet_temperature(luminosity: float, albedo: float) -> float:
    """
    Compute the mean planetary temperature using the Stefan-Boltzmann law.

    Parameters
    ----------
    luminosity : float
        Relative solar luminosity (1.0 = current Sun).
    albedo : float
        Mean planetary albedo.

    Returns
    -------
    float
        Mean surface temperature in Kelvin.
    """
    return ((luminosity * SOLAR_FLUX * (1.0 - albedo)) / (4.0 * SIGMA)) ** 0.25


def local_temperature(
    planet_temp: float,
    planet_albedo: float,
    daisy_albedo: float,
) -> float:
    """
    Compute the local temperature near a daisy patch.

    Parameters
    ----------
    planet_temp : float
        Mean planetary temperature in Kelvin.
    planet_albedo : float
        Mean planetary albedo.
    daisy_albedo : float
        Albedo of the daisy patch.

    Returns
    -------
    float
        Local temperature in Kelvin near the daisy patch.
    """
    return (HEAT_TRANSFER_COEF * (planet_albedo - daisy_albedo) + planet_temp ** 4) ** 0.25


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

@track_plot("WhiteArea", "lightgray")
@track_plot("BlackArea", "black")
@track_plot("EmptyArea", "saddlebrown")
@track_plot("PlanetAlbedo", "blue")
@track_plot("AveTemp", "red")
@track_plot("DaisyArea", "green")
class Daisyworld(Model):
    """
    Daisyworld climate regulation model.

    A thought experiment by James Lovelock and Andrew Watson (1983)
    demonstrating that life can regulate planetary temperature through
    feedback mechanisms — without any intentional behavior.

    The planet is populated by two daisy species:

    - **White daisies** — high albedo, reflect sunlight, cool the planet.
    - **Black daisies** — low albedo, absorb sunlight, warm the planet.

    Each species grows when local temperature is within a viable range
    (5°C – 40°C) and dies at a constant rate. The balance between them
    maintains a stable planetary temperature across a wide range of
    solar luminosities.

    Parameters
    ----------
    sun_luminosity : float, optional
        Relative solar luminosity (1.0 = current Sun), by default 0.7.
    planet_area : float, optional
        Total normalized planet surface area, by default 1.0.
    white_area : float, optional
        Initial fraction covered by white daisies, by default 0.40.
    black_area : float, optional
        Initial fraction covered by black daisies, by default 0.273.
    white_albedo : float, optional
        Albedo of white daisies, by default 0.75.
    black_albedo : float, optional
        Albedo of black daisies, by default 0.25.
    soil_albedo : float, optional
        Albedo of bare soil, by default 0.5.
    decay_rate : float, optional
        Per-step death rate for both daisy species, by default 0.3.

    Notes
    -----
    The ``@track_plot`` decorators register all tracked variables for
    automatic live plotting. Any :class:`~dissmodel.visualization.Chart`
    connected to the same environment will plot them at every step.

    Examples
    --------
    >>> from dissmodel.core import Environment
    >>> env = Environment(end_time=50)
    >>> model = Daisyworld()
    >>> env.run()
    """

    #: Relative solar luminosity.
    sun_luminosity: float

    #: Total normalized planet surface area.
    planet_area: float

    #: Fraction covered by white daisies.
    white_area: float

    #: Fraction covered by black daisies.
    black_area: float

    #: Fraction of bare soil.
    empty_area: float

    #: Albedo of white daisies.
    white_albedo: float

    #: Albedo of black daisies.
    black_albedo: float

    #: Albedo of bare soil.
    soil_albedo: float

    #: Per-step death rate for both daisy species.
    decay_rate: float

    #: Computed mean planetary albedo.
    planet_albedo: float

    #: Computed mean planetary temperature (K).
    ave_temp: float

    #: Total daisy coverage (white + black).
    daisy_area: float

    def setup(
            self,
            sun_luminosity: float = 1.0,   # ← era 0.7
            planet_area: float = 1.0,
            white_area: float = 0.40,
            black_area: float = 0.273,
            white_albedo: float = 0.75,
            black_albedo: float = 0.25,
            soil_albedo: float = 0.5,
            decay_rate: float = 0.3,
        ) -> None:
        """
        Configure the model parameters and compute initial observables.

        Parameters
        ----------
        sun_luminosity : float, optional
            Relative solar luminosity, by default 0.7.
        planet_area : float, optional
            Total normalized planet surface area, by default 1.0.
        white_area : float, optional
            Initial white daisy coverage, by default 0.40.
        black_area : float, optional
            Initial black daisy coverage, by default 0.273.
        white_albedo : float, optional
            Albedo of white daisies, by default 0.75.
        black_albedo : float, optional
            Albedo of black daisies, by default 0.25.
        soil_albedo : float, optional
            Albedo of bare soil, by default 0.5.
        decay_rate : float, optional
            Per-step death rate for both species, by default 0.3.
        """
        self.sun_luminosity = sun_luminosity
        self.planet_area    = planet_area
        self.white_area     = white_area
        self.black_area     = black_area
        self.empty_area     = planet_area - (white_area + black_area)
        self.white_albedo   = white_albedo
        self.black_albedo   = black_albedo
        self.soil_albedo    = soil_albedo
        self.decay_rate     = decay_rate

        # Initial observables
        self.planet_albedo = self._compute_planet_albedo()
        self.ave_temp      = planet_temperature(self.sun_luminosity, self.planet_albedo)
        self.daisy_area    = self.white_area + self.black_area

    def _compute_planet_albedo(self) -> float:
        """Compute the mean planetary albedo from current surface coverage."""
        return (
            self.white_area  * self.white_albedo
            + self.black_area  * self.black_albedo
            + self.empty_area  * self.soil_albedo
        )

    def execute(self) -> None:
        """
        Advance the model by one time step.

        Updates planetary albedo and temperature, then applies growth
        and decay to both daisy populations.
        """
        # Update planetary observables
        self.planet_albedo = self._compute_planet_albedo()
        self.ave_temp      = planet_temperature(self.sun_luminosity, self.planet_albedo)

        # White daisies
        temp_white       = local_temperature(self.ave_temp, self.planet_albedo, self.white_albedo)
        white_growth     = daisy_growth_rate(temp_white) * self.empty_area
        self.white_area += self.white_area * (white_growth - self.decay_rate)

        # Black daisies
        temp_black       = local_temperature(self.ave_temp, self.planet_albedo, self.black_albedo)
        black_growth     = daisy_growth_rate(temp_black) * self.empty_area
        self.black_area += self.black_area * (black_growth - self.decay_rate)

        # Update derived areas
        self.empty_area = self.planet_area - (self.white_area + self.black_area)
        self.daisy_area = self.white_area + self.black_area


__all__ = ["Daisyworld"]
