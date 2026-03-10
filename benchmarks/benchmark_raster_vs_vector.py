"""
benchmarks/benchmark_raster_vs_vector.py
==========================================
Benchmark: RasterBackend (NumPy) vs GeoDataFrame (libpysal)

Autocontido — não depende de projetos externos ao dissmodel.
Define um modelo de inundação mínimo inline para isolar a medição
do overhead de cada backend.

Execução
--------
    python benchmarks/benchmark_raster_vs_vector.py
    python benchmarks/benchmark_raster_vs_vector.py --steps 5 --sizes 10 20 50
    python benchmarks/benchmark_raster_vs_vector.py --no-validation
"""
from __future__ import annotations

import argparse
import time
from dataclasses import dataclass, field

import numpy as np
import geopandas as gpd
import pandas as pd
from shapely.geometry import box
from libpysal.weights import Queen

from dissmodel.core import Environment
from dissmodel.geo.raster_backend import RasterBackend, DIRS_MOORE
from dissmodel.geo.raster_model import RasterModel
from dissmodel.geo.spatial_model import SpatialModel


# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES MÍNIMAS (inline — sem dependência externa)
# ══════════════════════════════════════════════════════════════════════════════

MAR                       = 3
SOLO_INUNDADO             = 6
AREA_ANTROPIZADA_INUNDADA = 7
MANGUE_INUNDADO           = 9
VEG_TERRESTRE_INUNDADA    = 10

USOS_INUNDADOS = [MAR, SOLO_INUNDADO, AREA_ANTROPIZADA_INUNDADA,
                  MANGUE_INUNDADO, VEG_TERRESTRE_INUNDADA]

REGRAS_INUNDACAO = {
    1: MANGUE_INUNDADO,          # MANGUE
    8: MANGUE_INUNDADO,          # MANGUE_MIGRADO
    2: VEG_TERRESTRE_INUNDADA,   # VEGETACAO_TERRESTRE
    4: AREA_ANTROPIZADA_INUNDADA,# AREA_ANTROPIZADA
    5: SOLO_INUNDADO,            # SOLO_DESCOBERTO
}

TAXA = 0.011


# ══════════════════════════════════════════════════════════════════════════════
# MODELOS INLINE (mínimos, sem importar projetos externos)
# ══════════════════════════════════════════════════════════════════════════════

class _FloodRaster(RasterModel):
    def setup(self, backend):
        super().setup(backend)

    def execute(self):
        nivel_mar  = self.env.now() * TAXA
        rows, cols = self.shape
        uso_past   = self.backend.get("uso").copy()
        alt_past   = self.backend.get("alt").copy()

        eh_fonte   = np.isin(uso_past, USOS_INUNDADOS) & (alt_past >= 0)
        viz_baixos = np.ones((rows, cols), dtype=float)
        for dr, dc in self.dirs:
            viz_baixos += (self.shift(alt_past, dr, dc) <= alt_past).astype(float)

        fluxo     = np.where(eh_fonte, TAXA / viz_baixos, 0.0)
        delta_alt = fluxo.copy()
        uso_novo  = uso_past.copy()

        for dr, dc in self.dirs:
            fonte_viz = self.shift(eh_fonte.astype(float), dr, dc) > 0
            delta_alt += np.where(
                fonte_viz & (alt_past <= self.shift(alt_past, dr, dc)),
                self.shift(fluxo, dr, dc), 0.0,
            )
            for uso_seco, uso_inund in REGRAS_INUNDACAO.items():
                pode = fonte_viz & (uso_past == uso_seco) & (alt_past <= nivel_mar)
                uso_novo = np.where(pode, uso_inund, uso_novo)

        self.backend.arrays["alt"] = alt_past + delta_alt
        self.backend.arrays["uso"] = uso_novo


class _FloodVector(SpatialModel):
    def setup(self):
        self.create_neighborhood(strategy=Queen, silence_warnings=True)

    def execute(self):
        nivel_mar = self.env.now() * TAXA
        uso_past  = self.gdf["uso"].copy()
        alt_past  = self.gdf["alt"].copy()

        fontes   = set(uso_past.index[uso_past.isin(USOS_INUNDADOS) & (alt_past >= 0)])
        alt_nova = alt_past.copy()

        for idx in fontes:
            alt_atual  = alt_past[idx]
            vizinhos   = self.neighs_id(idx)
            viz_baixos = 1 + sum(1 for n in vizinhos if alt_past[n] <= alt_atual)
            fluxo      = TAXA / viz_baixos
            alt_nova[idx] += fluxo
            for n in vizinhos:
                if alt_past[n] <= alt_atual:
                    alt_nova[n] += fluxo

        self.gdf["alt"] = alt_nova
        uso_novo = uso_past.copy()

        for idx in self.gdf.index:
            uso_atual = uso_past[idx]
            if uso_atual not in REGRAS_INUNDACAO:
                continue
            if alt_past[idx] > nivel_mar:
                continue
            if any(n in fontes for n in self.neighs_id(idx)):
                uso_novo[idx] = REGRAS_INUNDACAO[uso_atual]

        self.gdf["uso"] = uso_novo


