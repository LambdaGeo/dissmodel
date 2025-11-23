
import math
from libpysal.weights import Queen
from dissmodel.core import Model
from dissmodel.geo import attach_neighbors


class CellularAutomaton(Model):
    """
    Classe base para autômatos celulares espaciais baseada em um GeoDataFrame.

    Parâmetros:
    - gdf: GeoDataFrame com geometrias e atributo de estado.
    - state_attr: nome da coluna que representa o estado da célula.
    - step, start_time, end_time, name: parâmetros herdados da classe Model.
    """

    def __init__(self, gdf, state_attr="state", step=1, start_time=0, end_time=math.inf, name="", dim=None, *args, **kwargs):
        self.gdf = gdf
        self.state_attr = state_attr
        self._neighborhood_created = False
        self._neighs_cache = {}  # Cache for neighborhood lookups
        self.dim = dim
        super().__init__(step=step, start_time=start_time, end_time=end_time, name=name, *args, **kwargs)

    def initialize(self):
        """
        Deve ser sobrescrito pelas subclasses.
        """
        pass

    def create_neighborhood(self, strategy=Queen, neighbors_dict=None, *args, **kwargs):
        """
        Cria e anexa a vizinhança no GeoDataFrame.

        Parâmetros:
        - neighborhood_strategy: estratégia de vizinhança (ex: Queen, Rook)
        - neighbors_dict: dicionário ou caminho JSON para vizinhança externa
        - *args, **kwargs: parâmetros extras para a estratégia
        """
        self.gdf = attach_neighbors(
            gdf=self.gdf,
            strategy=strategy,
            neighbors_dict=neighbors_dict,
            *args,
            **kwargs
        )
        self._neighborhood_created = True
        # Create a cache for faster lookup
        self._neighs_cache = self.gdf["_neighs"].to_dict()

    def neighs_id(self, idx):
        """
        Retorna a lista de índices vizinhos da célula `idx`.
        """
        if self._neighs_cache:
            return self._neighs_cache.get(idx, [])
        return self.gdf.loc[idx, "_neighs"]

    def neighs(self, idx):
        """
        Retorna as células vizinhas da célula `idx` como um GeoDataFrame/DataFrame.

        Lança erro se a vizinhança ainda não foi criada.
        """
        if not self._neighborhood_created:
            raise RuntimeError("Vizinhança ainda não foi criada. Use `.create_neighborhood()` primeiro.")
        if "_neighs" not in self.gdf.columns:
            raise ValueError("A coluna '_neighs' não está presente no GeoDataFrame.")

        ids = self.neighs_id(idx)
        return self.gdf.loc[ids]

    def neighbor_values(self, idx, col):
        """
        Retorna os valores de uma coluna para os vizinhos da célula `idx` como um array numpy.
        Mais rápido que `neighs(idx)[col]`.
        """
        ids = self.neighs_id(idx)
        return self.gdf.loc[ids, col].values

    def rule(self, idx):
        """
        Deve ser sobrescrito pelas subclasses. Define a regra de transição de estado.
        """
        raise NotImplementedError("A subclasse deve implementar a regra.")

    def execute(self):
        """
        Executa um passo do autômato aplicando a regra a cada célula.
        """
        if not self._neighborhood_created:
            raise RuntimeError("Você deve criar a vizinhança antes de executar o modelo. Use `.create_neighborhood()`.")

        # Optimization:
        # The main bottleneck is iterating over the GeoDataFrame index and accessing rows individually via .loc within the loop.
        # We can optimize this by using a temporary dictionary or other structure to speed up neighbor lookups if possible,
        # or just accepting that the user-defined rule needs to be efficient.
        # However, the default `self.neighs(idx)` calls `self.gdf.loc[idx, "_neighs"]` and then `self.gdf.loc[ids]`.
        # These pandas lookups are very slow inside a loop.

        # Ideally, we would vectorize the rule, but since `rule` is an arbitrary python function, we can't easily vectorize it
        # without changing the API (e.g. asking the user to write a rule that takes the whole dataframe).

        # Strategy:
        # Since we cannot easily change the user API (rule(idx)), we optimize the internals of `neighs` or pre-fetch data.
        # But `neighs` is called inside `rule`, which is user code.

        # We can encourage the user to use `apply` but `map` is similar.
        
        self.gdf[self.state_attr] = self.gdf.index.map(self.rule)
