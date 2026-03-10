from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
import matplotlib.figure
import matplotlib.axes
import geopandas as gpd

from dissmodel.core import Model
from dissmodel.visualization._utils import is_interactive_backend, is_notebook


class Map(Model):
    """
    Simulation model that renders a live choropleth map.

    Extends :class:`~dissmodel.core.Model` and redraws the map at every
    time step. Supports three rendering targets:

    - **Streamlit** — pass a ``plot_area`` (``st.empty()``).
    - **Jupyter** — detected automatically via :func:`is_notebook`.
    - **Matplotlib window** — fallback for plain Python scripts.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame to render.
    plot_params : dict
        Keyword arguments forwarded to :meth:`GeoDataFrame.plot`
        (e.g. ``column``, ``cmap``, ``legend``).
    pause : bool, optional
        If ``True``, call ``plt.pause()`` after each update, by default
        ``True``. Required for live updates outside notebooks.
    plot_area : any, optional
        Streamlit ``st.empty()`` placeholder, by default ``None``.

    Examples
    --------
    >>> env = Environment(end_time=10)
    >>> Map(gdf=grid, plot_params={"column": "state", "cmap": "viridis"})
    >>> env.run()
    """

    fig: matplotlib.figure.Figure
    ax: matplotlib.axes.Axes
    gdf: gpd.GeoDataFrame
    plot_params: dict[str, Any]
    pause: bool
    plot_area: Any

    def setup(
        self,
        gdf: gpd.GeoDataFrame,
        plot_params: dict[str, Any],
        pause: bool = True,
        plot_area: Any = None,
    ) -> None:
        """
        Configure the map.

        Called automatically by salabim during component initialisation.

        Parameters
        ----------
        gdf : geopandas.GeoDataFrame
            GeoDataFrame to render.
        plot_params : dict
            Keyword arguments forwarded to :meth:`GeoDataFrame.plot`
            (e.g. ``column``, ``cmap``, ``legend``).
        pause : bool, optional
            If ``True``, call ``plt.pause()`` after each update,
            by default ``True``.
        plot_area : any, optional
            Streamlit ``st.empty()`` placeholder, by default ``None``.
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

        Parameters
        ----------
        year : float
            Current simulation time, displayed in the map title.
        gdf : geopandas.GeoDataFrame
            GeoDataFrame snapshot to render.

        Raises
        ------
        RuntimeError
            If no interactive matplotlib backend is detected and the code is
            not running in a notebook or Streamlit context.
        """
        if is_notebook():
            from IPython.display import clear_output, display
            clear_output(wait=True)
            self.fig, self.ax = plt.subplots(1, 1, figsize=(10, 6))
        else:
            self.fig.clf()
            self.ax = self.fig.add_subplot(1, 1, 1)

        gdf.plot(ax=self.ax, **self.plot_params)
        self.ax.set_title(f"Map — Step {year}")
        plt.tight_layout()
        plt.draw()

        if self.plot_area is not None:
            self.plot_area.pyplot(self.fig)
        elif is_notebook():
            from IPython.display import display
            display(self.fig)
            plt.close(self.fig)
        elif self.pause:
            if is_interactive_backend():
                plt.pause(0.01)
                if self.env.now() == self.env.end_time:
                    plt.show()
            else:
                raise RuntimeError(
                    "No interactive matplotlib backend detected. "
                    "On Linux, install tkinter:\n\n"
                    "    sudo apt install python3-tk\n"
                )


    def execute(self) -> None:
        """Redraw the map for the current simulation time step."""
        self.update(year=self.env.now(), gdf=self.gdf)
