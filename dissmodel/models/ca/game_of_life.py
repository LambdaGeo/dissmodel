# Modelo Game of Life
# Exemplo de execução do Game of Life com autômato celular espacial


import random

from libpysal.weights import Queen
from dissmodel.geo import regular_grid, fill, FillStrategy

from dissmodel.geo import attach_neighbors
from dissmodel.geo.celullar_automaton import CellularAutomaton



class GameOfLife(CellularAutomaton):
    """
    Implementação do Game of Life como um autômato celular espacial.

    A célula sobrevive, nasce ou morre conforme o número de vizinhos vivos.
    """


    def initialize (self):

        fill(
            strategy=FillStrategy.RANDOM_SAMPLE,
            gdf=self.gdf,
            attr="state",
            data={1: 0.6, 0: 0.4},  # 70% de células com 1, 30% com 0
            seed=42
        )
        
    def initialize_ (self):
        # Padrões clássicos do Game of Life
        patterns = {
            "glider": [
                [0, 1, 0],
                [0, 0, 1],
                [1, 1, 1]
            ],
            "toad": [
                [0, 1, 1, 1],
                [1, 1, 1, 0]
            ],
            "blinker": [
                [1, 1, 1]
            ]
        }
        # assume uma grade com altura e largura iguais
        grid_dim = int(len(self.gdf) ** 0.5)


        # Inserção aleatória dos padrões
        for name, pattern in patterns.items():
            start_x = random.randint(0, grid_dim - len(pattern))
            start_y = random.randint(0, grid_dim - len(pattern[0]))
            
            fill(
                strategy=FillStrategy.PATTERN,
                gdf=self.gdf,
                attr="state",
                pattern=pattern,
                start_x=start_x,
                start_y=start_y
            )

    def setup(self):
        """
        Inicializa a vizinhança usando a estratégia Queen.
        """
        self.create_neighborhood(strategy=Queen, use_index=True)

    def rule(self, idx):
        """
        Aplica a regra do Game of Life para uma célula do índice `idx`.

        Regras:
        - Qualquer célula viva com menos de dois ou mais de três vizinhos vivos morre.
        - Qualquer célula viva com dois ou três vizinhos sobrevive.
        - Qualquer célula morta com exatamente três vizinhos vivos se torna viva.

        Retorna:
        - 0 para célula morta
        - 1 para célula viva
        """
        value = self.gdf.loc[idx, self.state_attr]
        neighs = self.neighs(idx)
        count = neighs[self.state_attr].fillna(0).sum()

        if value == 1:
            return 1 if 2 <= count <= 3 else 0
        else:
            return 1 if count == 3 else 0
