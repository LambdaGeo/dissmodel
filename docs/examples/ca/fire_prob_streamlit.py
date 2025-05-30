
from dissmodel.core import Model, Environment

from dissmodel.core.spatial import regular_grid, fill

from dissmodel.visualization import Map

from dissmodel.visualization.streamlit import StreamlitMap, display_inputs


from matplotlib.colors import ListedColormap

import streamlit as st

import random

from dissmodel.models.ca import FireModelProb


############################
### Interface do usuário com Streamlit

# Configuração inicial da página
st.set_page_config(page_title="Fire Model", layout="centered")
st.title("Fire Model (DisSModel)")

# Painel lateral com parâmetros ajustáveis pelo usuário
st.sidebar.title("Parâmetros do Modelo")
steps = st.sidebar.slider("Número de passos da simulação", min_value=1, max_value=50, value=10)
grid_dim = st.sidebar.slider("Tamanho da grade", min_value=5, max_value=100, value=20)

# Botão principal para iniciar a simulação
executar = st.button("Executar Simulação")

############################
### Criação do espaço simulado

# Geração de uma grade regular como espaço simulado, sem dados espaciais externos
gdf = regular_grid(bounds=(0, 0, 100, 100), dim=grid_dim, attrs={'state': 0})

# Criação do ambiente de simulação, que integra espaço, tempo e agentes
env = Environment(
    gdf=gdf,
    end_time=steps,
    start_time=0
)

############################
### Instanciação do modelo e exibição de parâmetros

# Criação do modelo de fogo com definição da vizinhança (Rook)
fire = FireModelProb(create_neighbohood="Rook")

# Exibição dos parâmetros do modelo na barra lateral
display_inputs(fire, st.sidebar)

############################
### Visualização da simulação

# Área da interface reservada para o mapa interativo
plot_area = st.empty()

# Mapeamento de cores personalizado para os estados das células
custom_cmap = ListedColormap(['green', 'red', 'brown'])
plot_params = {"column": "state", "cmap": custom_cmap, "ec": "black"}

# Componente de visualização do mapa
StreamlitMap(
    plot_area=plot_area,
    plot_params=plot_params
)

############################
### Execução da simulação

# Inicia a simulação quando o botão for clicado
if executar:
    env.run()
