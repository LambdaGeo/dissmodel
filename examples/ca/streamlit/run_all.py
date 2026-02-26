import streamlit as st
import inspect
import random
import matplotlib.pyplot as plt

from dissmodel.core import Environment
from dissmodel.visualization.map import Map
from dissmodel.visualization.widgets import display_inputs
from dissmodel.geo import regular_grid
from matplotlib.colors import ListedColormap



import dissmodel.models.ca as cellular_models  


# Configurações da página
st.set_page_config(page_title="Modelos Celulares", layout="centered")
st.title("Modelos de Autômatos Celulares (DisSModel)")

# Obter todas as classes do módulo de modelos celulares
model_classes = {
    name: cls for name, cls in inspect.getmembers(cellular_models, inspect.isclass)
}




# Sidebar - seleção do modelo
model_name = st.sidebar.selectbox("Escolha o modelo", list(model_classes.keys()))

# Parâmetros gerais
steps = st.sidebar.slider("Número de passos", min_value=1, max_value=1000, value=50)
grid_dim = st.sidebar.slider("Tamanho da grade", min_value=5, max_value=100, value=20)

# Colormaps disponíveis (qualitativos e contínuos)
colormap_names = [
    "tab10", "Set1", "Pastel1",
    "viridis", "plasma", "inferno",
    "Greens", "Reds", "Blues",
    "coolwarm", "bwr"
]

# Sidebar - seleção de colormap
selected_cmap_name = st.sidebar.selectbox("Escolha o colormap", colormap_names)

# Botão de execução
executar = st.button("Executar Simulação")

# Geração da grade base
gdf = regular_grid(dimension=(grid_dim, grid_dim), resolution=1, attrs={'state': 0})

# Ambiente de simulação
env = Environment(start_time=0, end_time=steps)

# Instanciando o modelo dinamicamente
ModelClass = model_classes[model_name]
model_instance = ModelClass(gdf=gdf, dim=grid_dim, start_time=0, end_time=steps)

# Exibir parâmetros ajustáveis do modelo
display_inputs(model_instance, st.sidebar)



# Colormap selecionado
cmap = plt.get_cmap(selected_cmap_name)

# Área de plotagem
plot_area = st.empty()

# Parâmetros do gráfico
plot_params = {
    "column": "state",
    "cmap": cmap,
    "ec": "black"
}

# Mapa inicial
Map(gdf=gdf, plot_area=plot_area, plot_params=plot_params)

# Executar simulação ao clicar no botão
if executar:
    model_instance.initialize()
    env.run()
