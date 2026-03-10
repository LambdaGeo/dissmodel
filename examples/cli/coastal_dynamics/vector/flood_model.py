"""
brmangue/flood_vector_model.py — Modelo Hidro (versão GeoDataFrame)
====================================================================
Versão do FloodRasterModel usando GeoDataFrame + SpatialModel,
para comparação direta com a versão NumPy (flood_raster_model.py).

Mesma lógica, diferente substrato:

    flood_raster_model.py     RasterBackend (NumPy, vetorizado)
    flood_vector_model.py  ←  GeoDataFrame  (libpysal, célula a célula)

Por que NÃO usar CellularAutomaton
-----------------------------------
CellularAutomaton.rule(idx) calcula o novo estado de uma célula com base
em si mesma e nos seus vizinhos (modelo pull). O Hidro é orientado a
FONTE: células inundadas propagam fluxo e inundação para vizinhos —
a lógica é inversa (modelo push). Por isso herdamos SpatialModel
diretamente e implementamos execute() livremente.

Uso
---
    from dissmodel.core import Environment
    from brmangue.flood_vector_model import FloodVectorModel
    import geopandas as gpd

    gdf = gpd.read_file("flood_model.shp")
    env = Environment(start_time=1, end_time=88)
    FloodVectorModel(gdf=gdf, taxa_elevacao=0.011)
    env.run()
"""
from __future__ import annotations

import geopandas as gpd
from libpysal.weights import Queen

from dissmodel.geo.raster.spatial_model import SpatialModel

from coastal_dynamics.common.constants import (
    USOS_INUNDADOS,
    REGRAS_INUNDACAO,
    MAR,
)


class FloodVectorModel(SpatialModel):
    """
    Hidro (hidro.lua) → DisSModel + GeoDataFrame.

    Equivalência com a versão Raster
    ---------------------------------
    RasterBackend.shift2d()          →  neighs_id(idx) / neighbor_values()
    np.isin(uso, USOS_INUNDADOS)     →  uso_past.isin(USOS_INUNDADOS)
    loop sobre DIRS_MOORE            →  loop sobre vizinhos reais do GDF
    vetorizado sobre grade inteira   →  loop célula a célula (mais lento,
                                        mas fiel à geometria real)

    Parâmetros
    ----------
    gdf           : GeoDataFrame com colunas attr_uso e attr_alt
    taxa_elevacao : m/ano — IPCC RCP8.5 = 0.011
    attr_uso      : coluna de uso do solo. Padrão: "uso"
    attr_alt      : coluna de altitude.   Padrão: "alt"
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

        # métricas expostas para @track_plot / Chart
        self.celulas_inundadas = 0
        self.novas_inundadas   = 0
        self.nivel_mar_atual   = 0.0

        # Queen = vizinhança Moore (8 direções) para grade regular
        # silence_warnings suprime aviso de ilhas (células sem vizinhos)
        self.create_neighborhood(strategy=Queen, silence_warnings=True)

    def execute(self) -> None:
        nivel_mar = self.env.now() * self.taxa_elevacao

        # Snapshots — equivale a celula.past[] do TerraME
        uso_past = self.gdf[self.attr_uso].copy()
        alt_past = self.gdf[self.attr_alt].copy()

        # ── fontes: ehMarOuInundado(uso) and alt >= 0 ─────────────────────────
        fontes = set(
            uso_past.index[
                uso_past.isin(USOS_INUNDADOS) & (alt_past >= 0)
            ]
        )

        # ── A. Altimetria — difusão de fluxo (condição relativa) ──────────────
        # Lua: if vizinho.past[alt] <= altAtual: viz[alt] += fluxo
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

        # ── B. Inundação — cota absoluta (BR-MANGUE, Bezerra 2014) ───────────
        # Lua: if vizinho.past[alt] <= nivelMar and not ehMarOuInundado(viz):
        #          aplicarInundacao(vizinho)
        # Usa alt_past — fiel ao .past do TerraME
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

        # ── métricas ──────────────────────────────────────────────────────────
        inund = uso_novo.isin(USOS_INUNDADOS) & (uso_novo != MAR)
        novas = uso_novo.isin(USOS_INUNDADOS) & ~uso_past.isin(USOS_INUNDADOS)
        self.celulas_inundadas = int(inund.sum())
        self.novas_inundadas   = int(novas.sum())
        self.nivel_mar_atual   = round(nivel_mar, 4)
