"""
dissmodel/visualization/map.py
================================
Visualization component for GeoDataFrame — choropleth map rendered at
every simulation step.

Supported render targets
------------------------
1. **Streamlit**   — ``plot_area=st.empty()``
2. **Jupyter**     — detected automatically
3. **Interactive** — matplotlib window (TkAgg / Qt)
4. **Headless**    — saves PNGs to ``map_frames/`` (default fallback)

The headless fallback means the component never raises ``RuntimeError``
in CI or server environments — it simply writes one PNG per step.

Usage examples
--------------
    # basic
    Map(gdf=grid, plot_params={"column": "state", "cmap": "viridis"})

    # with legend and classification scheme
    Map(gdf=grid, plot_params={
        "column": "f",
        "cmap":   "Greens",
        "scheme": "equal_interval",
        "k":      5,
        "legend": True,
    })

    # Streamlit
    plot_area = st.empty()
    Map(gdf=grid, plot_params={"column": "uso"}, plot_area=plot_area)

    # force frame saving even in interactive mode
    Map(gdf=grid, plot_params={"column": "uso"}, save_frames=True)

Notes
-----
Analogous to ``RasterMap`` for vector data. Both components share the
same rendering targets and the same ``save_frames`` / headless behaviour.
"""
from __future__ import annotations

import pathlib
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.figure
import matplotlib.axes
import geopandas as gpd

from dissmodel.core import Model
from dissmodel.visualization._utils import is_interactive_backend, is_notebook


class Map(Model):
    """
    Simulation model that renders a live choropleth map of a GeoDataFrame.

    Extends :class:`~dissmodel.core.Model` and redraws the map at every
    simulation step.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame to render. Updated in-place by the simulation models
        sharing the same reference.
    plot_params : dict
        Keyword arguments forwarded to :meth:`GeoDataFrame.plot`
        (e.g. ``column``, ``cmap``, ``scheme``, ``legend``).
    figsize : tuple[int, int]
        Figure size in inches. Default: ``(10, 6)``.
    pause : bool
        Call ``plt.pause()`` after each update in interactive mode.
        Default: ``True``.
    interval : float
        Seconds passed to ``plt.pause()``. Default: ``0.01``.
    plot_area : st.empty() | None
        Streamlit placeholder. Default: ``None``.
    save_frames : bool
        If ``True``, save one PNG per step to ``map_frames/`` regardless
        of the rendering environment. Default: ``False``.

    Notes
    -----
    **Headless / CI behaviour** — when no interactive backend is available
    and ``plot_area`` is ``None`` and the code is not running in a notebook,
    the component automatically saves PNGs to ``map_frames/`` instead of
    raising an error. This makes it safe to use in CI pipelines and remote
    servers without a display.

    Examples
    --------
    >>> env = Environment(end_time=10)
    >>> Map(gdf=grid, plot_params={"column": "state", "cmap": "viridis"})
    >>> env.run()
    """

    fig: matplotlib.figure.Figure
    ax:  matplotlib.axes.Axes

    def setup(
        self,
        gdf:         gpd.GeoDataFrame,
        plot_params: dict[str, Any],
        figsize:     tuple[int, int]  = (10, 6),
        pause:       bool             = True,
        interval:    float            = 0.01,
        plot_area:   Any              = None,
        save_frames: bool             = False,
    ) -> None:
        self.gdf         = gdf
        self.plot_params = plot_params
        self.figsize     = figsize
        self.pause       = pause
        self.interval    = interval
        self.plot_area   = plot_area
        self.save_frames = save_frames

        # pre-create figure for interactive mode to avoid flicker
        if not is_notebook() and plot_area is None:
            self.fig, self.ax = plt.subplots(1, 1, figsize=self.figsize)

    # ── rendering ─────────────────────────────────────────────────────────────

    def _render(self, step: float) -> matplotlib.figure.Figure:
        """Build and return the figure for the current step."""
        if is_notebook():
            from IPython.display import clear_output
            clear_output(wait=True)
            self.fig, self.ax = plt.subplots(1, 1, figsize=self.figsize)
        else:
            self.fig.clf()
            self.ax = self.fig.add_subplot(1, 1, 1)

        self.gdf.plot(ax=self.ax, **self.plot_params)
        self.ax.set_title(f"Map — Step {int(step)}")
        plt.tight_layout()
        plt.draw()
        return self.fig

    def _save_frame(self, fig: matplotlib.figure.Figure, step: float) -> None:
        """Save the current figure to map_frames/{column}_step_NNN.png."""
        col     = self.plot_params.get("column", "map")
        out_dir = pathlib.Path("map_frames")
        out_dir.mkdir(exist_ok=True)
        fname = out_dir / f"{col}_step_{int(step):03d}.png"
        fig.savefig(fname, dpi=100, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        plt.close(fig)
        end_time = getattr(self.env, "end_time", step)
        if int(step) % 10 == 0 or step == end_time:
            print(f"  Map [{col}] step {int(step):3d} → {fname}")

    # ── execute ───────────────────────────────────────────────────────────────

    def execute(self) -> None:
        """Redraw the map for the current simulation step."""
        step = self.env.now()
        fig  = self._render(step)

        # ── Streamlit ─────────────────────────────────────────────────────────
        if self.plot_area is not None:
            self.plot_area.pyplot(fig)
            plt.close(fig)

        # ── Jupyter ───────────────────────────────────────────────────────────
        elif is_notebook():
            from IPython.display import display
            display(fig)
            plt.close(fig)

        # ── save frames (explicit or headless fallback) ───────────────────────
        elif self.save_frames or not is_interactive_backend():
            self._save_frame(fig, step)

        # ── interactive window ────────────────────────────────────────────────
        else:
            if self.pause:
                plt.pause(self.interval)
            end_time = getattr(self.env, "end_time", step)
            if step == end_time:
                plt.show()
