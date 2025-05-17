
from dissmodel.core import Model, Environment

from dissmodel.core.spatial import regular_grid, fill, dw_query

from dissmodel.visualization import Map, track_plot, Chart

from dissmodel.visualization.streamlit import StreamlitMap, display_inputs

import pandas as pd

from matplotlib.colors import ListedColormap
from matplotlib.colors import ListedColormap, BoundaryNorm

SEA_OR_FLOODED = [3, 6, 7, 9, 10]  # Correspondentes às constantes MAR, SOLO_DESCOBERTO_INUNDADO etc.

# Códigos de uso da terra
uso_classes = {
    1: "Mangue",
    2: "Vegetação Terrestre",
    3: "Mar",
    4: "Área Antropizada",
    5: "Solo Descoberto",
    6: "Solo Descoberto Inundado",
    7: "Área Antropizada Inundada",
    8: "Mangue Migrado",
    9: "Mangue Inundado",
    10: "Vegetação Terrestre Inundada"
}

# Cores RGB normalizadas (0-1)
colors = [
    (0/255, 100/255, 0/255),       # Mangue
    (128/255, 128/255, 0/255),     # Vegetação Terrestre
    (0/255, 0/255, 139/255),       # Mar
    (255/255, 215/255, 0/255),     # Área Antropizada
    (255/255, 222/255, 173/255),   # Solo Descoberto
    (0/255, 0/255, 0/255),         # Solo Descoberto Inundado
    (0/255, 0/255, 0/255),         # Área Antropizada Inundada
    (0/255, 255/255, 0/255),       # Mangue Migrado
    (255/255, 0/255, 0/255),       # Mangue Inundado
    (0/255, 0/255, 0/255)          # Vegetação Terrestre Inundada
]

# Mapeia cada código a uma cor
cmap = ListedColormap(colors)
norm = BoundaryNorm(boundaries=range(1, 12), ncolors=len(colors))


import geopandas as gpd

@track_plot("media_geral", "red")
@track_plot("media_mar", "blue")
class Elevacao(Model):

    seaLevelRiseRate: float
    media_geral : float
    media_mar : float

    def setup (self, seaLevelRiseRate=0.011):
        self.seaLevelRiseRate = seaLevelRiseRate          # estrutura de vizinhança (ex: libpysal.weights)
        self.media_geral = 0
        self.media_mar = 0

    def neighs(self, idx):
        """
        Retorna os índices dos vizinhos da célula fornecida.
        """
        if self.create_neighbohood and self.w_ is not None:
            return self.w_.neighbors[idx]  # lista de índices
        else:
            return []

    def update_sea_level (self, idx):

        cell = self.env.gdf.loc[idx]
        viz_idxs = self.neighs(idx)
        
        affected = [idx]  # começa com a célula atual
        
        self.celulas_modificadas += 1
        count = 1
        for v_idx in viz_idxs:
            if self.env.gdf.loc[v_idx, "Alt2"] < cell["Alt2"]:
                affected.append(v_idx)

        for i in affected:
            if self.env.gdf.loc[i, "Usos"] not in [3, 6, 7, 9, 10]:  # evitar sobrescrever mar/inundados
                self.env.gdf.at[i, "Usos"] = 7  # AREA_ANTROPIZADA_INUNDADO

                
        n = len(affected)
        flow = self.seaLevelRiseRate / n
        
        # retorna dicionário de atualizações
        return {i: flow for i in affected}
        

    def execute(self):
        # Inicializa uma série com zeros para acumular alterações
        delta = pd.Series(0, index=self.env.gdf.index, dtype=float)

        self.celulas_modificadas = 0
        self.soma_elevacao = 0
        # Itera sobre os índices de interesse
        target_idxs = self.env.gdf[self.env.gdf["Usos"].isin(SEA_OR_FLOODED)].index
        for idx in target_idxs:
            updates = self.update_sea_level(idx)
            for i, flow in updates.items():
                delta[i] += flow # pode receber agua de mais de uma celula
                self.soma_elevacao +=  flow

        #print (delta)
        # Aplica todas as atualizações de uma vez
        self.env.gdf["Alt2"] += delta

        self.media_geral = gdf["Alt2"].mean()
        filtro_mar_ou_inundado = gdf["Usos"].isin(SEA_OR_FLOODED)
        self.media_mar = gdf.loc[filtro_mar_ou_inundado, "Alt2"].mean()

        print (self.celulas_modificadas, self.soma_elevacao, self.soma_elevacao/self.celulas_modificadas)


file_name = "../brmangue/data/teste_uso/Recorte_Teste.shp"
#file_name = "../brmangue/data/anil/elevacao_pol.shp"
#file_name = "../brmangue/data/teste1/Recorte_Teste.shp"

gdf = gpd.read_file(filename=file_name)
gdf.set_index("object_id0", inplace=True)

print (gdf.head())
# Criação do ambiente de simulação, que integra espaço, tempo e agentes
env = Environment(
    gdf=gdf,
    end_time=20,
    start_time=1
)






############################
### Visualização da simulação

#model = Elevacao(create_neighbohood="Queen", seaLevelRiseRate=0.5)
model = Elevacao( seaLevelRiseRate=0.5)

import libpysal
import json

from libpysal.weights import W

with open("/home/scosta/dev/brmangue/neighbors.json") as f:
    neighbors = json.load(f)

model.w_ = W(neighbors)
model.create_neighbohood = True

# Mapeamento de cores personalizado para os estados das células
#plot_params={ "column":"Alt2","cmap": "Blues"}
plot_params={"column":'Alt2', "scheme":'quantiles', "k":5, "legend":True, "cmap":'RdYlGn'}

# Componente de visualização do mapa
Map(plot_params=plot_params)

plot_params_uso = {
    "column": "Usos",
    "cmap": ListedColormap(colors),
    "norm": BoundaryNorm(boundaries=range(1, 12), ncolors=len(colors)),
    "legend": False,  # a legenda personalizada será criada manualmente
    "edgecolor": "black",
    "linewidth": 0.2
}

Map(plot_params=plot_params_uso)

Chart(select={"media_mar"})
Chart(select={"media_geral"})

############################
### Execução da simulação

# Inicia a simulação quando o botão for clicado
env.run()
