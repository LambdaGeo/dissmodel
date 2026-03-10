"""
dissmodel/visualization/raster_map.py
======================================
Visualização de RasterBackend — análogo ao Map (geopandas) do DisSModel,
mas para grades NumPy 2D.

Responsabilidade
----------------
Renderizar qualquer array nomeado de um RasterBackend sem saber nada do
domínio — sem constantes de uso do solo, sem CRS, sem cores fixas.

As definições visuais (cores, labels, colormaps) são passadas pelo
projeto no momento da instanciação.

Destinos de renderização suportados
-------------------------------------
    1. Streamlit  — plot_area=st.empty()
    2. Jupyter    — detectado automaticamente
    3. Interativo — RASTER_MAP_INTERACTIVE=1 (TkAgg/Qt)
    4. Headless   — salva PNGs em raster_map_frames/ (padrão)

Uso mínimo (headless / sem cores)
----------------------------------
    from dissmodel.geo.raster_backend import RasterBackend
    from dissmodel.visualization.raster_map import RasterMap
    from dissmodel.core import Environment

    env = Environment(start_time=1, end_time=10)
    SeuModel(backend=b)
    RasterMap(backend=b, band="estado")
    env.run()
    # → raster_map_frames/estado_step_001.png … estado_step_010.png

Uso com cores de domínio (projeto BR-MANGUE)
---------------------------------------------
    from brmangue.constants import USO_COLORS, USO_LABELS

    RasterMap(
        backend    = b,
        band       = "uso",
        title      = "Uso do Solo",
        color_map  = USO_COLORS,   # dict[int, str hex]
        labels     = USO_LABELS,   # dict[int, str]
    )

Uso com colormap contínuo (altimetria, temperatura, …)
-------------------------------------------------------
    RasterMap(
        backend    = b,
        band       = "alt",
        title      = "Altimetria",
        cmap       = "terrain",
        colorbar_label = "Altitude (m)",
        mask_band  = "uso",    # opcional: mascara células onde uso==mask_value
        mask_value = 3,        # ex.: MAR=3
    )
"""
from __future__ import annotations

import os
import pathlib
from typing import Any

import matplotlib
if os.environ.get("RASTER_MAP_INTERACTIVE", "0") == "1":
    pass          # deixa matplotlib escolher TkAgg/Qt
else:
    matplotlib.use("Agg")   # headless — sem janela

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
    Modelo de visualização para RasterBackend.

    Parâmetros
    ----------
    backend : RasterBackend
        Backend compartilhado com os modelos de simulação.
    band : str
        Nome do array a visualizar.
    title : str
        Prefixo do título. Padrão: ``"RasterMap"``.
    figsize : tuple[int, int]
        Tamanho da figura em polegadas. Padrão: ``(7, 7)``.
    pause : bool
        Usar plt.pause() em modo interativo. Padrão: ``True``.
    plot_area : st.empty() | None
        Placeholder Streamlit. Padrão: ``None``.

    -- modo categórico (color_map preenchido) --
    color_map : dict[int, str] | None
        Mapeamento valor → cor hex. Ex.: {1: "#006400", 3: "#00008b"}.
        Se fornecido, renderiza com ListedColormap + legenda.
    labels : dict[int, str] | None
        Mapeamento valor → rótulo para a legenda.
        Se None e color_map fornecido, usa str(valor).

    -- modo contínuo (color_map ausente) --
    cmap : str
        Nome do colormap matplotlib. Padrão: ``"viridis"``.
    vmin : float | None
        Valor mínimo da escala. Padrão: mínimo do array.
    vmax : float | None
        Valor máximo da escala. Padrão: máximo do array.
    colorbar_label : str
        Rótulo da colorbar. Padrão: valor de ``band``.
    mask_band : str | None
        Nome de outro array usado para mascarar células.
    mask_value : int | float | None
        Valor em mask_band a mascarar (ex.: MAR=3 para altimetria).
    """

    def setup(
        self,
        backend,
        band:            str             = "estado",
        title:           str             = "RasterMap",
        figsize:         tuple[int, int] = (7, 7),
        pause:           bool            = True,
        interval:        float           = 0.5,   # segundos entre passos (modo interativo)
        plot_area:       Any             = None,
        # modo categórico
        color_map:       dict[int, str] | None = None,
        labels:          dict[int, str] | None = None,
        # modo contínuo
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

    # ── renderização ──────────────────────────────────────────────────────────

    def _render(self, step: float) -> matplotlib.figure.Figure:
        plt.close("all")
        fig, ax = plt.subplots(figsize=self.figsize)
        self.fig, self.ax = fig, ax

        arr = self.backend.arrays.get(self.band)
        if arr is None:
            ax.text(0.5, 0.5, f"band '{self.band}' não encontrado",
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
        """ListedColormap para arrays inteiros com mapeamento valor→cor."""
        vals = sorted(self.color_map)
        cmap = mcolors.ListedColormap([self.color_map[k] for k in vals])
        norm = mcolors.BoundaryNorm(
            [v - 0.5 for v in vals] + [vals[-1] + 0.5], cmap.N
        )
        ax.imshow(arr, cmap=cmap, norm=norm, aspect="equal", interpolation="nearest")

        # legenda apenas com valores presentes no array atual
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
        """Colormap contínuo com colorbar e máscara opcional."""
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
                input("Simulação concluída — pressione Enter para fechar...")
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
