from __future__ import annotations

from typing import Any, ClassVar, Optional


class Environment:
    """
    Simulation environment with support for a custom time window.

    Manages the simulation clock and coordinates the execution of all
    registered :class:`~dissmodel.core.Model` instances.

    Parameters
    ----------
    start_time : float, optional
        Simulation start time, by default 0.
    end_time : float, optional
        Simulation end time. Can also be set via ``till`` in :meth:`run`.

    Examples
    --------
    >>> env = Environment(start_time=0, end_time=10)
    >>> env.start_time
    0
    >>> env.end_time
    10
    """

    _current: ClassVar[Optional[Environment]] = None

    def __init__(
        self,
        start_time: float = 0,
        end_time: Optional[float] = None,
    ) -> None:
        self.start_time = start_time
        self.end_time = end_time
        self._now: float = start_time
        self._models: list[Any] = []
        self._plot_metadata: dict[str, Any] = {}
        Environment._current = self

    # ------------------------------------------------------------------
    # Clock
    # ------------------------------------------------------------------

    def now(self) -> float:
        """
        Return the current simulation time.

        Returns
        -------
        float
            Current simulation time.

        Examples
        --------
        >>> env = Environment(start_time=5)
        >>> env.now()
        5
        """
        return self._now

    # ------------------------------------------------------------------
    # Model registration
    # ------------------------------------------------------------------

    def _register(self, model: Any) -> None:
        """
        Register a model to be executed during the simulation.

        Called automatically by :class:`~dissmodel.core.Model.__init__`.

        Parameters
        ----------
        model : Model
            The model instance to register.
        """
        self._models.append(model)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def run(self, till: Optional[float] = None) -> None:
        """
        Run the simulation over the configured time window.

        Executes all registered models in time-step order. On each tick,
        every model whose next scheduled time is less than or equal to the
        current simulation time has its :meth:`~dissmodel.core.Model.execute`
        method called. The clock then advances to the nearest pending event.

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
            pass
        else:
            raise ValueError(
                "Provide 'till' or set 'end_time' before calling run()."
            )

        duration = self.end_time - self.start_time
        print(
            f"Running from {self.start_time} to {self.end_time} "
            f"(duration: {duration})"
        )

        # Initialise next-execution time for every registered model
        for model in self._models:
            model._next_time = model.start_time

        self._now = self.start_time

        while self._now < self.end_time:
            for model in self._models:
                if (
                    model._next_time <= self._now
                    and self._now < model.end_time
                ):
                    model.pre_execute()
                    model.execute()
                    model.post_execute()
                    model._next_time = self._now + model._step

            # Advance clock to the nearest pending event
            pending = [
                m._next_time
                for m in self._models
                if m._next_time < self.end_time
            ]
            if not pending:
                break
            self._now = min(pending)

    def reset(self) -> None:
        """
        Reset the clock and clear accumulated plot data.

        Called automatically at the start of :meth:`run` to ensure the
        environment starts fresh on each simulation run.

        Examples
        --------
        >>> env = Environment(start_time=0, end_time=10)
        >>> env._plot_metadata = {"x": {"data": [1, 2, 3]}}
        >>> env.reset()
        >>> env._plot_metadata["x"]["data"]
        []
        """
        self._now = self.start_time
        for item in self._plot_metadata.values():
            item["data"].clear()
