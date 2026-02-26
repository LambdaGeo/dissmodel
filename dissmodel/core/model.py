from __future__ import annotations

import math
from typing import Any

import salabim as sim


class Model(sim.Component):
    """
    Base class for simulation models backed by a salabim Component.

    Provides a time-stepped execution loop and automatic tracking of
    attributes marked for plotting via the :func:`~dissmodel.visualization.track_plot`
    decorator.

    Parameters
    ----------
    step : float, optional
        Time increment between successive :meth:`execute` calls, by default 1.
    start_time : float, optional
        Time at which the model starts executing, by default 0.
    end_time : float, optional
        Time at which the model stops executing, by default ``math.inf``.
    name : str, optional
        Component name, by default ``""``.
    *args :
        Extra positional arguments forwarded to :class:`salabim.Component`.
    **kwargs :
        Extra keyword arguments forwarded to :class:`salabim.Component`.

    Examples
    --------
    >>> class MyModel(Model):
    ...     def execute(self):
    ...         pass
    >>> env = Environment()
    >>> model = MyModel(step=1, start_time=0, end_time=5)
    >>> model.start_time
    0
    >>> model.end_time
    5
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
        salabim process loop.

        Waits until ``start_time``, then calls :meth:`execute` every
        ``step`` time units until ``end_time``.
        """
        if self.env.now() < self.start_time:
            self.hold(self.start_time - self.env.now())

        while self.env.now() < self.end_time:
            self.execute()
            self.hold(self._step)

    def execute(self) -> None:
        """
        Called once per time step.

        Override in subclasses to define model behaviour.
        """
        pass

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Intercept attribute assignment to record values marked for plotting.

        If the class defines ``_plot_info`` (via the
        :func:`~dissmodel.visualization.track_plot` decorator) and ``name``
        matches a tracked attribute, the value is appended to the plot data
        buffer and registered in ``env._plot_metadata``.

        Parameters
        ----------
        name : str
            Attribute name being set.
        value : Any
            Value being assigned.
        """
        cls = self.__class__

        if hasattr(cls, "_plot_info") and name.lower() in cls._plot_info:
            plot_info: dict[str, Any] = cls._plot_info[name.lower()]
            plot_info["data"].append(value)

            if not hasattr(self.env, "_plot_metadata"):
                self.env._plot_metadata = {}

            if plot_info["label"] not in self.env._plot_metadata:
                self.env._plot_metadata[plot_info["label"]] = plot_info

        super().__setattr__(name, value)
