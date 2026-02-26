from enum import Enum
import random
from rasterstats import zonal_stats

# === Estratégias disponíveis ===
class FillStrategy(str, Enum):
    ZONAL_STATS = "zonal_stats"
    MIN_DISTANCE = "min_distance"
    RANDOM_SAMPLE = "random_sample"
    PATTERN = "pattern"


# === Registry de estratégias ===
_fill_strategies = {}

def register_strategy(name):
    def decorator(func):
        _fill_strategies[name] = func
        return func
    return decorator


# === Função auxiliar ===
def generate_sample(data, size=1):
    if isinstance(data, dict):
        if 'min' in data and 'max' in data:
            return [random.randint(data['min'], data['max']) for _ in range(size)]
        options = list(data.keys())
        probabilities = list(data.values())
        return random.choices(options, weights=probabilities, k=size)

    elif isinstance(data, list):
        return random.choices(data, k=size)

    else:
        raise ValueError("O argumento `data` deve ser uma lista ou um dicionário.")


# === Estratégias de preenchimento ===
@register_strategy(FillStrategy.PATTERN)
def fill_regular_grid(gdf, attr, pattern, start_x=0, start_y=0):
    """
    Preenche atributos em um GeoDataFrame com base em um padrão regular (grid).

    Parameters:
        gdf (GeoDataFrame): GeoDataFrame cujas células serão preenchidas.
        attr (str): Nome do atributo a ser preenchido.
        pattern (list[list]): Padrão (grid) a ser aplicado.
        start_x (int): Offset inicial na direção x.
        start_y (int): Offset inicial na direção y.
    """
    w = len(pattern)
    h = len(pattern[0])
    for i in range(w):
        for j in range(h):
            idx = f"{start_x + i}-{start_y + j}"
            gdf.loc[idx, attr] = pattern[w - i - 1][j]


@register_strategy(FillStrategy.RANDOM_SAMPLE)
def fill_random_sample(gdf, attr, data, seed=None):
    """
    Preenche um atributo do GeoDataFrame com amostras aleatórias.

    Parameters:
        gdf (GeoDataFrame): GeoDataFrame cujas células serão preenchidas.
        attr (str): Nome do atributo a ser preenchido.
        data (list | dict): Fonte de dados para amostragem. Pode ser:
            - list: valores serão sorteados uniformemente.
            - dict com 'min'/'max': inteiros aleatórios no intervalo [min, max].
            - dict chave/peso: amostragem ponderada entre as chaves.
        seed (int | None): Semente para reprodutibilidade. Default None.
    """
    if seed is not None:
        random.seed(seed)
    samples = generate_sample(data, size=len(gdf))
    gdf[attr] = samples


@register_strategy(FillStrategy.ZONAL_STATS)
def fill_zonal_stats(vectors, raster_data, affine, stats, prefix="attr_", nodata=-999):
    """
    Preenche atributos em um GeoDataFrame com estatísticas zonais extraídas de um raster.

    Parameters:
        vectors (GeoDataFrame): Geometrias sobre as quais as estatísticas serão calculadas.
        raster_data (np.ndarray): Array do raster de entrada.
        affine (Affine): Transformação afim do raster (origem e resolução).
        stats (list[str]): Estatísticas a calcular, ex: ['mean', 'min', 'max', 'sum'].
        prefix (str): Prefixo para nomear as colunas resultantes. Default 'attr_'.
        nodata (int | float): Valor a ignorar como ausente no raster. Default -999.
    """
    stats_output = zonal_stats(vectors, raster_data, affine=affine, nodata=nodata, stats=stats)
    for stat in stats:
        vectors[f"{prefix}{stat}"] = [f[stat] for f in stats_output]


@register_strategy(FillStrategy.MIN_DISTANCE)
def fill_min_distance(from_gdf, to_gdf, attr_name="min_distance"):
    """
    Preenche um atributo com a distância mínima de cada geometria até o conjunto alvo.

    A distância é calculada no sistema de coordenadas das geometrias, portanto
    use um CRS projetado (ex: UTM) para obter resultados em metros.

    Parameters:
        from_gdf (GeoDataFrame): GeoDataFrame de origem cujas células serão preenchidas.
        to_gdf (GeoDataFrame): GeoDataFrame alvo para cálculo da distância mínima.
        attr_name (str): Nome da coluna a ser criada/atualizada. Default 'min_distance'.
    """
    from_gdf[attr_name] = from_gdf.geometry.apply(
        lambda geom: to_gdf.geometry.distance(geom).min()
    )


# === Interface principal ===
def fill(strategy: str, **kwargs):
    """
    Ponto de entrada unificado para todas as estratégias de preenchimento.

    Delega a execução à estratégia registrada sob o nome fornecido, repassando
    todos os argumentos nomeados diretamente à função correspondente.

    Parameters:
        strategy (str | FillStrategy): Identificador da estratégia a ser usada.
            Valores válidos: 'pattern', 'random_sample', 'zonal_stats', 'min_distance'.
        **kwargs: Argumentos específicos da estratégia escolhida.

    Returns:
        Resultado da estratégia executada (pode ser None para operações in-place).

    Raises:
        ValueError: Se a estratégia fornecida não estiver registrada.

    Examples:
        >>> fill(FillStrategy.RANDOM_SAMPLE, gdf=grid, attr="land_use", data=[1, 2, 3], seed=42)
        >>> fill("min_distance", from_gdf=grid, to_gdf=roads, attr_name="dist_road")
        >>> fill(FillStrategy.PATTERN, gdf=grid, attr="zone", pattern=[[1,2],[3,4]])
    """
    if strategy not in _fill_strategies:
        raise ValueError(f"Estratégia desconhecida: {strategy}")
    return _fill_strategies[strategy](**kwargs)


# === Exportáveis ===
__all__ = ["fill", "FillStrategy", "register_strategy"]