
from dissmodel.core import Model, Environment

from dissmodel.core.spatial import regular_grid, fill, dw_query

from dissmodel.visualization import Map

from dissmodel.visualization.streamlit import StreamlitMap, display_inputs


from matplotlib.colors import ListedColormap


import geopandas as gpd

class Elevacao(Model):

    seaLevelRiseRate: float

    def __init__ (self, seaLevelRiseRate=0.011):
        super().__init__()
        self.seaLevelRiseRate = seaLevelRiseRate

    def execute(self):
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

model = Elevacao(1)

# Mapeamento de cores personalizado para os estados das células
#plot_params={ "column":"Alt2","cmap": "Blues"}
plot_params={"column":'Alt2', "scheme":'quantiles', "k":5, "legend":True, "cmap":'viridis'}

# Componente de visualização do mapa
Map(    plot_params=plot_params)


############################
### Execução da simulação

# Inicia a simulação quando o botão for clicado
env.run(20)
