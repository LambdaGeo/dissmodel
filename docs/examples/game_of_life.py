
from dissmodel.core import Model, Environment

from dissmodel.visualization.map import Map

from dissmodel.core.spatial import regular_grid, fill

from matplotlib.colors import ListedColormap

### Modelo

class GameOfLife(Model):
       

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





### espaço 
gdf = regular_grid (bounds=(0, 0, 100, 100), dim=20, attrs={'state': 0})
#grid = regular_grid (bounds=(0, 0, 100, 100), dim=10, attrs={'land_use': 0})
glider_pattern = [
            [0, 1, 0],
            [0, 0, 1],
            [1, 1, 1]
]

fill(
        strategy="pattern",
        gdf=gdf,
        attr="state",
        pattern=glider_pattern,
        start_x=5,
        start_y=5
)


### instanciação de um modelo
### ambiente que integra o espaço e os modelos
env = Environment (
    gdf = gdf,
    end_time = 10,
    start_time=0
)

## instanciacao do modelo
gol = GameOfLife(create_neighbohood="Queen")

## visualização
custom_cmap = ListedColormap(['green', 'red'])
plot_params={ "column": "state","cmap": custom_cmap,  "ec" : 'black'}
Map( 
    plot_params={ "column": "state","cmap": custom_cmap,  "ec" : 'black'}
)

## execução
env.run()