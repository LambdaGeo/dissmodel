from dissmodel.geo import regular_grid,fill, FillStrategy
import matplotlib.pyplot as plt

grid = regular_grid(dimension=(5, 5), resolution=1.0)

# Valores amostrados com base em probabilidades
sample_data = {
    "baixo": 0.2,
    "médio": 0.5,
    "alto": 0.3
}

fill(strategy=FillStrategy.RANDOM_SAMPLE, gdf=grid, attr="risco", data=sample_data, seed=42)

print(grid[["risco"]].head())
grid.plot(column="risco", legend=True)
plt.show()
