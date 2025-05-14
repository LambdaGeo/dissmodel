
from dissmodel.core import Model, Environment

from dissmodel.core.spatial import regular_grid, fill, dw_query

from dissmodel.visualization import Map

from dissmodel.visualization.streamlit import StreamlitMap, display_inputs


from matplotlib.colors import ListedColormap


import geopandas as gpd

file_name = ""
gdf = gpd.read_file(filename=file_name)

# Criação do ambiente de simulação, que integra espaço, tempo e agentes
env = Environment(
    gdf=gdf,
    end_time=10,
    start_time=0
)


############################
### Visualização da simulação



# Mapeamento de cores personalizado para os estados das células
plot_params={ "column":"Alt2","cmap": "Blues"}

# Componente de visualização do mapa
Map(
    plot_params=plot_params
)

############################
### Execução da simulação

# Inicia a simulação quando o botão for clicado
env.run()
