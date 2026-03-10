"""
brmangue/mangue_vector_model.py — Modelo Mangue (versão GeoDataFrame)
======================================================================
Versão do MangroveModel usando GeoDataFrame + SpatialModel,
para comparação direta com a versão NumPy (mangue_raster_model.py).

Mesma lógica, diferente substrato:

    mangue_raster_model.py     RasterBackend (NumPy, vetorizado)
    mangue_vector_model.py  ←  GeoDataFrame  (libpysal, célula a célula)

Três processos por passo — ordem idêntica ao Lua e à versão raster:

    1. migrarSolos   — propaga substrato de mangue
    2. migrarUsos    — propaga uso MANGUE_MIGRADO (usa solo_past)
    3. aplicarAcrecao — eleva altitude (Alongi 2008, False por padrão)

NOTA CRÍTICA: migrarUsos usa solo_past — fiel ao .past do TerraME.

Uso
---
    from dissmodel.core import Environment
    from brmangue.mangue_vector_model import MangroveVectorModel
    import geopandas as gpd

    gdf = gpd.read_file("flood_model.shp")
    env = Environment(start_time=1, end_time=88)
    MangroveVectorModel(gdf=gdf, taxa_elevacao=0.011)
    env.run()
"""
from __future__ import annotations

import geopandas as gpd
from libpysal.weights import Queen

from dissmodel.geo.raster.spatial_model import SpatialModel

from coastal_dynamics.common.constants import (
    MANGUE,
    MANGUE_MIGRADO,
    VEGETACAO_TERRESTRE,
    SOLO_DESCOBERTO,
    USOS_INUNDADOS,
    SOLO_MANGUE,
    SOLO_MANGUE_MIGRADO,
    SOLO_CANAL_FLUVIAL,
)


class MangroveModel(SpatialModel):
    """
    Mangue (mangue.lua) → DisSModel + GeoDataFrame.

    Equivalência com a versão Raster
    ---------------------------------
    np.isin(solo, SOLOS_FONTE)       →  solo_past.isin(SOLOS_FONTE)
    shift2d loop sobre DIRS_MOORE    →  loop sobre vizinhos reais do GDF
    np.where(cond, novo, atual)      →  solo_novo[idx] = SOLO_MANGUE_MIGRADO
    solo_past (não solo_novo)        →  solo_past[idx] — mesmo cuidado .past

    Parâmetros
    ----------
    gdf           : GeoDataFrame com colunas attr_uso, attr_alt, attr_solo
    taxa_elevacao : m/ano — IPCC RCP8.5 = 0.011
    altura_mare   : AIM base em metros. Padrão: 6.0
    acrecao_ativa : habilita aplicarAcrecao (Alongi 2008). Padrão: False
    attr_uso      : coluna de uso do solo.  Padrão: "uso"
    attr_alt      : coluna de altitude.     Padrão: "alt"
    attr_solo     : coluna de tipo de solo. Padrão: "solo"
    """

    SOLOS_FONTE  = [SOLO_MANGUE, SOLO_MANGUE_MIGRADO, SOLO_CANAL_FLUVIAL]
    SOLOS_MANGUE = [SOLO_MANGUE, SOLO_MANGUE_MIGRADO]
    USOS_FONTE   = [MANGUE, MANGUE_MIGRADO]
    USOS_ALVO    = [VEGETACAO_TERRESTRE, SOLO_DESCOBERTO]
    COEF_A, COEF_B = 1.693, 0.939   # Alongi 2008

    def setup(
        self,
        taxa_elevacao: float = 0.011,
        altura_mare:   float = 6.0,
        acrecao_ativa: bool  = False,
        attr_uso:      str   = "uso",
        attr_alt:      str   = "alt",
        attr_solo:     str   = "solo",
    ) -> None:
        self.taxa_elevacao = taxa_elevacao
        self.altura_mare   = altura_mare
        self.acrecao_ativa = acrecao_ativa
        self.attr_uso      = attr_uso
        self.attr_alt      = attr_alt
        self.attr_solo     = attr_solo

        # métricas expostas para @track_plot / Chart
        self.mangue_migrado = 0
        self.solo_migrado   = 0

        self.create_neighborhood(strategy=Queen, silence_warnings=True)

    def execute(self) -> None:
        nivel_mar = self.env.now() * self.taxa_elevacao
        zi        = self.altura_mare + nivel_mar
        taxa_ac   = self.COEF_A / 1000.0 + self.COEF_B * nivel_mar

        # snapshots — equivale a celula.past[] do TerraME
        uso_past  = self.gdf[self.attr_uso].copy()
        alt_past  = self.gdf[self.attr_alt].copy()
        solo_past = self.gdf[self.attr_solo].copy()

        # ── migrarSolos ───────────────────────────────────────────────────────
        # Fonte: celula.past[solo] in SOLOS_FONTE
        # Alvo:  viz.uso  in USOS_ALVO
        #        viz.solo != SOLO_MANGUE_MIGRADO
        #        viz.alt  <= zonaInfluencia
        fontes_solo = set(
            solo_past.index[solo_past.isin(self.SOLOS_FONTE)]
        )
        solo_novo = solo_past.copy()

        for idx in self.gdf.index:
            if uso_past[idx] not in self.USOS_ALVO:
                continue
            if solo_past[idx] == SOLO_MANGUE_MIGRADO:
                continue
            if alt_past[idx] > zi:
                continue
            if any(n in fontes_solo for n in self.neighs_id(idx)):
                solo_novo[idx] = SOLO_MANGUE_MIGRADO

        # ── migrarUsos ────────────────────────────────────────────────────────
        # Fonte: celula.past[uso] in USOS_FONTE
        # Alvo:  viz.uso  in USOS_ALVO
        #        viz.solo in SOLOS_MANGUE  ← solo_PAST, não solo_novo
        #        viz.alt  <= zonaInfluencia
        fontes_uso = set(
            uso_past.index[uso_past.isin(self.USOS_FONTE)]
        )
        uso_novo = uso_past.copy()

        for idx in self.gdf.index:
            if uso_past[idx] not in self.USOS_ALVO:
                continue
            if solo_past[idx] not in self.SOLOS_MANGUE:   # ← solo_past
                continue
            if alt_past[idx] > zi:
                continue
            if any(n in fontes_uso for n in self.neighs_id(idx)):
                uso_novo[idx] = MANGUE_MIGRADO

        # ── aplicarAcrecao (False por padrão — comentada no Lua) ─────────────
        if self.acrecao_ativa:
            alt_nova = alt_past.copy()
            for idx in self.gdf.index:
                if solo_past[idx] in self.SOLOS_MANGUE:
                    if uso_past[idx] not in USOS_INUNDADOS:
                        alt_nova[idx] += taxa_ac
            self.gdf[self.attr_alt] = alt_nova

        self.gdf[self.attr_uso]  = uso_novo
        self.gdf[self.attr_solo] = solo_novo

        # ── métricas ──────────────────────────────────────────────────────────
        self.mangue_migrado = int((uso_novo  == MANGUE_MIGRADO).sum())
        self.solo_migrado   = int((solo_novo == SOLO_MANGUE_MIGRADO).sum())
