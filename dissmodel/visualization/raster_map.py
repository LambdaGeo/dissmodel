"""
dissmodel/visualization/raster_map.py
======================================
Visualization component for RasterBackend — the raster analogue of the
vector ``Map`` component in DisSModel.

Responsibility
--------------
Render any named array from a ``RasterBackend`` without any domain
knowledge — no land-use constants, no CRS, no hard-coded colours.

Visual definitions (colours, labels, colormaps) are injected by the
project at instantiation time.

Supported render targets
------------------------
1. **Streamlit**   — ``plot_area=st.empty()``
2. **Jupyter**     — detected automatically
3. **Interactive** — ``RASTER_MAP_INTERACTIVE=1`` (TkAgg / Qt)
4. **Headless**    — saves PNGs to ``raster_map_frames/`` (default)

Minimal usage (headless / no colour map)
-----------------------------------------
    from dissmodel.geo.raster.backend import RasterBackend
    from dissmodel.visualization.raster_map import RasterMap
    from dissmodel.core import Environment

    env = Environment(start_time=1, end_time=10)
    YourModel(backend=b)
    RasterMap(backend=b, band="state")
    env.run()
    # → raster_map_frames/state_step_001.png … state_step_010.png

Categorical usage (domain colour map)
---------------------------------------
    from myproject.constants import LAND_USE_COLORS, LAND_USE_LABELS

    RasterMap(
        backend    = b,
        band       = "uso",
        title      = "Land Use",
        color_map  = LAND_USE_COLORS,   # dict[int, str]  value → hex colour
        labels     = LAND_USE_LABELS,   # dict[int, str]  value → legend label
    )

Continuous usage (altimetry, temperature, …)
---------------------------------------------
    RasterMap(
        backend         = b,
        band            = "alt",
        title           = "Altimetry",
        cmap            = "terrain",
        colorbar_label  = "Altitude (m)",
        mask_band       = "uso",    # optional: mask cells where uso == mask_value
        mask_value      = 3,        # e.g. SEA = 3
    )
"""
from __future__ import annotations

import os
import pathlib
from typing import Any

import matplotlib
if os.environ.get("RASTER_MAP_INTERACTIVE", "0") == "1":
    pass          # let matplotlib choose TkAgg / Qt
else:
    matplotlib.use("Agg")   # headless — no display window

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches

from dissmodel.core import Model
from dissmodel.visualization._utils import is_notebook


def _is_interactive() -> bool:
    return matplotlib.get_backend().lower() not in ("agg", "cairo", "svg", "pdf", "ps")


