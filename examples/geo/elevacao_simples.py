import pandas as pd
import geopandas as gpd
from dissmodel.core import Model, Environment
from dissmodel.visualization import Map, Chart, track_plot

from matplotlib.colors import ListedColormap, BoundaryNorm


# Modelo Elevacao Simplificado
@track_plot("media_altitude", "blue")
class ElevacaoSimples(Model):

    seaLevelRiseRate: float
    media_altitude: float

    def setup(self, gdf, seaLevelRiseRate=10):
        self.gdf = gdf
        self.seaLevelRiseRate = seaLevelRiseRate
        self.media_altitude = 0

    def execute(self):
        print("execute:", self.env.now())
        filtro = self.gdf["Usos"] == 3
        self.gdf.loc[filtro, "Alt2"] += self.seaLevelRiseRate
        gdf_mar = self.gdf[filtro]
        self.media_altitude = gdf_mar["Alt2"].mean()


# Carrega os dados espaciais
file_name = "examples/data/Recorte_Teste.zip"
gdf = gpd.read_file(file_name)
gdf.set_index("object_id0", inplace=True)

import mapclassify
# 1. Criar classificador uma vez com os dados iniciais
classifier = mapclassify.NaturalBreaks(gdf['Alt2'], k=5)

# Cria o ambiente
env = Environment(start_time=1, end_time=10)

# Instancia o modelo
modelo = ElevacaoSimples(gdf=gdf, seaLevelRiseRate=0.01)



#gdf['classe'] = classifier.classify(gdf['Alt2'])  # usa os mesmos bins
gdf['classe'] = classifier.yb

# Visualização do mapa da elevação
Map(gdf=gdf, plot_params={"column": "classe", "legend": True, "cmap": "Blues"})


# Gráfico da média de altitude
Chart(select={"media_altitude"})

# Executa a simulação
env.run()
