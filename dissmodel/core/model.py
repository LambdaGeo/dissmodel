from __future__ import annotations

import math
from typing import Any

import salabim as sim


class Model(sim.Component):
    """
    Base class for simulation models backed by a salabim Component.

    Args:
        step:       Time increment between successive :meth:`execute` calls.
        start_time: Time at which the model starts executing.
        end_time:   Time at which the model stops executing.
        name:       Optional component name.
        *args:      Extra positional arguments forwarded to
                    :class:`sim.Component`.
        **kwargs:   Extra keyword arguments forwarded to
                    :class:`sim.Component`.
    """

    def __init__(
        self,
        step: float = 1,
        start_time: float = 0,
        end_time: float = math.inf,
        name: str = "",
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._step = step
        self.start_time = start_time
        self.end_time = end_time

    def process(self) -> None:
        """
        salabim process loop: waits until ``start_time``, then calls
        :meth:`execute` every ``step`` time units until ``end_time``.
        """
        if self.env.now() < self.start_time:
            self.hold(self.start_time - self.env.now())

        while self.env.now() < self.end_time:
            self.execute()
            self.hold(self._step)

    def execute(self) -> None:
        """
        Called once per time step. Override in subclasses to define behaviour.
        """
        pass

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Intercepts attribute assignment to record values that are marked for
        plotting via ``_plot_info`` on the class.
        """
        cls = self.__class__

        if hasattr(cls, "_plot_info") and name.lower() in cls._plot_info:
            plot_info: dict[str, Any] = cls._plot_info[name.lower()]
            plot_info["data"].append(value)

            if not hasattr(self.env, "_plot_metadata"):
                self.env._plot_metadata: dict[str, Any] = {}

            if plot_info["label"] not in self.env._plot_metadata:
                self.env._plot_metadata[plot_info["label"]] = plot_info

        super().__setattr__(name, value)


