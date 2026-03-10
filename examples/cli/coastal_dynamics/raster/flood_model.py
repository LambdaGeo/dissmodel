"""
brmangue/flood_raster_model.py — Modelo Hidro para DisSModel
=============================================================
Tradução fiel do hidro.lua para DisSModel + RasterBackend.
"""
from __future__ import annotations

import numpy as np
from dissmodel.geo.raster_model import RasterModel
from dissmodel.geo.raster_backend import RasterBackend

from coastal_dynamics.common.constants import USOS_INUNDADOS, REGRAS_INUNDACAO, MAR


class FloodModel(RasterModel):
    """
    Hidro (hidro.lua) → DisSModel + RasterBackend.

    Parâmetros
    ----------
    backend       : RasterBackend com arrays "uso" e "alt"
    taxa_elevacao : m/ano — IPCC RCP8.5 = 0.011
    aim_base      : AIM base em metros. Padrão: 6.0
    """

    def setup(
        self,
        backend:       RasterBackend,
        taxa_elevacao: float = 0.011,
        aim_base:      float = 6.0,
    ) -> None:
        super().setup(backend)
        self.taxa_elevacao = taxa_elevacao
        self.aim_base      = aim_base

        self.celulas_inundadas = 0
        self.novas_inundadas   = 0
        self.nivel_mar_atual   = 0.0

    def execute(self) -> None:
        nivel_mar        = self.env.now() * self.taxa_elevacao
        rows, cols       = self.shape
        uso_past         = self.backend.get("uso").copy()
        alt_past         = self.backend.get("alt").copy()

        eh_fonte = np.isin(uso_past, USOS_INUNDADOS) & (alt_past >= 0)

        viz_baixos = np.ones((rows, cols), dtype=float)
        for dr, dc in self.dirs:
            viz_baixos += (self.shift(alt_past, dr, dc) <= alt_past).astype(float)

        fluxo     = np.where(eh_fonte, self.taxa_elevacao / viz_baixos, 0.0)
        delta_alt = fluxo.copy()
        uso_novo  = uso_past.copy()

        for dr, dc in self.dirs:
            fonte_viz = self.shift(eh_fonte.astype(float), dr, dc) > 0
            alt_viz   = self.shift(alt_past, dr, dc)
            fluxo_viz = self.shift(fluxo,    dr, dc)

            # 1. altimetria — condição relativa
            delta_alt += np.where(
                fonte_viz & (alt_past <= alt_viz), fluxo_viz, 0.0
            )
            # 2. inundação — cota absoluta
            for uso_seco, uso_inund in REGRAS_INUNDACAO.items():
                pode = fonte_viz & (uso_past == uso_seco) & (alt_past <= nivel_mar)
                uso_novo = np.where(pode, uso_inund, uso_novo)

        self.backend.arrays["alt"] = alt_past + delta_alt
        self.backend.arrays["uso"] = uso_novo

        inund = np.isin(uso_novo, USOS_INUNDADOS) & (uso_novo != MAR)
        novas = np.isin(uso_novo, USOS_INUNDADOS) & ~np.isin(uso_past, USOS_INUNDADOS)
        self.celulas_inundadas = int(np.sum(inund))
        self.novas_inundadas   = int(np.sum(novas))
        self.nivel_mar_atual   = round(nivel_mar, 4)
