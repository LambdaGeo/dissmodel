import json
from pathlib import Path
from typing import Any, Protocol

import geopandas as gpd
from libpysal.weights import W


class WeightStrategy(Protocol):
    """
    Protocolo que define o contrato esperado de uma estratégia de vizinhança da libpysal.

    Qualquer classe que implemente `from_dataframe` satisfaz este protocolo
    estruturalmente, sem necessidade de herança explícita.

    Examples:
        >>> from libpysal.weights import Queen, Rook
        >>> # Queen e Rook satisfazem WeightStrategy automaticamente
    """

    @classmethod
    def from_dataframe(cls, gdf: gpd.GeoDataFrame, *args: Any, **kwargs: Any) -> W:
        ...


def attach_neighbors(
    gdf: gpd.GeoDataFrame,
    strategy: WeightStrategy | None = None,
    neighbors_dict: dict | str | None = None,
    *args: Any,
    **kwargs: Any,
) -> gpd.GeoDataFrame:
    """
    Anexa os vizinhos a um GeoDataFrame, usando uma estratégia de vizinhança
    ou um dicionário/arquivo JSON pré-computado.

    Adiciona a coluna '_neighs' ao GeoDataFrame com os índices dos vizinhos
    de cada célula, e retorna o próprio GeoDataFrame modificado in-place.

    Parameters:
        gdf (GeoDataFrame): GeoDataFrame cujas células receberão a coluna de vizinhança.
        strategy (WeightStrategy | None): Classe de vizinhança da libpysal, ex: Queen, Rook.
            Deve implementar o método `from_dataframe`. Ignorado se `neighbors_dict`
            for fornecido.
        neighbors_dict (dict | str | None): Vizinhanças pré-computadas. Pode ser:
            - dict: mapeamento {índice: [vizinhos]}.
            - str: caminho para um arquivo JSON com o mesmo formato.
            - None: a vizinhança será calculada via `strategy`.
        *args: Argumentos posicionais extras passados a `strategy.from_dataframe`.
        **kwargs: Argumentos nomeados extras passados a `strategy.from_dataframe`.

    Returns:
        GeoDataFrame: O mesmo `gdf` recebido, com a coluna '_neighs' adicionada.

    Raises:
        ValueError: Se `neighbors_dict` não for dict nem caminho para JSON válido.
        ValueError: Se nem `strategy` nem `neighbors_dict` forem fornecidos.
        FileNotFoundError: Se o caminho fornecido em `neighbors_dict` não existir.

    Examples:
        >>> from libpysal.weights import Queen
        >>> gdf = attach_neighbors(gdf, strategy=Queen)
        >>> gdf = attach_neighbors(gdf, neighbors_dict="vizinhanca.json")
        >>> gdf = attach_neighbors(gdf, strategy=Rook, ids="cell_id")
    """
    if isinstance(neighbors_dict, str):
        path = Path(neighbors_dict)
        if not path.is_file():
            raise FileNotFoundError(f"Arquivo de vizinhança não encontrado: {neighbors_dict}")
        with open(path) as f:
            neighbors_dict = json.load(f)
    elif neighbors_dict is not None and not isinstance(neighbors_dict, dict):
        raise ValueError("`neighbors_dict` deve ser um dicionário ou caminho para arquivo JSON.")

    if neighbors_dict:
        w = W(neighbors_dict)
    else:
        if strategy is None:
            raise ValueError("Informe uma `strategy` ou `neighbors_dict`.")
        w = strategy.from_dataframe(gdf, *args, **kwargs)

    gdf["_neighs"] = gdf.index.map(lambda idx: w.neighbors.get(idx, []))
    return gdf


def get_neighbors(gdf: gpd.GeoDataFrame, idx: Any) -> list:
    """
    Retorna os índices dos vizinhos de uma célula específica.

    Parameters:
        gdf (GeoDataFrame): GeoDataFrame com a coluna '_neighs' já populada.
        idx: Índice da célula de interesse.

    Returns:
        list: Lista de índices dos vizinhos. Retorna lista vazia se não houver vizinhos.

    Raises:
        KeyError: Se `idx` não existir no GeoDataFrame.
        ValueError: Se a coluna '_neighs' ainda não tiver sido gerada via `attach_neighbors`.

    Examples:
        >>> get_neighbors(gdf, "10-5")
        ['9-5', '11-5', '10-4', '10-6']
    """
    if "_neighs" not in gdf.columns:
        raise ValueError("Coluna '_neighs' não encontrada. Execute `attach_neighbors` primeiro.")
    if idx not in gdf.index:
        raise KeyError(f"Índice '{idx}' não encontrado no GeoDataFrame.")
    return gdf.at[idx, "_neighs"]


def get_neighbor_values(gdf: gpd.GeoDataFrame, idx: Any, attr: str) -> list:
    """
    Retorna os valores de um atributo para todos os vizinhos de uma célula.

    Parameters:
        gdf (GeoDataFrame): GeoDataFrame com a coluna '_neighs' já populada.
        idx: Índice da célula de interesse.
        attr (str): Nome do atributo cujos valores serão coletados.

    Returns:
        list: Valores do atributo nos vizinhos, na mesma ordem de '_neighs'.

    Raises:
        ValueError: Se '_neighs' não existir.
        KeyError: Se `idx` ou `attr` não existirem no GeoDataFrame.

    Examples:
        >>> get_neighbor_values(gdf, "10-5", "land_use")
        [1, 1, 2, 1]
    """
    neighbors = get_neighbors(gdf, idx)
    if attr not in gdf.columns:
        raise KeyError(f"Atributo '{attr}' não encontrado no GeoDataFrame.")
    return gdf.loc[neighbors, attr].tolist()


def export_neighbors(gdf: gpd.GeoDataFrame, path: str) -> None:
    """
    Exporta a vizinhança do GeoDataFrame para um arquivo JSON.

    Útil para persistir vizinhanças computadas e reutilizá-las via
    `attach_neighbors(gdf, neighbors_dict='vizinhanca.json')`.

    Parameters:
        gdf (GeoDataFrame): GeoDataFrame com a coluna '_neighs' já populada.
        path (str): Caminho do arquivo JSON de destino.

    Raises:
        ValueError: Se a coluna '_neighs' não estiver presente.

    Examples:
        >>> export_neighbors(gdf, "vizinhanca.json")
    """
    if "_neighs" not in gdf.columns:
        raise ValueError("Coluna '_neighs' não encontrada. Execute `attach_neighbors` primeiro.")
    neighbors_dict = gdf["_neighs"].to_dict()
    with open(path, "w") as f:
        json.dump(neighbors_dict, f, indent=2)


__all__ = [
    "WeightStrategy",
    "attach_neighbors",
    "get_neighbors",
    "get_neighbor_values",
    "export_neighbors",
]