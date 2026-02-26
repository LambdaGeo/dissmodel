
from dissmodel.core import Model, Environment



from dissmodel.visualization import Map






import geopandas as gpd

file_name = "examples/data/ilha_do_maranhao.zip"
gdf = gpd.read_file(filename=file_name)

# Criação do ambiente de simulação, que integra espaço, tempo e agentes
env = Environment(  
    end_time=10,
    start_time=0
)


############################
### Visualização da simulação


# Componente de visualização do mapa
Map(
    gdf=gdf,
    plot_params={}
)

############################
### Execução da simulação

# Inicia a simulação quando o botão for clicado
env.run()
