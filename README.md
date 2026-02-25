# 👋 DissModel (Discrete Spatial Modelling)

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)

📚 **Documentação online:** https://lambdageo.github.io/dissmodel/

## 🎯 Visão Geral

O **DissModel** é uma biblioteca Python voltada para modelagem espacial baseada em zonas, com suporte à integração de dados geográficos e estatísticas espaciais. Seu objetivo é facilitar o desenvolvimento de modelos espaciais dinâmicos, especialmente úteis em aplicações como planejamento territorial, análise ambiental, simulações espaciais e estudos socioeconômicos.

> ⚠️ Aviso: Esta biblioteca ainda está em fase de testes e não está publicada no repositório oficial do PyPI. Interessados em testar podem instalá-la via TestPyPI (veja abaixo).
> 

## 🚀 Funcionalidades Principais

- **Algoritmos de Integração Espacial**: integração entre dados vetoriais e matriciais por meio de estatísticas zonais, distância mínima, e interseções geométricas.
- **Suporte a Dados Geográficos**: leitura e manipulação de shapefiles, GeoJSON, raster e integração com bibliotecas como `geopandas`, `shapely`, `rasterio` e `pyproj`.
- **Estrutura Modular para Modelagem**: componentes reutilizáveis para construir modelos espaciais dinâmicos, flexíveis e extensíveis.
- **Ferramentas de Visualização**: mapas, histogramas, gráficos e exportações para softwares de SIG como QGIS.
- **Autômatos Celulares Espaciais**: suporte à definição de regras baseadas em vizinhança e evolução temporal.

## 💻 Instalação

Instalação via **TestPyPI**:

```sql
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ dissmodel
```

Ou diretamente a partir do código-fonte:

```sql
git clone https://github.com/LambdaGeo/dissmodel.git
cd dissmodel
pip install -e .
```

## 🧩 Exemplo com Autômato Celular Espacial: Game of Life

A seguir, um exemplo de implementação do clássico **Game of Life**, utilizando o suporte da biblioteca `dissmodel` a autômatos celulares espaciais.

```sql
from dissmodel.geo.celullar_automaton import CellularAutomaton
from dissmodel.geo import fill, FillStrategy
from libpysal.weights import Queen

class GameOfLife(CellularAutomaton):
    def initialize(self):
        fill(
            strategy=FillStrategy.RANDOM_SAMPLE,
            gdf=self.gdf,
            attr="state",
            data={1: 0.6, 0: 0.4},
            seed=42
        )

    def setup(self):
        self.create_neighborhood(strategy=Queen, use_index=True)

    def rule(self, idx):
        value = self.gdf.loc[idx, self.state_attr]
        neighs = self.neighs(idx)
        count = neighs[self.state_attr].fillna(0).sum()

        if value == 1:
            return 1 if 2 <= count <= 3 else 0
        else:
            return 1 if count == 3 else 0

```

Execução e Visualização

```sql
from dissmodel.geo import regular_grid
from dissmodel.core import Environment
from dissmodel.visualization.map import Map
from dissmodel.models.ca import GameOfLife
from matplotlib.colors import ListedColormap

# Geração de uma grade espacial
gdf = regular_grid(dimension=(20, 20), resolution=1, attrs={'state': 0})

# Instanciação do modelo e do ambiente
gol = GameOfLife(gdf=gdf)
env = Environment(start_time=0, end_time=10)

# Inicialização e visualização do estado inicial
gol.initialize()
Map(gdf=gdf, plot_params={"column": "state", "cmap": ListedColormap(['green', 'red']), "ec": 'black'})

# Execução do modelo
env.run()

```

🔁 O modelo aplica as regras do Game of Life em uma vizinhança do tipo *Queen*, evoluindo o estado espacial ao longo do tempo.

## 📘 Documentação

Documentação completa disponível em:

👉 https://lambdageo.github.io/dissmodel/

## 🤝 Contribuições

Contribuições são bem-vindas! Você pode:

1. Fazer um fork do repositório
2. Criar uma branch com sua contribuição (`feature/minha_funcionalidade`)
3. Enviar um pull request com uma breve descrição

## 📄 Licença

Este projeto está licenciado sob a Licença MIT.

Consulte o arquivo LICENSE para mais detalhes.
