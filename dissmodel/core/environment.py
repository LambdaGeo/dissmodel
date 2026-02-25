from __future__ import annotations

from typing import Any, Optional

import salabim as sim


class Environment(sim.Environment):
    """
    Extended simulation environment with support for a custom start time.

    Works as a standard salabim environment, but accepts ``start_time`` and
    ``end_time`` to define the simulation window explicitly.

    Args:
        start_time: Simulation start time (default: 0).
        end_time:   Simulation end time. Can also be set via ``till`` in
                    :meth:`run`.
        *args:      Extra positional arguments forwarded to
                    :class:`sim.Environment`.
        **kwargs:   Extra keyword arguments forwarded to
                    :class:`sim.Environment`.
    """

    def __init__(
        self,
        start_time: float = 0,
        end_time: Optional[float] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.start_time = start_time
        self.end_time = end_time

    def run(self, till: Optional[float] = None) -> None:
        """
        Run the simulation using the configured time window.

        Args:
            till: Duration to run from ``start_time``. If provided, overrides
                  ``end_time``. If omitted, ``end_time`` must be set.

        Raises:
            ValueError: If neither ``till`` nor ``end_time`` is defined.
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
        """Clear accumulated plot data, if any."""
        if hasattr(self, "_plot_metadata"):
            for item in self._plot_metadata.values():
                item["data"].clear()

    def now(self) -> float:
        """
        Return the current simulation time adjusted by ``start_time``.

        Returns:
            Current time as ``salabim.now() + start_time``.
        """
        return super().now() + self.start_time
