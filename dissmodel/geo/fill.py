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
    if seed is not None:
        random.seed(seed)
    samples = generate_sample(data, size=len(gdf))
    gdf[attr] = samples


@register_strategy(FillStrategy.ZONAL_STATS)
def fill_zonal_stats(vectors, raster_data, affine, stats, prefix="attr_", nodata=-999):
    stats_output = zonal_stats(vectors, raster_data, affine=affine, nodata=nodata, stats=stats)
    for stat in stats:
        vectors[f"{prefix}{stat}"] = [f[stat] for f in stats_output]


@register_strategy(FillStrategy.MIN_DISTANCE)
def fill_min_distance(from_gdf, to_gdf, attr_name="min_distance"):
    from_gdf[attr_name] = from_gdf.geometry.apply(
        lambda geom: to_gdf.geometry.distance(geom).min()
    )


# === Interface principal ===
def fill(strategy: str, **kwargs):
    if strategy not in _fill_strategies:
        raise ValueError(f"Estratégia desconhecida: {strategy}")
    return _fill_strategies[strategy](**kwargs)


# === Exportáveis ===
__all__ = ["fill", "FillStrategy", "register_strategy"]
