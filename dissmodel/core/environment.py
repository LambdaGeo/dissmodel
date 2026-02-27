from __future__ import annotations

from typing import Any, Optional

import salabim as sim


class Environment(sim.Environment):
    """
    Simulation environment with support for a custom time window.

    Extends :class:`salabim.Environment` with ``start_time`` and ``end_time``
    to define the simulation boundaries explicitly.

    Parameters
    ----------
    start_time : float, optional
        Simulation start time, by default 0.
    end_time : float, optional
        Simulation end time. Can also be set via ``till`` in :meth:`run`.
    *args :
        Extra positional arguments forwarded to :class:`salabim.Environment`.
    **kwargs :
        Extra keyword arguments forwarded to :class:`salabim.Environment`.

    Examples
    --------
    >>> env = Environment(start_time=0, end_time=10)
    >>> env.start_time
    0
    >>> env.end_time
    10
    """

    def __init__(
        self,
        start_time: float = 0,
        end_time: Optional[float] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        kwargs.pop("animation", None)
        kwargs.pop("trace", False)
        super().__init__(*args, trace=False, **kwargs)
        self.start_time = start_time
        self.end_time = end_time

    def run(self, till: Optional[float] = None) -> None:
        """
        Run the simulation over the configured time window.

        Parameters
        ----------
        till : float, optional
            Duration to run from ``start_time``. If provided, overrides
            ``end_time``. If omitted, ``end_time`` must be set.

        Raises
        ------
        ValueError
            If neither ``till`` nor ``end_time`` is defined.

        Examples
        --------
        >>> env = Environment(start_time=0, end_time=10)
        >>> env.run()
        Running from 0 to 10 (duration: 10)
        """
        self.reset()

        if till is not None:
            self.end_time = self.start_time + till
        elif self.end_time is not None:
            till = self.end_time - self.start_time
        else:
            raise ValueError("Provide 'till' or set 'end_time' before calling run().")

        print(f"Running from {self.start_time} to {self.end_time} (duration: {till})")
        super().run(till=till)

    def reset(self) -> None:
        """
        Clear accumulated plot data.

        This method is called automatically at the start of :meth:`run` to
        ensure charts start fresh on each simulation run.

        Examples
        --------
        >>> env = Environment()
        >>> env._plot_metadata = {"x": {"data": [1, 2, 3]}}
        >>> env.reset()
        >>> env._plot_metadata["x"]["data"]
        []
        """
        if hasattr(self, "_plot_metadata"):
            for item in self._plot_metadata.values():
                item["data"].clear()

    def now(self) -> float:
        """
        Return the current simulation time adjusted by ``start_time``.

        Returns
        -------
        float
            Current time as ``salabim.now() + start_time``.

        Examples
        --------
        >>> env = Environment(start_time=5)
        >>> env.now()
        5.0
        """
        return super().now() + self.start_time
