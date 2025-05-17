
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
        cell = self.env.gdf.loc[idx]

        neighs = self.neighs(idx).query("Alt2 < @cell.Alt2")
        n, _ = neighs.shape 
        n = n + 1

        flow = self.seaLevelRiseRate / n
        value = cell.Alt2 + flow

        #neighs["Alt2"] += self.seaLevelRiseRate + flow

        return value
      

    def execute(self):
        # Aplicar a função `rule` a todos os índices e armazenar os novos estados
        #self.env.gdf["state"] = self.env.gdf.index.map(self.rule)
        #gdf_sea = gdf.loc[gdf["Usos"] == 3]
        gdf.loc[gdf["Usos"] == 3, "Alt2"] = gdf.loc[gdf["Usos"] == 3].index.map(self.rule)
        #print (self.env.now())



#file_name = "../brmangue/data/teste_uso/Recorte_Teste.shp"
file_name = "/home/scosta/dev/recorte_teste_simplificado.shp"
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
