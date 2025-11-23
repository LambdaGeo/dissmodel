import json
from pathlib import Path
from libpysal.weights import W


def attach_neighbors(gdf, strategy=None, neighbors_dict=None, *args, **kwargs):
    """
    Anexa os vizinhos a um GeoDataFrame, usando uma estratégia de vizinhança ou um dicionário/arquivo JSON.

    Retorna o próprio GeoDataFrame com a coluna "_neighs".

    Parâmetros:
    - gdf: GeoDataFrame
    - strategy: ex: Queen, Rook (de libpysal)
    - neighbors_dict: dict ou caminho para JSON com as vizinhanças
    - *args, **kwargs: passados para `strategy.from_dataframe`
    """
    if isinstance(neighbors_dict, str) and Path(neighbors_dict).is_file():
        with open(neighbors_dict) as f:
            neighbors_dict = json.load(f)
    elif neighbors_dict is not None and not isinstance(neighbors_dict, dict):
        raise ValueError("`neighbors_dict` deve ser um dicionário ou caminho para arquivo JSON.")

    if neighbors_dict:
        w = W(neighbors_dict)
    else:
        if strategy is None:
            raise ValueError("Informe uma strategy ou neighbors_dict.")
        w = strategy.from_dataframe(gdf, *args, **kwargs)

    gdf["_neighs"] = gdf.index.map(lambda idx: w.neighbors.get(idx, []))
    return gdf
