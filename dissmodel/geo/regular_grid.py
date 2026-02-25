
import geopandas as gpd
import numpy as np
from shapely.geometry import box

import matplotlib.pyplot as plt
import rasterio


def parse_idx(idx: str) -> tuple[int, int]:
    """
    Extrai x e y a partir de um índice no formato 'y-x'.

    Args:
        idx (str): Índice no formato 'y-x', como '0-0', '3-4', etc.

    Returns:
        tuple[int, int]: (x, y) como inteiros
    """
    y_str, x_str = idx.split("-")
    return int(x_str), int(y_str)

def regular_grid(gdf=None, bounds=None, resolution=None, dimension=None, attrs={}, crs=None):
    """
    Cria um grid regular com células de tamanho fixo (homogêneo), baseado em:
    - Um GeoDataFrame (para pegar os bounds)
    - Um bounds manual
    - Apenas a dimensão e resolução (sem localização geográfica)

    Args:
        gdf (GeoDataFrame, optional): Para extrair os bounds.
        bounds (tuple, optional): (xmin, ymin, xmax, ymax).
        resolution (float, optional): Tamanho das células.
        dimension (tuple, optional): Número de colunas e linhas (n_cols, n_rows).
        attrs (dict): Atributos extras.
        crs (str): CRS (opcional; se None, será um grid abstrato).

    Returns:
        GeoDataFrame: Grade regular como GeoDataFrame.
    """
    import numpy as np
    import geopandas as gpd
    from shapely.geometry import box

    if dimension is not None and resolution is not None:
        n_cols, n_rows = dimension
        xmin, ymin = 0, 0
        resolution_x = resolution_y = resolution
        xmax = xmin + n_cols * resolution_x
        ymax = ymin + n_rows * resolution_y
    elif bounds is not None:
        xmin, ymin, xmax, ymax = bounds
        width = xmax - xmin
        height = ymax - ymin
        if resolution is not None:
            resolution_x = resolution_y = resolution
            n_cols = int(np.ceil(width / resolution_x))
            n_rows = int(np.ceil(height / resolution_y))
        elif dimension is not None:
            n_cols, n_rows = dimension
            resolution_x = width / n_cols
            resolution_y = height / n_rows
        else:
            raise ValueError("Informe `resolution` ou `dimension`.")
    elif gdf is not None:
        return regular_grid(bounds=gdf.total_bounds, resolution=resolution, dimension=dimension, attrs=attrs, crs=gdf.crs)
    else:
        raise ValueError("Informe `gdf`, `bounds` ou `dimension` com `resolution`.")

    x_edges = np.arange(xmin, xmax, resolution_x)
    y_edges = np.arange(ymin, ymax, resolution_y)

    grid_cells = []
    ids = []
    for i, x0 in enumerate(x_edges):
        for j, y0 in enumerate(y_edges):
            x1, y1 = x0 + resolution_x, y0 + resolution_y
            poly = box(x0, y0, x1, y1)
            grid_cells.append(poly)
            ids.append(f"{j}-{i}")

    data = {"geometry": grid_cells, "id": ids}
    for key, value in attrs.items():
        data[key] = [value] * len(grid_cells)

    grid_gdf = gpd.GeoDataFrame(data, crs=crs).set_index("id")
    return grid_gdf
