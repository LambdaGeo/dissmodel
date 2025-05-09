
from dissmodel.core import Model, Environment

from dissmodel.core.spatial import regular_grid, fill

from dissmodel.visualization.map import Map

from dissmodel.visualization.streamlit import StreamlitMap


from matplotlib.colors import ListedColormap

import streamlit as st

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





## a configuracao começaria aqui

# Configurações da aplicação
st.set_page_config(page_title="Modelo Game of Life", layout="centered")
st.title("Simulação com Game of Life (DisSModel)")

# Parâmetros do usuário
st.sidebar.title("Parametros do Modelo")

steps = st.sidebar.slider("Número de passos da simulação", min_value=1, max_value=50, value=10)
grid_dim = st.sidebar.slider("Tamanho da grade", min_value=5, max_value=50, value=20)

custom_cmap = ListedColormap(['green', 'red'])
plot_params={ "column": "state","cmap": custom_cmap,  "ec" : 'black'}


import numpy as np

# Inicializar estado da sessão
if st.button("Executar Simulação"):

    # Área de plotagem reservada
    plot_area = st.empty()

    ### espaço 
    gdf = regular_grid (bounds=(0, 0, 100, 100), dim=grid_dim, attrs={'state': 0})
    
    n = len(gdf)
    
    fill(
        strategy="random_sample",
        gdf=gdf,
        attr="state",
        data={0: 0.7, 1: 0.3},
        seed=42
    )

    env = Environment (
        gdf = gdf,
        end_time = steps,
        start_time=0
    )


    GameOfLife(create_neighbohood="Queen")

    StreamlitMap(  
        plot_area = plot_area,
        plot_params={ "column": "state","cmap": custom_cmap,  "ec" : 'black'}
    )

    env.run()