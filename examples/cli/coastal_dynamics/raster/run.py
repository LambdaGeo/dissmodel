"""
brmangue/run.py — Ponto de entrada BR-MANGUE
=============================================
Acopla FloodRasterModel + MangueRasterModel + RasterMap no mesmo
Environment DisSModel, compartilhando um RasterBackend.

Ordem de execução por passo (ordem de instanciação):
    1. FloodRasterModel   — Hidro: altimetria + inundação
    2. MangueRasterModel  — Mangue: migração solo/uso + acreção
    3. RasterMap(uso)     — visualização

Uso
---
    python -m brmangue.run flood_p000_0.000m.tif

    # modo interativo (requer display):
    RASTER_MAP_INTERACTIVE=1 python -m brmangue.run flood_p000_0.000m.tif

    # múltiplos mapas:
    python -m brmangue.run flood_p000_0.000m.tif --bands uso alt solo

    # sem salvar resultado:
    python -m brmangue.run flood_p000_0.000m.tif --no-save
"""
from __future__ import annotations

import argparse
import pathlib
import sys

from dissmodel.core import Environment
from dissmodel.visualization.raster_map import RasterMap

from coastal_dynamics.common.constants import (
    USO_COLORS, USO_LABELS,
    SOLO_COLORS, SOLO_LABELS,
    MAR,TIFF_BANDS, CRS
)
#from raster_io import carregar_tiff, salvar_tiff

from dissmodel.geo.raster_io import load_geotiff, save_geotiff


from coastal_dynamics.raster.flood_model import FloodModel
from coastal_dynamics.raster.mangrove_model import MangroveModel


# ── configuração da simulação ─────────────────────────────────────────────────

TAXA_ELEVACAO = 0.011   # m/ano — IPCC RCP8.5
ALTURA_MARE   = 6.0     # AIM base em metros
END_TIME      = 88      # passos (2012–2100)

# definição visual por band — passada ao RasterMap genérico do dissmodel
BAND_CONFIG: dict[str, dict] = {
    "uso": dict(
        color_map = USO_COLORS,
        labels    = USO_LABELS,
        title     = "Uso do Solo",
    ),
    "solo": dict(
        color_map = SOLO_COLORS,
        labels    = SOLO_LABELS,
        title     = "Solo",
    ),
    "alt": dict(
        cmap            = "terrain",
        colorbar_label  = "Altitude (m)",
        mask_band       = "uso",
        mask_value      = MAR,
        title           = "Altimetria",
    ),
}


# ── main ──────────────────────────────────────────────────────────────────────

def run(
    tif_path:      str | pathlib.Path,
    bands:         list[str]  = ("uso",),
    acrecao_ativa: bool       = False,
    save:          bool       = True,
) -> None:
    tif_path = pathlib.Path(tif_path)

    # ── carrega estado inicial ────────────────────────────────────────────────
    print(f"Carregando {tif_path}...")
    backend, meta = load_geotiff(
        tif_path,
        band_spec=TIFF_BANDS
    )

    tags = meta.get("tags", {})

    print(
        f"  shape={backend.shape}  "
        f"passo={tags.get('passo',0)}  "
        f"nivel_mar={tags.get('nivel_mar',0)}m  "
        f"crs={meta['crs']}"
    )

    start = int(tags.get("passo", 0)) + 1

    env   = Environment(start_time=start, end_time=END_TIME)

    # ── modelos — compartilham o mesmo backend ────────────────────────────────
    FloodModel(
        backend       = backend,
        taxa_elevacao = TAXA_ELEVACAO,
        aim_base      = ALTURA_MARE,
    )
    MangroveModel(
        backend       = backend,
        taxa_elevacao = TAXA_ELEVACAO,
        altura_mare   = ALTURA_MARE,
        acrecao_ativa = acrecao_ativa,
    )

    # ── visualização — um RasterMap por band solicitado ───────────────────────
    for band in bands:
        if band not in BAND_CONFIG:
            print(f"  aviso: band '{band}' sem configuração visual — usando viridis")
        RasterMap(backend=backend, band=band, **BAND_CONFIG.get(band, {}))

    # ── execução ──────────────────────────────────────────────────────────────
    print(f"Executando passos {start} → {END_TIME}...")
    env.run()
    print("Concluído.")

    # ── salva estado final ────────────────────────────────────────────────────
    if save:

        nivel_mar_final = END_TIME * TAXA_ELEVACAO

        out_path = tif_path.with_name(
            tif_path.stem + "_resultado.tif"
        )

        save_geotiff(
            backend,
            out_path,
            band_spec=TIFF_BANDS,
            crs=CRS,
            transform=meta["transform"],
        )

        print(f"Salvo: {out_path}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="python -m brmangue.run",
        description="Simulação BR-MANGUE via DisSModel",
    )
    p.add_argument("tif", help="GeoTIFF de entrada (estado inicial)")
    p.add_argument(
        "--bands", nargs="+", default=["uso"],
        choices=list(BAND_CONFIG), metavar="BAND",
        help="Bands a visualizar: uso solo alt (padrão: uso)",
    )
    p.add_argument(
        "--acrecao", action="store_true",
        help="Ativa aplicarAcrecao no MangueRasterModel (Alongi 2008)",
    )
    p.add_argument(
        "--no-save", dest="save", action="store_false",
        help="Não salva GeoTIFF de resultado",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run(
        tif_path      = args.tif,
        bands         = args.bands,
        acrecao_ativa = args.acrecao,
        save          = args.save,
    )
