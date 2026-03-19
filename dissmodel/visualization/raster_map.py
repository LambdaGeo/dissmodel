"""
dissmodel/visualization/raster_map.py
======================================
Visualization component for RasterBackend — the raster analogue of the
vector ``Map`` component in DisSModel.

Supported render targets
------------------------
1. **Streamlit**   — ``plot_area=st.empty()``
2. **Jupyter**     — detected automatically
3. **Interactive** — ``RASTER_MAP_INTERACTIVE=1`` (TkAgg / Qt)
4. **Headless**    — saves PNGs to ``raster_map_frames/`` (default)

Usage examples
--------------
    # categorical
    RasterMap(backend=b, band="uso", color_map=COLORS, labels=LABELS)

    # continuous — paridade com Map vetorial
    RasterMap(backend=b, band="f", cmap="Greens",
              scheme="equal_interval", k=5, legend=True)

    # continuous — vmin/vmax explícitos
    RasterMap(backend=b, band="alt", cmap="terrain",
              vmin=0.0, vmax=100.0, colorbar_label="Altitude (m)",
              mask_band="uso", mask_value=3)
"""
from __future__ import annotations

import os
import pathlib
from typing import Any

import matplotlib
if os.environ.get("RASTER_MAP_INTERACTIVE", "0") == "1":
    pass