# ══════════════════════════════════════════════════════════════════════════════
# GERAÇÃO DE GRADE SINTÉTICA
# ══════════════════════════════════════════════════════════════════════════════

def _arrays(rows: int, cols: int, seed: int = 42) -> dict[str, np.ndarray]:
    rng  = np.random.default_rng(seed)
    uso  = np.full((rows, cols), 2, dtype=np.int16)   # VEG_TERRESTRE
    alt  = np.zeros((rows, cols), dtype=np.float32)
    c_mar = int(cols * 0.20)
    uso[:, :c_mar] = MAR
    for c in range(cols):
        alt[:, c] = max(0.0, (c - c_mar) * 0.1)
    alt += rng.uniform(0, 0.05, (rows, cols)).astype(np.float32)
    alt[:, :c_mar] = 0.0
    return {"uso": uso, "alt": alt}


def _make_backend(rows: int, cols: int) -> RasterBackend:
    b = RasterBackend(shape=(rows, cols))
    for name, arr in _arrays(rows, cols).items():
        b.set(name, arr)
    return b


def _make_gdf(rows: int, cols: int, cell_size: float = 100.0) -> gpd.GeoDataFrame:
    arrs = _arrays(rows, cols)
    geoms = [
        box(c * cell_size, (rows-1-r) * cell_size,
            (c+1) * cell_size, (rows-r) * cell_size)
        for r in range(rows) for c in range(cols)
    ]
    return gpd.GeoDataFrame(
        {"uso": arrs["uso"].ravel().astype(int),
         "alt": arrs["alt"].ravel().astype(float)},
        geometry=geoms, crs="EPSG:31984",
    )


# ══════════════════════════════════════════════════════════════════════════════
# RUNNERS
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Result:
    label:     str
    rows:      int
    cols:      int
    steps:     int
    total_s:   float
    uso_final: np.ndarray = field(repr=False)

    @property
    def ms_per_step(self) -> float:
        return self.total_s / self.steps * 1000


def run_raster(n: int, steps: int) -> Result:
    backend = _make_backend(n, n)
    env     = Environment(start_time=1, end_time=steps)
    _FloodRaster(backend=backend)
    t0 = time.perf_counter()
    env.run()
    return Result("raster", n, n, steps,
                  time.perf_counter() - t0,
                  backend.get("uso").copy())


def run_vector(n: int, steps: int) -> Result:
    gdf = _make_gdf(n, n)
    env = Environment(start_time=1, end_time=steps)
    _FloodVector(gdf=gdf)
    t0 = time.perf_counter()
    env.run()
    return Result("vector", n, n, steps,
                  time.perf_counter() - t0,
                  gdf["uso"].values.reshape(n, n).astype(np.int16))


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

VECTOR_MAX_CELLS = 10_000   # acima disso vetor é impraticável

def benchmark(sizes: list[int], steps: int, validate: bool) -> None:
    rows_data = []

    for n in sizes:
        cells = n * n
        print(f"\n── {n}×{n} ({cells:,} células, {steps} passos) ──")

        print(f"  raster ... ", end="", flush=True)
        r = run_raster(n, steps)
        print(f"{r.total_s:.3f}s  ({r.ms_per_step:.1f} ms/passo)")

        row = {
            "grid":      f"{n}×{n}",
            "cells":     cells,
            "raster_ms": round(r.ms_per_step, 2),
            "vector_ms": "—",
            "speedup":   "—",
            "identical": "—",
        }

        if cells <= VECTOR_MAX_CELLS:
            print(f"  vector ... ", end="", flush=True)
            v = run_vector(n, steps)
            print(f"{v.total_s:.3f}s  ({v.ms_per_step:.1f} ms/passo)")

            speedup = v.total_s / r.total_s if r.total_s > 0 else float("inf")
            print(f"  speedup:    {speedup:.0f}×")

            if validate:
                match = r.uso_final == v.uso_final
                pct   = float(match.mean()) * 100
                ok    = bool(match.all())
                print(f"  validação: {'✅ idêntico' if ok else f'⚠️  {pct:.1f}% iguais'}")
                row["identical"] = "yes" if ok else f"{pct:.1f}%"

            row["vector_ms"] = round(v.ms_per_step, 2)
            row["speedup"]   = f"{speedup:.0f}×"
        else:
            print(f"  vector:    skipped (>{VECTOR_MAX_CELLS:,} células)")

        rows_data.append(row)

    print("\n" + "═" * 60)
    print("RESUMO")
    print("═" * 60)
    print(pd.DataFrame(rows_data).to_string(index=False))
    print()


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Benchmark RasterBackend vs GeoDataFrame")
    p.add_argument("--sizes", nargs="+", type=int, default=[10, 50, 100, 200, 500])
    p.add_argument("--steps", type=int, default=10)
    p.add_argument("--no-validation", dest="validate", action="store_false")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    benchmark(sizes=args.sizes, steps=args.steps, validate=args.validate)
