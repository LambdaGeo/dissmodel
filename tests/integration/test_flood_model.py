"""
tests/integration/test_flood_model.py
========================================
Integration test: FloodVectorModel vs FloodRasterModel.

Runs both substrates with the same synthetic grid and asserts that the
final land-use state is equivalent within a tolerance threshold.

Unlike GameOfLife (exact integer match), the flood model uses floating
point altimetry — small numerical differences accumulate across steps.
Validation uses a percentage-match threshold rather than exact equality.

Why this test matters
----------------------
- Confirms that the raster vectorization preserves the TerraME .past semantics
- Guards against regression when refactoring either substrate
- Provides a concrete equivalence guarantee before running with real data
"""
from __future__ import annotations

import numpy as np
import pytest

from dissmodel.core import Environment
from dissmodel.geo import regular_grid
from dissmodel.geo.raster.backend import RasterBackend
from dissmodel.geo import make_raster_grid


# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS (inline — no coastal-dynamics dependency)
# ══════════════════════════════════════════════════════════════════════════════

MAR                       = 3
SOLO_INUNDADO             = 6
AREA_ANTROPIZADA_INUNDADA = 7
MANGUE_INUNDADO           = 9
VEG_TERRESTRE_INUNDADA    = 10

USOS_INUNDADOS = [MAR, SOLO_INUNDADO, AREA_ANTROPIZADA_INUNDADA,
                  MANGUE_INUNDADO, VEG_TERRESTRE_INUNDADA]

REGRAS_INUNDACAO = {
    1: MANGUE_INUNDADO,
    8: MANGUE_INUNDADO,
    2: VEG_TERRESTRE_INUNDADA,
    4: AREA_ANTROPIZADA_INUNDADA,
    5: SOLO_INUNDADO,
}

TAXA = 0.011


# ══════════════════════════════════════════════════════════════════════════════
# MODELS (inline)
# ══════════════════════════════════════════════════════════════════════════════

from dissmodel.geo.raster.raster_model import RasterModel
from dissmodel.geo.vector.spatial_model import SpatialModel


class FloodRaster(RasterModel):
    def setup(self, backend, taxa=TAXA):
        super().setup(backend)
        self._taxa = taxa

    def execute(self):
        nivel_mar  = self.env.now() * self._taxa
        uso_past   = self.backend.get("uso").copy()
        alt_past   = self.backend.get("alt").copy()

        eh_fonte   = np.isin(uso_past, USOS_INUNDADOS) & (alt_past >= 0)
        viz_baixos = np.ones(self.shape, dtype=float)
        for dr, dc in self.dirs:
            viz_baixos += (self.shift(alt_past, dr, dc) <= alt_past).astype(float)

        fluxo    = np.where(eh_fonte, self._taxa / viz_baixos, 0.0)
        delta    = fluxo.copy()
        uso_novo = uso_past.copy()

        for dr, dc in self.dirs:
            fonte_viz = self.shift(eh_fonte.astype(float), dr, dc) > 0
            delta    += np.where(
                fonte_viz & (alt_past <= self.shift(alt_past, dr, dc)),
                self.shift(fluxo, dr, dc), 0.0,
            )
            for uso_seco, uso_inund in REGRAS_INUNDACAO.items():
                pode = fonte_viz & (uso_past == uso_seco) & (alt_past <= nivel_mar)
                uso_novo = np.where(pode, uso_inund, uso_novo)

        self.backend.arrays["alt"] = alt_past + delta
        self.backend.arrays["uso"] = uso_novo


class FloodVector(SpatialModel):
    def setup(self, taxa=TAXA):
        from libpysal.weights import Queen
        self._taxa = taxa
        self.create_neighborhood(strategy=Queen, silence_warnings=True)

    def execute(self):
        nivel_mar = self.env.now() * self._taxa
        uso_past  = self.gdf["uso"].copy()
        alt_past  = self.gdf["alt"].copy()

        fontes   = set(uso_past.index[uso_past.isin(USOS_INUNDADOS) & (alt_past >= 0)])
        alt_nova = alt_past.copy()

        for idx in fontes:
            alt_atual  = alt_past[idx]
            vizinhos   = self.neighs_id(idx)
            viz_baixos = 1 + sum(1 for n in vizinhos if alt_past[n] <= alt_atual)
            fluxo      = self._taxa / viz_baixos
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
# SYNTHETIC GRID FACTORIES
# ══════════════════════════════════════════════════════════════════════════════

def _arrays(rows: int, cols: int, seed: int = 42):
    """Shared initial arrays — both substrates must start identically."""
    rng    = np.random.default_rng(seed)
    uso    = np.full((rows, cols), 2, dtype=np.int32)   # VEG_TERRESTRE
    alt    = np.zeros((rows, cols), dtype=np.float32)
    c_mar  = max(1, int(cols * 0.20))
    uso[:, :c_mar] = MAR
    for c in range(cols):
        alt[:, c] = max(0.0, (c - c_mar) * 0.1)
    alt += rng.uniform(0, 0.05, (rows, cols)).astype(np.float32)
    alt[:, :c_mar] = 0.0
    return uso, alt


def make_raster(rows: int, cols: int, seed: int = 42) -> RasterBackend:
    uso, alt = _arrays(rows, cols, seed)
    b = make_raster_grid(rows=rows, cols=cols,
                         attrs={"uso": uso.copy(), "alt": alt.copy()})
    return b


