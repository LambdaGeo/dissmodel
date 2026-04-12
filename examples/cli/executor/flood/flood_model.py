"""
flood_vector_model.py — Hydrological Model (GeoDataFrame version)
=================================================================

Vector-based version of FloodRasterModel using GeoDataFrame + SpatialModel,
designed for direct comparison with the NumPy implementation
(flood_raster_model.py).

Same logic, different substrate:

    flood_raster_model.py     RasterBackend (NumPy, vectorized)
    flood_vector_model.py  ←  GeoDataFrame  (libpysal, cell-by-cell)

Why NOT use CellularAutomaton
------------------------------
CellularAutomaton.rule(idx) computes the new state of a cell based
on itself and its neighbors (pull model). The hydrological process
is source-oriented: flooded cells propagate flow and flooding to
their neighbors — the logic is the opposite (push model).

For this reason we inherit directly from SpatialModel and implement
execute() freely.

Usage
-----
    from dissmodel.core import Environment
    from coastal_dynamics.vector.flood_vector_model import FloodModel
    import geopandas as gpd

    gdf = gpd.read_file("flood_model.shp")
    env = Environment(start_time=1, end_time=88)
    FloodModel(gdf=gdf, taxa_elevacao=0.011)
    env.run()
"""
from __future__ import annotations

import geopandas as gpd
from libpysal.weights import Queen

from dissmodel.geo import SpatialModel
from dissmodel.visualization import track_plot


from .constants import (
    USOS_INUNDADOS,
    REGRAS_INUNDACAO,
    MAR,
)

@track_plot("flooded_cells", "blue")
class FloodModel(SpatialModel):
    """
    Hydrological model implemented with DisSModel + GeoDataFrame.

    Equivalence with the raster version
    -----------------------------------
    RasterBackend.shift2d()          →  neighs_id(idx) / neighbor_values()
    np.isin(uso, USOS_INUNDADOS)     →  uso_past.isin(USOS_INUNDADOS)
    loop over DIRS_MOORE             →  loop over real GDF neighbors
    vectorized over full grid        →  cell-by-cell loop (slower,
                                        but faithful to real geometry)

    Parameters
    ----------
    gdf           : GeoDataFrame with columns attr_uso and attr_alt
    taxa_elevacao : meters/year — IPCC RCP8.5 ≈ 0.011
    attr_uso      : land-use column. Default: "uso"
    attr_alt      : elevation column. Default: "alt"
    """


    

    def setup(
        self,
        taxa_elevacao: float = 0.011,
        attr_uso:      str   = "uso",
        attr_alt:      str   = "alt",
    ) -> None:
        self.taxa_elevacao = taxa_elevacao
        self.attr_uso      = attr_uso
        self.attr_alt      = attr_alt

        # metrics exposed for @track_plot / Chart
        self.flooded_cells = 0
        self.novas_inundadas   = 0
        self.nivel_mar_atual   = 0.0

        # Queen = Moore neighborhood (8 directions) for regular grids
        # silence_warnings suppresses island warnings (cells without neighbors)
        self.create_neighborhood(strategy=Queen, silence_warnings=True)

    def execute(self) -> None:
        nivel_mar = self.env.now() * self.taxa_elevacao

        # Snapshots — equivalent to cell.past[] in TerraME
        uso_past = self.gdf[self.attr_uso].copy()
        alt_past = self.gdf[self.attr_alt].copy()

        # ── sources: isSeaOrFlooded(uso) and alt >= 0 ─────────────────────────
        fontes = set(
            uso_past.index[
                uso_past.isin(USOS_INUNDADOS) & (alt_past >= 0)
            ]
        )

        # ── A. Elevation — flow diffusion (relative condition) ────────────────
        # Lua: if neighbor.past[alt] <= currentAlt: neigh[alt] += flow
        alt_nova = alt_past.copy()

        for idx in fontes:
            alt_atual = alt_past[idx]
            vizinhos  = self.neighs_id(idx)

            viz_baixos = 1 + sum(
                1 for n in vizinhos if alt_past[n] <= alt_atual
            )
            fluxo = self.taxa_elevacao / viz_baixos

            alt_nova[idx] += fluxo
            for n in vizinhos:
                if alt_past[n] <= alt_atual:
                    alt_nova[n] += fluxo

        self.gdf[self.attr_alt] = alt_nova

        # ── B. Flooding — absolute elevation threshold ───────────────────────
        # Lua: if neighbor.past[alt] <= seaLevel and not isSeaOrFlooded(neigh):
        #          applyFlooding(neighbor)
        # Uses alt_past — faithful to TerraME .past semantics
        uso_novo = uso_past.copy()

        for idx in self.gdf.index:
            uso_atual = uso_past[idx]
            if uso_atual not in REGRAS_INUNDACAO:
                continue
            if alt_past[idx] > nivel_mar:
                continue
            if any(n in fontes for n in self.neighs_id(idx)):
                uso_novo[idx] = REGRAS_INUNDACAO[uso_atual]

        self.gdf[self.attr_uso] = uso_novo

        # ── metrics ──────────────────────────────────────────────────────────
        inund = uso_novo.isin(USOS_INUNDADOS) & (uso_novo != MAR)
        novas = uso_novo.isin(USOS_INUNDADOS) & ~uso_past.isin(USOS_INUNDADOS)

        self.flooded_cells = int(inund.sum())
        self.novas_inundadas   = int(novas.sum())
        self.nivel_mar_atual   = round(nivel_mar, 4)