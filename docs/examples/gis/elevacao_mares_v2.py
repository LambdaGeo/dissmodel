
from dissmodel.core import Model, Environment

from dissmodel.core.spatial import regular_grid, fill, dw_query

from dissmodel.visualization import Map, track_plot, Chart

from dissmodel.visualization.streamlit import StreamlitMap, display_inputs

import pandas as pd

from matplotlib.colors import ListedColormap


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
        

        for v_idx in viz_idxs:
            if self.env.gdf.loc[v_idx, "Alt2"] < cell["Alt2"]:
                affected.append(v_idx)

        n = len(affected)
        flow = self.seaLevelRiseRate / n
        
        # retorna dicionário de atualizações
        return {i: flow for i in affected}

    def execute(self):
        # Inicializa uma série com zeros para acumular alterações
        delta = pd.Series(0, index=self.env.gdf.index, dtype=float)

        # Itera sobre os índices de interesse
        target_idxs = self.env.gdf[self.env.gdf["Usos"] == 3].index
        for idx in target_idxs:
            updates = self.update_sea_level(idx)
            for i, flow in updates.items():
                delta[i] += flow # pode receber agua de mais de uma celula

        #print (delta)
        # Aplica todas as atualizações de uma vez
        self.env.gdf["Alt2"] += delta

        self.media_geral = gdf["Alt2"].mean()
        SEA_OR_FLOODED = [3, 6, 7, 9, 10]  # Correspondentes às constantes MAR, SOLO_DESCOBERTO_INUNDADO etc.
        filtro_mar_ou_inundado = gdf["Usos"].isin(SEA_OR_FLOODED)
        self.media_mar = gdf.loc[filtro_mar_ou_inundado, "Alt2"].mean()




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

Chart(select={"media_mar"})
Chart(select={"media_geral"})

############################
### Execução da simulação

# Inicia a simulação quando o botão for clicado
env.run()
