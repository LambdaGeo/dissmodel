"""
brmangue/run_vector.py — Ponto de entrada BR-MANGUE (versão GeoDataFrame)
=========================================================================
Versão vetorial para comparação com run.py (RasterBackend).

Usa FloodVectorModel + MangroveVectorModel + GeoDataFrame + Map/Chart.

Uso
---
    python -m brmangue.run_vector flood_model.shp
    python -m brmangue.run_vector flood_model.gpkg --taxa 0.05
    python -m brmangue.run_vector flood_model.shp --chart
    python -m brmangue.run_vector flood_model.shp --acrecao --no-save
"""
from __future__ import annotations

import argparse
import pathlib

import geopandas as gpd
from matplotlib.colors import ListedColormap, BoundaryNorm

from dissmodel.core import Environment
from dissmodel.visualization import Map, Chart

from coastal_dynamics.common.constants import (
    USO_COLORS, USO_LABELS,
    SOLO_COLORS, SOLO_LABELS,
)
from examples.cli.coastal_dynamics.vector.flood_model import FloodVectorModel
from examples.cli.coastal_dynamics.vector.mangue_model import MangroveModel


# ── configuração ──────────────────────────────────────────────────────────────

TAXA_ELEVACAO = 0.011
ALTURA_MARE   = 6.0
END_TIME      = 88

_vals    = sorted(USO_COLORS)
USO_CMAP = ListedColormap([USO_COLORS[k] for k in _vals])
USO_NORM = BoundaryNorm([v - 0.5 for v in _vals] + [_vals[-1] + 0.5], USO_CMAP.N)

_svals    = sorted(SOLO_COLORS)
SOLO_CMAP = ListedColormap([SOLO_COLORS[k] for k in _svals])
SOLO_NORM = BoundaryNorm([v - 0.5 for v in _svals] + [_svals[-1] + 0.5], SOLO_CMAP.N)


# ── main ──────────────────────────────────────────────────────────────────────

def run(
    shp_path:      str | pathlib.Path,
    taxa_elevacao: float = TAXA_ELEVACAO,
    altura_mare:   float = ALTURA_MARE,
    acrecao_ativa: bool  = False,
    attr_uso:      str   = "uso",
    attr_alt:      str   = "alt",
    attr_solo:     str   = "solo",
    show_chart:    bool  = False,
    save:          bool  = True,
) -> None:
    shp_path = pathlib.Path(shp_path)

    # ── carrega ───────────────────────────────────────────────────────────────
    print(f"Carregando {shp_path}...")
    gdf = gpd.read_file(shp_path)
    print(f"  features={len(gdf)}  crs={gdf.crs}")

    # ── ambiente ──────────────────────────────────────────────────────────────
    env = Environment(start_time=1, end_time=END_TIME)

    # ── modelos — compartilham o mesmo gdf ────────────────────────────────────
    # Ordem de instanciação = ordem de execução por passo
    FloodVectorModel(
        gdf           = gdf,
        taxa_elevacao = taxa_elevacao,
        attr_uso      = attr_uso,
        attr_alt      = attr_alt,
    )
    MangroveModel(
        gdf           = gdf,
        taxa_elevacao = taxa_elevacao,
        altura_mare   = altura_mare,
        acrecao_ativa = acrecao_ativa,
        attr_uso      = attr_uso,
        attr_alt      = attr_alt,
        attr_solo     = attr_solo,
    )

    # ── visualização ──────────────────────────────────────────────────────────
    Map(gdf=gdf, plot_params={"column": attr_uso,  "cmap": USO_CMAP,  "norm": USO_NORM,  "legend": False})
    Map(gdf=gdf, plot_params={"column": attr_alt,  "cmap": "terrain", "legend": True})
    Map(gdf=gdf, plot_params={"column": attr_solo, "cmap": SOLO_CMAP, "norm": SOLO_NORM, "legend": False})

    if show_chart:
        Chart(select={"celulas_inundadas", "mangue_migrado"})

    # ── execução ──────────────────────────────────────────────────────────────
    print(f"Executando passos 1 → {END_TIME}...")
    env.run()
    print("Concluído.")

    # ── salva ─────────────────────────────────────────────────────────────────
    if save:
        out_path = shp_path.with_name(shp_path.stem + "_resultado.gpkg")
        gdf.to_file(out_path, driver="GPKG", layer="flood_vector")
        print(f"Salvo: {out_path}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="python -m brmangue.run_vector",
        description="Simulação BR-MANGUE — versão GeoDataFrame",
    )
    p.add_argument("shp", help="Shapefile ou GeoPackage de entrada")
    p.add_argument(
        "--taxa", type=float, default=TAXA_ELEVACAO, metavar="M/ANO",
        help=f"Taxa de elevação do mar em m/ano (padrão: {TAXA_ELEVACAO})",
    )
    p.add_argument(
        "--altura-mare", type=float, default=ALTURA_MARE, metavar="M",
        help=f"AIM base em metros (padrão: {ALTURA_MARE})",
    )
    p.add_argument(
        "--acrecao", action="store_true",
        help="Ativa aplicarAcrecao no MangroveVectorModel (Alongi 2008)",
    )
    p.add_argument(
        "--attr-uso",  default="uso",  metavar="COL",
        help="Coluna de uso do solo (padrão: uso)",
    )
    p.add_argument(
        "--attr-alt",  default="alt",  metavar="COL",
        help="Coluna de altitude (padrão: alt)",
    )
    p.add_argument(
        "--attr-solo", default="solo", metavar="COL",
        help="Coluna de tipo de solo (padrão: solo)",
    )
    p.add_argument(
        "--chart", action="store_true",
        help="Exibe gráfico de métricas por passo",
    )
    p.add_argument(
        "--no-save", dest="save", action="store_false",
        help="Não salva GeoPackage de resultado",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run(
        shp_path      = args.shp,
        taxa_elevacao = args.taxa,
        altura_mare   = args.altura_mare,
        acrecao_ativa = args.acrecao,
        attr_uso      = args.attr_uso,
        attr_alt      = args.attr_alt,
        attr_solo     = args.attr_solo,
        show_chart    = args.chart,
        save          = args.save,
    )