class RasterMap(Model):
    """
    Visualization model for RasterBackend.

    Parameters
    ----------
    backend : RasterBackend
        Backend shared with the simulation models.
    band : str
        Name of the array to visualize.
    title : str
        Figure title prefix. Default: ``"RasterMap"``.
    figsize : tuple[int, int]
        Figure size in inches. Default: ``(7, 7)``.
    pause : bool
        Use ``plt.pause()`` in interactive mode. Default: ``True``.
    interval : float
        Seconds between steps in interactive mode. Default: ``0.5``.
    plot_area : st.empty() | None
        Streamlit placeholder. Default: ``None``.

    Categorical mode (``color_map`` provided)
    ------------------------------------------
    color_map : dict[int, str] | None
        Value-to-hex-colour mapping. Example: ``{1: "#006400", 3: "#00008b"}``.
        When provided, renders with a ``ListedColormap`` and a legend.
    labels : dict[int, str] | None
        Value-to-label mapping for the legend.
        If ``None`` and ``color_map`` is provided, uses ``str(value)``.

    Continuous mode (``color_map`` absent)
    ----------------------------------------
    cmap : str
        Matplotlib colormap name. Default: ``"viridis"``.
    vmin : float | None
        Minimum value for the colour scale. Default: array minimum.
    vmax : float | None
        Maximum value for the colour scale. Default: array maximum.
    colorbar_label : str
        Colorbar label. Default: value of ``band``.
    mask_band : str | None
        Name of another array used to mask cells.
    mask_value : int | float | None
        Value in ``mask_band`` to mask (e.g. ``SEA=3`` for altimetry).

    Examples
    --------
    >>> env = Environment(start_time=1, end_time=10)
    >>> RasterMap(backend=b, band="state")
    >>> env.run()
    """

    def setup(
        self,
        backend,
        band:            str             = "state",
        title:           str             = "RasterMap",
        figsize:         tuple[int, int] = (7, 7),
        pause:           bool            = True,
        interval:        float           = 0.5,
        plot_area:       Any             = None,
        # categorical mode
        color_map:       dict[int, str] | None = None,
        labels:          dict[int, str] | None = None,
        # continuous mode
        cmap:            str             = "viridis",
        vmin:            float | None    = None,
        vmax:            float | None    = None,
        colorbar_label:  str | None      = None,
        mask_band:       str | None      = None,
        mask_value:      int | float | None = None,
    ) -> None:
        self.backend         = backend
        self.band            = band
        self.title           = title
        self.figsize         = figsize
        self.pause           = pause
        self.interval        = interval
        self.plot_area       = plot_area
        self.color_map       = color_map
        self.labels          = labels or {}
        self.cmap            = cmap
        self.vmin            = vmin
        self.vmax            = vmax
        self.colorbar_label  = colorbar_label or band
        self.mask_band       = mask_band
        self.mask_value      = mask_value

    # ── rendering ─────────────────────────────────────────────────────────────

    def _render(self, step: float) -> matplotlib.figure.Figure:
        plt.close("all")
        fig, ax = plt.subplots(figsize=self.figsize)
        self.fig, self.ax = fig, ax

        arr = self.backend.arrays.get(self.band)
        if arr is None:
            ax.text(0.5, 0.5, f"band '{self.band}' not found",
                    ha="center", va="center", transform=ax.transAxes)
            ax.set_title(f"{self.title} [{self.band}] — Step {int(step)}")
            return fig

        if self.color_map:
            self._render_categorical(ax, arr)
        else:
            self._render_continuous(ax, arr)

        ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(f"{self.title} [{self.band}] — Step {int(step)}")
        plt.tight_layout()
        return fig

    def _render_categorical(self, ax, arr: np.ndarray) -> None:
        """Render integer arrays using a ListedColormap with value-to-colour mapping."""
        vals = sorted(self.color_map)
        cmap = mcolors.ListedColormap([self.color_map[k] for k in vals])
        norm = mcolors.BoundaryNorm(
            [v - 0.5 for v in vals] + [vals[-1] + 0.5], cmap.N
        )
        ax.imshow(arr, cmap=cmap, norm=norm, aspect="equal", interpolation="nearest")

        # legend shows only values present in the current array
        present = set(np.unique(arr))
        patches = [
            matplotlib.patches.Patch(
                color=self.color_map[k],
                label=self.labels.get(k, str(k)),
            )
            for k in vals if k in present
        ]
        if patches:
            ax.legend(handles=patches, loc="lower right", fontsize=7, framealpha=0.7)

    def _render_continuous(self, ax, arr: np.ndarray) -> None:
        """Render continuous arrays with a colorbar and optional mask."""
        data = arr.astype(float)

        if self.mask_band is not None and self.mask_value is not None:
            mask_arr = self.backend.arrays.get(self.mask_band)
            if mask_arr is not None:
                data = np.ma.masked_where(mask_arr == self.mask_value, data)

        vmin = self.vmin if self.vmin is not None else float(np.nanmin(data))
        vmax = self.vmax if self.vmax is not None else float(np.nanmax(data))
        if vmin == vmax:
            vmax = vmin + 1.0

        im = ax.imshow(data, cmap=self.cmap, aspect="equal",
                       interpolation="nearest", vmin=vmin, vmax=vmax)
        plt.colorbar(im, ax=ax, label=self.colorbar_label, fraction=0.03, pad=0.02)

    # ── execute ───────────────────────────────────────────────────────────────

    def execute(self) -> None:
        """Render the current array state and dispatch to the active output target."""
        step = self.env.now()
        fig  = self._render(step)
        plt.draw()

        if self.plot_area is not None:
            # Streamlit
            self.plot_area.pyplot(fig)
            plt.close(fig)

        elif is_notebook():
            # Jupyter
            from IPython.display import clear_output, display
            clear_output(wait=True)
            display(fig)
            plt.close(fig)

        elif self.pause and _is_interactive():
            # interactive window (TkAgg / Qt)
            plt.pause(self.interval)
            if step == getattr(self.env, "end_time", step):
                input("Simulation complete — press Enter to close...")
                plt.close("all")

        else:
            # headless — save PNG to raster_map_frames/
            out_dir = pathlib.Path("raster_map_frames")
            out_dir.mkdir(exist_ok=True)
            fname = out_dir / f"{self.band}_step_{int(step):03d}.png"
            fig.savefig(fname, dpi=100, bbox_inches="tight",
                        facecolor=fig.get_facecolor())
            plt.close(fig)
            if int(step) % 10 == 0 or step == getattr(self.env, "end_time", step):
                print(f"  RasterMap [{self.band}] step {int(step):3d} → {fname}")