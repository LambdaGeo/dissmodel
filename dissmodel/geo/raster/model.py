"""
dissmodel/geo/raster_model.py
==============================
Classe base para modelos com suporte a RasterBackend (NumPy 2D).

Análogo a SpatialModel para o substrato raster — provê infraestrutura
sem impor contrato de regra de transição.

Hierarquia
----------
    Model  (dissmodel.core)
      ├── SpatialModel     gdf + vizinhança Queen/Rook  (vetor)
      └── RasterModel      backend + shift2d            (raster)  ← este arquivo
            ├── FloodRasterModel
            └── MangueRasterModel

Uso
---
    class MeuModeloRaster(RasterModel):
        def setup(self, backend, meu_param=1.0):
            super().setup(backend)
            self.meu_param = meu_param

        def execute(self):
            uso = self.backend.get("uso").copy()
            ...
            self.backend.arrays["uso"] = uso_novo
"""
from __future__ import annotations


from dissmodel.core import Model
from dissmodel.geo.raster.backend import RasterBackend, DIRS_MOORE


class RasterModel(Model):
    """
    Model com suporte a RasterBackend.

    Subclasse de Model que acrescenta infraestrutura raster sem impor
    contrato de regra de transição. Pode ser herdada diretamente por
    qualquer modelo que opere sobre arrays NumPy 2D.

    Parâmetros (setup)
    ------------------
    backend : RasterBackend
        Backend compartilhado entre os modelos do mesmo Environment.

    Atributos disponíveis nas subclasses
    -------------------------------------
    self.backend    : RasterBackend
    self.shape      : (rows, cols) — atalho para self.backend.shape
    self.shift      : atalho para RasterBackend.shift2d (método estático)
    self.dirs       : DIRS_MOORE — as 8 direções da vizinhança de Moore
    """

    def setup(self, backend: RasterBackend) -> None:
        self.backend = backend
        self.shape   = backend.shape
        self.shift   = RasterBackend.shift2d
        self.dirs    = DIRS_MOORE
