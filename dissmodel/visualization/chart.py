from __future__ import annotations

import io
from typing import Any, Optional

import matplotlib.pyplot as plt
import matplotlib.figure
import matplotlib.axes

from dissmodel.core import Model
from dissmodel.visualization._utils import is_interactive_backend, is_notebook


# ---------------------------------------------------------------------------
# Decorator
# ---------------------------------------------------------------------------

def track_plot(
    label: str,
    color: str,
    plot_type: str = "line",
) -> Any:
    """
    Class decorator that registers an attribute for live plotting.

    Parameters
    ----------
    label : str
        Display label and lookup key for the tracked attribute.
    color : str
        Matplotlib-compatible color string (e.g. ``"red"``, ``"#ff0000"``).
    plot_type : str, optional
        Plot style, by default ``"line"``.

    Returns
    -------
    type
        The decorated class with ``_plot_info`` populated.

    Examples
    --------
    >>> @track_plot(label="Infected", color="red")
    ... class SIR(Model):
    ...     infected: int = 0
    """
    def decorator(cls: type) -> type:
        if not hasattr(cls, "_plot_info"):
            cls._plot_info = {}  # type: ignore[attr-defined]
        cls._plot_info[label.lower()] = {  # type: ignore[attr-defined]
            "plot_type": plot_type,
            "label": label,
            "color": color,
            "data": [],
        }
        return cls
    return decorator


# ---------------------------------------------------------------------------
# Chart model
# ---------------------------------------------------------------------------

class Chart(Model):
    """
    Simulation model that renders a live time-series chart.

    Extends :class:`~dissmodel.core.Model` and redraws the chart at every
    time step. Supports three rendering targets:

    - **Streamlit** — pass a ``plot_area`` (``st.empty()``).
    - **Jupyter** — detected automatically via :func:`is_notebook`.
    - **Matplotlib window** — fallback for plain Python scripts.

    Parameters
    ----------
    select : list of str, optional
        Subset of labels to plot. If ``None``, all tracked variables are shown.
    pause : bool, optional
        If ``True``, call ``plt.pause()`` after each update, by default ``True``.
        Required for live updates outside notebooks.
    plot_area : any, optional
        Streamlit ``st.empty()`` placeholder, by default ``None``.
    show_legend : bool, optional
        Whether to display the plot legend, by default ``True``.
    show_grid : bool, optional
        Whether to display the plot grid, by default ``False``.
    title : str, optional
        Chart title, by default ``"Variable History"``.

    Examples
    --------
    >>> env = Environment(end_time=30)
    >>> Chart(show_legend=True, show_grid=True, title="SIR Model")
    >>> env.run()
    """

    fig: matplotlib.figure.Figure
    ax: matplotlib.axes.Axes
    select: Optional[list[str]]
    interval: int
    time_points: list[float]
    pause: bool
    plot_area: Any
    show_legend: bool
    show_grid: bool
    title: str

    def setup(
        self,
        select: Optional[list[str]] = None,
        pause: bool = True,
        plot_area: Any = None,
        show_legend: bool = True,
        show_grid: bool = False,
        title: str = "Variable History",
    ) -> None:
        """
        Configure the chart.

        Called automatically by salabim during component initialisation.

        Parameters
        ----------
        select : list of str, optional
            Subset of labels to plot. If ``None``, all tracked variables
            are shown.
        pause : bool, optional
            If ``True``, call ``plt.pause()`` after each update,
            by default ``True``.
        plot_area : any, optional
            Streamlit ``st.empty()`` placeholder, by default ``None``.
        show_legend : bool, optional
            Whether to display the plot legend, by default ``True``.
        show_grid : bool, optional
            Whether to display the plot grid, by default ``False``.
        title : str, optional
            Chart title, by default ``"Variable History"``.
        """
        self.select = select
        self.interval = 1
        self.time_points = []
        self.pause = pause
        self.plot_area = plot_area
        self.show_legend = show_legend
        self.show_grid = show_grid
        self.title = title

        if not is_notebook():
            self.fig, self.ax = plt.subplots()
            self.ax.set_xlabel("Time")
            self.ax.set_title(self.title)

    def execute(self) -> None:
        """
        Redraw the chart for the current simulation time step.

        Raises
        ------
        RuntimeError
            If no interactive matplotlib backend is detected and the code is
            not running in a notebook or Streamlit context.
        """
        if is_notebook():
            from IPython.display import clear_output
            clear_output(wait=True)
            self.fig, self.ax = plt.subplots()
            self.ax.set_xlabel("Time")
            self.ax.set_title(self.title)

        plt.sca(self.ax)
        self.time_points.append(self.env.now())

        plot_metadata: dict[str, Any] = getattr(self.env, "_plot_metadata", {})

        self.ax.clear()
        self.ax.set_xlabel("Time")
        self.ax.set_title(self.title)

        for label, info in plot_metadata.items():
            if self.select is None or label in self.select:
                self.ax.plot(info["data"], label=label, color=info["color"])

        if self.show_grid:
            self.ax.grid(True)

        if self.show_legend:
            self.ax.legend()

        self.ax.relim()
        self.ax.autoscale_view()
        plt.tight_layout()
        plt.draw()

        if self.plot_area is not None:
            self.plot_area.pyplot(self.fig)
        elif is_notebook():
            from IPython.display import display, Image
            buf = io.BytesIO()
            self.fig.savefig(buf, format="png")
            buf.seek(0)
            display(Image(data=buf.read()))
            plt.close(self.fig)
        elif self.pause:
            if is_interactive_backend():
                plt.pause(0.1)
                if self.env.now() == self.env.end_time:
                    plt.show()
            else:
                raise RuntimeError(
                    "No interactive matplotlib backend detected. "
                    "On Linux, install tkinter:\n\n"
                    "    sudo apt install python3-tk\n"
                )