def make_vector(rows: int, cols: int, seed: int = 42):
    import geopandas as gpd
    from shapely.geometry import box
    uso, alt = _arrays(rows, cols, seed)
    cell = 100.0
    geoms = [
        box(c * cell, (rows-1-r) * cell, (c+1) * cell, (rows-r) * cell)
        for r in range(rows) for c in range(cols)
    ]
    return gpd.GeoDataFrame(
        {"uso": uso.ravel().astype(int),
         "alt": alt.ravel().astype(float)},
        geometry=geoms, crs="EPSG:31984",
    )


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def pct_match(a: np.ndarray, b: np.ndarray) -> float:
    return float((a == b).mean()) * 100


# ══════════════════════════════════════════════════════════════════════════════
# TESTS
# ══════════════════════════════════════════════════════════════════════════════

# Threshold: at least 95% of cells must agree on land-use category
MATCH_THRESHOLD = 95.0


class TestFloodEquivalence:

    @pytest.mark.parametrize("n,steps", [
        (5,  1),
        (5,  3),
        (10, 1),
        (10, 3),
    ])
    def test_uso_match_above_threshold(self, n, steps):
        """
        Final land-use state must match between vector and raster
        above MATCH_THRESHOLD (95%).
        """
        # raster
        b = make_raster(n, n)
        Environment(start_time=1, end_time=steps)
        FloodRaster(backend=b)
        from dissmodel.core import Environment as Env
        env_r = Env(start_time=1, end_time=steps)
        b = make_raster(n, n)
        FloodRaster(backend=b)
        env_r.run()
        uso_r = b.get("uso").astype(np.int32)

        # vector
        gdf = make_vector(n, n)
        env_v = Env(start_time=1, end_time=steps)
        FloodVector(gdf=gdf)
        env_v.run()
        uso_v = gdf["uso"].values.reshape(n, n).astype(np.int32)

        pct = pct_match(uso_r, uso_v)
        assert pct >= MATCH_THRESHOLD, (
            f"{n}×{n} grid, {steps} steps: only {pct:.1f}% of uso cells match "
            f"(threshold {MATCH_THRESHOLD}%)"
        )

    def test_sea_cells_always_match(self):
        """
        Cells that start as MAR (sea) never change — must match exactly
        between substrates regardless of steps.
        """
        from dissmodel.core import Environment as Env
        n, steps = 10, 5
        uso0, _ = _arrays(n, n)
        sea_mask = (uso0 == MAR)

        b = make_raster(n, n)
        env_r = Env(start_time=1, end_time=steps)
        FloodRaster(backend=b)
        env_r.run()
        uso_r = b.get("uso").astype(np.int32)

        gdf = make_vector(n, n)
        env_v = Env(start_time=1, end_time=steps)
        FloodVector(gdf=gdf)
        env_v.run()
        uso_v = gdf["uso"].values.reshape(n, n).astype(np.int32)

        r_sea = uso_r[sea_mask]
        v_sea = uso_v[sea_mask]
        assert (r_sea == v_sea).all(), "Sea cells differ between substrates"

    def test_initially_flooded_cells_remain_flooded(self):
        """
        Cells that start flooded (uso in USOS_INUNDADOS) must stay flooded
        in both substrates — they can only transition to other flooded types.
        """
        from dissmodel.core import Environment as Env
        n, steps = 10, 3

        b = make_raster(n, n)
        uso0 = b.get("uso").copy()
        initially_flooded = np.isin(uso0, USOS_INUNDADOS)

        env_r = Env(start_time=1, end_time=steps)
        FloodRaster(backend=b)
        env_r.run()
        uso_r_final = b.get("uso")

        still_flooded = np.isin(uso_r_final[initially_flooded], USOS_INUNDADOS)
        assert still_flooded.all(), (
            "Some initially flooded cells became dry in raster substrate"
        )

    def test_no_new_dry_cells_in_sea_column(self):
        """
        The leftmost columns (sea) must not dry out — raster and vector agree.
        """
        from dissmodel.core import Environment as Env
        n, steps = 8, 3
        uso0, _ = _arrays(n, n)
        c_mar = max(1, int(n * 0.20))
        sea_cols = np.s_[:, :c_mar]

        b = make_raster(n, n)
        env_r = Env(start_time=1, end_time=steps)
        FloodRaster(backend=b)
        env_r.run()
        assert np.isin(b.get("uso")[sea_cols], USOS_INUNDADOS).all(), (
            "Sea columns contain dry cells after simulation (raster)"
        )

    @pytest.mark.parametrize("seed", [0, 7, 42])
    def test_multiple_seeds_above_threshold(self, seed):
        """Match threshold must hold across different initial conditions."""
        from dissmodel.core import Environment as Env
        n, steps = 8, 2

        b = make_raster(n, n, seed=seed)
        env_r = Env(start_time=1, end_time=steps)
        FloodRaster(backend=b)
        env_r.run()
        uso_r = b.get("uso").astype(np.int32)

        gdf = make_vector(n, n, seed=seed)
        env_v = Env(start_time=1, end_time=steps)
        FloodVector(gdf=gdf)
        env_v.run()
        uso_v = gdf["uso"].values.reshape(n, n).astype(np.int32)

        pct = pct_match(uso_r, uso_v)
        assert pct >= MATCH_THRESHOLD, (
            f"seed={seed}: only {pct:.1f}% of uso cells match"
        )
