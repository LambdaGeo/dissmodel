from __future__ import annotations

from typing import Any, Optional

import matplotlib.pyplot as plt
import matplotlib.figure
import matplotlib.axes
import geopandas as gpd

from dissmodel.core import Model


# ---------------------------------------------------------------------------
# Helper — shared with chart.py; consider moving to dissmodel.visualization._utils
# ---------------------------------------------------------------------------

def is_notebook() -> bool:
    """Return True if the code is running inside a Jupyter notebook."""
    try:
        from IPython import get_ipython
        return get_ipython().__class__.__name__ == "ZMQInteractiveShell"
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Map model
# ---------------------------------------------------------------------------

class Map(Model):
    """
    A :class:`~dissmodel.core.Model` that renders a live choropleth map.

    Supports the same three rendering targets as :class:`~dissmodel.visualization.Chart`:
    Streamlit, Jupyter, and a plain Matplotlib window.
    """

    fig: matplotlib.figure.Figure
    ax: matplotlib.axes.Axes
    gdf: gpd.GeoDataFrame
    plot_params: dict[str, Any]
    pause: bool
    plot_area: Any  # streamlit DeltaGenerator or None

    def setup(
        self,
        gdf: gpd.GeoDataFrame,
        plot_params: dict[str, Any],
        pause: bool = True,
        plot_area: Any = None,
    ) -> None:
        """
        Configure the map.

        Args:
            gdf:         GeoDataFrame to render.
            plot_params: Keyword arguments forwarded to
                         :meth:`GeoDataFrame.plot` (e.g. ``column``, ``cmap``,
                         ``legend``).
            pause:       If ``True``, call ``plt.pause()`` after each update
                         (required for live updates outside notebooks).
            plot_area:   Streamlit ``st.empty()`` placeholder. If provided,
                         the map is rendered via Streamlit.
        """
        self.gdf = gdf
        self.plot_params = plot_params
        self.pause = pause
        self.plot_area = plot_area

        if not is_notebook():
            self.fig, self.ax = plt.subplots(1, 1, figsize=(10, 6))

    def update(self, year: float, gdf: gpd.GeoDataFrame) -> None:
        """
        Redraw the map for a given simulation time.

        Args:
            year: Current simulation time, shown in the map title.
            gdf:  GeoDataFrame snapshot to render.
        """
        if is_notebook():
            from IPython.display import clear_output
            clear_output(wait=True)
            self.fig, self.ax = plt.subplots(1, 1, figsize=(10, 6))

        self.fig.clf()
        self.ax = self.fig.add_subplot(1, 1, 1)

        gdf.plot(ax=self.ax, **self.plot_params)
        self.ax.set_title(f"Map — Year {year}")
        plt.tight_layout()
        plt.draw()

        if self.plot_area is not None:
            self.plot_area.pyplot(self.fig)
        elif is_notebook():
            from IPython.display import display
            display(self.fig)
            plt.close(self.fig)
        elif self.pause:
            plt.pause(0.01)
            if self.env.now() == self.env.end_time:
                plt.show()

    def execute(self) -> None:
        """Redraw the map for the current simulation time step."""
        self.update(year=self.env.now(), gdf=self.gdf)
