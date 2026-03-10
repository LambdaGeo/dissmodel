"""
brmangue/mangue_raster_model.py — Modelo Mangue para DisSModel
===============================================================
Tradução fiel do mangue.lua para DisSModel + RasterBackend.
"""
from __future__ import annotations

import numpy as np
from dissmodel.geo.raster_model import RasterModel
from dissmodel.geo.raster_backend import RasterBackend

from coastal_dynamics.common.constants import (
    MANGUE, MANGUE_MIGRADO, VEGETACAO_TERRESTRE, SOLO_DESCOBERTO,
    USOS_INUNDADOS,
    SOLO_MANGUE, SOLO_MANGUE_MIGRADO, SOLO_CANAL_FLUVIAL,
)


class MangroveModel(RasterModel):
    """
    Mangue (mangue.lua) → DisSModel + RasterBackend.

    Parâmetros
    ----------
    backend        : RasterBackend com arrays "uso", "alt", "solo"
    taxa_elevacao  : m/ano — IPCC RCP8.5 = 0.011
    altura_mare    : AIM base em metros. Padrão: 6.0
    acrecao_ativa  : habilita aplicarAcrecao (Alongi 2008). Padrão: False
    """

    SOLOS_FONTE  = [SOLO_MANGUE, SOLO_MANGUE_MIGRADO, SOLO_CANAL_FLUVIAL]
    SOLOS_MANGUE = [SOLO_MANGUE, SOLO_MANGUE_MIGRADO]
    USOS_FONTE   = [MANGUE, MANGUE_MIGRADO]
    USOS_ALVO    = [VEGETACAO_TERRESTRE, SOLO_DESCOBERTO]
    COEF_A, COEF_B = 1.693, 0.939   # Alongi 2008

    def setup(
        self,
        backend:       RasterBackend,
        taxa_elevacao: float = 0.011,
        altura_mare:   float = 6.0,
        acrecao_ativa: bool  = False,
    ) -> None:
        super().setup(backend)
        self.taxa_elevacao = taxa_elevacao
        self.altura_mare   = altura_mare
        self.acrecao_ativa = acrecao_ativa

        self.mangue_migrado = 0
        self.solo_migrado   = 0

    def execute(self) -> None:
        nivel_mar = self.env.now() * self.taxa_elevacao
        zi        = self.altura_mare + nivel_mar
        taxa_ac   = self.COEF_A / 1000.0 + self.COEF_B * nivel_mar

        uso_past  = self.backend.get("uso").copy()
        alt_past  = self.backend.get("alt").copy()
        solo_past = self.backend.get("solo").copy()

        # ── migrarSolos ───────────────────────────────────────────────────────
        eh_fonte_solo = np.isin(solo_past, self.SOLOS_FONTE)
        solo_novo     = solo_past.copy()

        for dr, dc in self.dirs:
            fonte_viz = self.shift(eh_fonte_solo.astype(np.int8), dr, dc) > 0
            cond = (
                fonte_viz
                & np.isin(uso_past,  self.USOS_ALVO)
                & (solo_past != SOLO_MANGUE_MIGRADO)
                & (alt_past  <= zi)
            )
            solo_novo = np.where(cond, SOLO_MANGUE_MIGRADO, solo_novo)

        # ── migrarUsos — usa solo_past (fiel ao .past do TerraME) ────────────
        eh_fonte_uso = np.isin(uso_past, self.USOS_FONTE)
        uso_novo     = uso_past.copy()

        for dr, dc in self.dirs:
            fonte_viz = self.shift(eh_fonte_uso.astype(np.int8), dr, dc) > 0
            cond = (
                fonte_viz
                & np.isin(uso_past,  self.USOS_ALVO)
                & np.isin(solo_past, self.SOLOS_MANGUE)   # ← solo_past
                & (alt_past <= zi)
            )
            uso_novo = np.where(cond, MANGUE_MIGRADO, uso_novo)

        # ── aplicarAcrecao (False por padrão) ─────────────────────────────────
        if self.acrecao_ativa:
            cond_ac = (
                np.isin(solo_past, self.SOLOS_MANGUE)
                & ~np.isin(uso_past, USOS_INUNDADOS)
            )
            self.backend.arrays["alt"] = np.where(cond_ac, alt_past + taxa_ac, alt_past)

        self.backend.arrays["uso"]  = uso_novo
        self.backend.arrays["solo"] = solo_novo

        self.mangue_migrado = int(np.sum(uso_novo  == MANGUE_MIGRADO))
        self.solo_migrado   = int(np.sum(solo_novo == SOLO_MANGUE_MIGRADO))
