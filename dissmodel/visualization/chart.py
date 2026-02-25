from __future__ import annotations

import io
from typing import Any, Optional

import matplotlib.pyplot as plt
import matplotlib.figure
import matplotlib.axes

from dissmodel.core import Model


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_notebook() -> bool:
    """Return True if the code is running inside a Jupyter notebook."""
    try:
        from IPython import get_ipython
        return get_ipython().__class__.__name__ == "ZMQInteractiveShell"
    except Exception:
        return False


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

    Args:
        label:     Display label and key used to look up the attribute.
        color:     Matplotlib-compatible color string.
        plot_type: Plot style (currently only ``"line"`` is used).

    Returns:
        The decorated class with ``_plot_info`` populated.
    """
    def decorator(cls: type) -> type:
        if not hasattr(cls, "_plot_info"):
            cls._plot_info: dict[str, Any] = {}
        cls._plot_info[label.lower()] = {
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
    A :class:`~dissmodel.core.Model` that renders a live time-series chart.

    Supports three rendering targets:
    - **Streamlit**: pass a ``plot_area`` (``st.empty()``).
    - **Jupyter**: detected automatically via :func:`is_notebook`.
    - **Matplotlib window**: used as fallback in plain Python scripts.
    """

    # Declared here so mypy knows these exist after setup()
    fig: matplotlib.figure.Figure
    ax: matplotlib.axes.Axes
    select: Optional[list[str]]
    interval: int
    time_points: list[float]
    pause: bool
    plot_area: Any  # streamlit DeltaGenerator or None
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

        Args:
            select:      Subset of labels to plot. If ``None``, all tracked
                         variables are shown.
            pause:       If ``True``, call ``plt.pause()`` after each update
                         (required for live updates outside notebooks).
            plot_area:   Streamlit ``st.empty()`` placeholder. If provided,
                         the chart is rendered via Streamlit.
            show_legend: Whether to display the plot legend.
            show_grid:   Whether to display the plot grid.
            title:       Chart title.
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
        """Redraw the chart for the current simulation time step."""
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
