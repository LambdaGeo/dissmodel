
from dissmodel.core import Model, Environment

from dissmodel.core.spatial import regular_grid, fill, dw_query

from dissmodel.visualization import Map

from dissmodel.visualization.streamlit import StreamlitMap, display_inputs


from matplotlib.colors import ListedColormap


import geopandas as gpd

class Elevacao(Model):

    seaLevelRiseRate: float

    def setup (self, seaLevelRiseRate=0.011):
        self.seaLevelRiseRate = seaLevelRiseRate

    def rule(self, idx):
        """
        Define a regra do Game of Life para atualizar o estado de uma célula.
        """
        # Estado atual da célula
        value = self.env.gdf.loc[idx].Alt2 + self.seaLevelRiseRate
        return value
        '''
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
        '''

    def execute(self):
        # Aplicar a função `rule` a todos os índices e armazenar os novos estados
        #self.env.gdf["state"] = self.env.gdf.index.map(self.rule)
        #gdf_sea = gdf.loc[gdf["Usos"] == 3]
        gdf.loc[gdf["Usos"] == 3, "Alt2"] = gdf.loc[gdf["Usos"] == 3].index.map(self.rule)
        #print (self.env.now())

    def execute__(self):
        print ("time", self.env.now())
        gdf = self.env.gdf
        gdf.loc[gdf["Usos"] == 3, "Alt2"] += self.seaLevelRiseRate


file_name = "../brmangue/data/teste_uso/Recorte_Teste.shp"
gdf = gpd.read_file(filename=file_name)

# Criação do ambiente de simulação, que integra espaço, tempo e agentes
env = Environment(
    gdf=gdf,
    end_time=10,
    start_time=0
)




############################
### Visualização da simulação

model = Elevacao(create_neighbohood="Rook", seaLevelRiseRate=1)

# Mapeamento de cores personalizado para os estados das células
#plot_params={ "column":"Alt2","cmap": "Blues"}
plot_params={"column":'Alt2', "scheme":'quantiles', "k":3, "legend":True, "cmap":'viridis'}

# Componente de visualização do mapa
Map(plot_params=plot_params)


############################
### Execução da simulação

# Inicia a simulação quando o botão for clicado
env.run()