else:
    matplotlib.use("Agg")

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
    band : str
        Array to visualize.
    title : str
        Figure title prefix. Default: ``"RasterMap"``.
    figsize : tuple[int, int]
        Default: ``(7, 7)``.
    pause : bool
        Use ``plt.pause()`` in interactive mode. Default: ``True``.
    interval : float
        Seconds between steps in interactive mode. Default: ``0.5``.
    plot_area : st.empty() | None
        Streamlit placeholder.

    Categorical mode  (``color_map`` provided)
    -------------------------------------------
    color_map : dict[int, str]
        ``{value: "#rrggbb"}``
    labels : dict[int, str]
        ``{value: "label"}`` — used in the legend.

    Continuous mode  (``color_map`` absent)
    ----------------------------------------
    cmap : str
        Matplotlib colormap name. Default: ``"viridis"``.
    scheme : str
        ``"manual"``         — use ``vmin`` / ``vmax`` (default).
        ``"equal_interval"`` — divide [min, max] of valid data into ``k`` classes.
        ``"quantiles"``      — p2–p98 of valid data, robust to outliers.
    k : int
        Number of colour classes for ``scheme="equal_interval"``.
        Analogous to ``k`` in the vector Map. Default: ``5``.
    vmin, vmax : float | None
        Bounds for ``scheme="manual"``.
    legend : bool
        Show the colorbar. Default: ``True``.
    colorbar_label : str
        Colorbar label. Default: ``band``.
    mask_band : str | None
        Array used to mask cells.
    mask_value : int | float | None
        Value in ``mask_band`` to mask.

    Notes
    -----
    NaN / Inf cells — including pixels outside the study extent — are
    rendered as fully transparent so they never inherit the colormap's
    "under" colour.
    """

    def setup(
        self,
        backend,
        band:            str              = "state",
        title:           str              = "RasterMap",
        figsize:         tuple[int, int]  = (7, 7),
        pause:           bool             = True,
        interval:        float            = 0.5,
        plot_area:       Any              = None,
        # categorical
        color_map:       dict[int, str] | None = None,
        labels:          dict[int, str] | None = None,
        # continuous
        cmap:            str              = "viridis",
        scheme:          str              = "manual",
        k:               int              = 5,
        vmin:            float | None     = None,
        vmax:            float | None     = None,
        legend:          bool             = True,
        colorbar_label:  str | None       = None,
        mask_band:       str | None       = None,
        mask_value:      int | float | None = None,
    ) -> None:
        self.backend        = backend
        self.band           = band
        self.title          = title
        self.figsize        = figsize
        self.pause          = pause
        self.interval       = interval
        self.plot_area      = plot_area
        self.color_map      = color_map
        self.labels         = labels or {}
        self.cmap           = cmap
        self.scheme         = scheme
        self.k              = k
        self.vmin           = vmin
        self.vmax           = vmax
        self.legend         = legend
        self.colorbar_label = colorbar_label or band
        self.mask_band      = mask_band
        self.mask_value     = mask_value

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

        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(f"{self.title} [{self.band}] — Step {int(step)}")
        plt.tight_layout()
        return fig

    def _render_categorical(self, ax, arr: np.ndarray) -> None:
        vals = sorted(self.color_map)
        cmap = mcolors.ListedColormap([self.color_map[v] for v in vals])
        norm = mcolors.BoundaryNorm(
            [v - 0.5 for v in vals] + [vals[-1] + 0.5], cmap.N
        )
        # NaN → transparent
        data = np.ma.masked_invalid(arr.astype(float))
        cmap.set_bad(color="white", alpha=0)

        ax.imshow(data, cmap=cmap, norm=norm, aspect="equal", interpolation="nearest")

        present = set(np.unique(arr[~np.isnan(arr.astype(float))]))
        patches = [
            matplotlib.patches.Patch(color=self.color_map[v],
                                     label=self.labels.get(v, str(v)))
            for v in vals if v in present
        ]
        if patches:
            ax.legend(handles=patches, loc="lower right", fontsize=7, framealpha=0.7)

    def _render_continuous(self, ax, arr: np.ndarray) -> None:
        data = arr.astype(float)

        # 1. máscara explícita de no-data (ex: células de mar)
        if self.mask_band is not None and self.mask_value is not None:
            mask_arr = self.backend.arrays.get(self.mask_band)
            if mask_arr is not None:
                data = np.where(mask_arr == self.mask_value, np.nan, data)

        # 2. mascara NaN/Inf — cobre pixels fora do extent
        data = np.ma.masked_invalid(data)

        # 3. colormap com células mascaradas transparentes
        cmap = plt.get_cmap(self.cmap).copy()
        cmap.set_bad(color="white", alpha=0)

        # 4. limites da escala de cor
        valid = data.compressed()   # apenas valores não mascarados

        if len(valid) == 0:
            vmin, vmax = 0.0, 1.0

        elif self.scheme == "equal_interval":
            # divide [min, max] em k classes iguais — análogo ao Map vetorial
            vmin = float(valid.min())
            vmax = float(valid.max())
            if vmin != vmax and self.k > 1:
                bounds = np.linspace(vmin, vmax, self.k + 1)
                norm   = mcolors.BoundaryNorm(bounds, plt.get_cmap(self.cmap).N)
                im = ax.imshow(data, cmap=cmap, norm=norm, aspect="equal",
                               interpolation="nearest")
                if self.legend:
                    plt.colorbar(im, ax=ax, label=self.colorbar_label,
                                 fraction=0.03, pad=0.02)
                return   # saída antecipada — norm já aplicado

        elif self.scheme == "quantiles":
            vmin = float(np.percentile(valid, 2))
            vmax = float(np.percentile(valid, 98))

        else:   # "manual"
            vmin = self.vmin if self.vmin is not None else float(valid.min())
            vmax = self.vmax if self.vmax is not None else float(valid.max())

        if vmin == vmax:
            vmax = vmin + 1.0

        im = ax.imshow(data, cmap=cmap, aspect="equal",
                       interpolation="nearest", vmin=vmin, vmax=vmax)
        if self.legend:
            plt.colorbar(im, ax=ax, label=self.colorbar_label,
                         fraction=0.03, pad=0.02)

    # ── execute ───────────────────────────────────────────────────────────────

    def execute(self) -> None:
        step = self.env.now()
        fig  = self._render(step)
        plt.draw()

        if self.plot_area is not None:
            self.plot_area.pyplot(fig)
            plt.close(fig)

        elif is_notebook():
            from IPython.display import clear_output, display
            clear_output(wait=True)
            display(fig)
            plt.close(fig)

        elif self.pause and _is_interactive():
            plt.pause(self.interval)
            if step == getattr(self.env, "end_time", step):
                input("Simulation complete — press Enter to close...")
                plt.close("all")

        else:
            out_dir = pathlib.Path("raster_map_frames")
            out_dir.mkdir(exist_ok=True)
            fname = out_dir / f"{self.band}_step_{int(step):03d}.png"
            fig.savefig(fname, dpi=100, bbox_inches="tight",
                        facecolor=fig.get_facecolor())
            plt.close(fig)
            if int(step) % 10 == 0 or step == getattr(self.env, "end_time", step):
                print(f"  RasterMap [{self.band}] step {int(step):3d} → {fname}")
