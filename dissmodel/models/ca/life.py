

from dissmodel.core import Model


class GameOfLife(Model):

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
       

    def rule(self, idx):
        """
        Define a regra do Game of Life para atualizar o estado de uma célula.
        """
        # Estado atual da célula
        value = self.env.gdf.loc[idx].state
        
        # Estados dos vizinhos
        neighs = self.neighs(idx)
        count = neighs["state"].sum()
        
        # Aplicar as regras do Game of Life
        if value == 1:  # Célula viva
            if count < 2 or count > 3:  # Subpopulação ou superpopulação
                return 0  # Morre
            else:
                return 1  # Sobrevive
        else:  # Célula morta
            if count == 3:  # Reprodução
                return 1  # Revive
            else:
                return 0  # Continua morta


    def execute(self):
        # Aplicar a função `rule` a todos os índices e armazenar os novos estados
        self.env.gdf["state"] = self.env.gdf.index.map(self.rule)
        print (self.env.now())

