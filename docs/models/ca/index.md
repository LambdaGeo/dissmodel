# Cellular Automata

A **Cellular Automaton (CA)** is a discrete spatial model in which a grid of cells
evolves over time according to a local transition rule. At each step, every cell
reads the states of its neighbours and computes a new state — producing emergent
global behaviour from simple local interactions.

## How CAs work in DisSModel

DisSModel implements cellular automata on top of a **GeoDataFrame grid** (vector substrate)
using the `CellularAutomaton` base class. The key concepts are:

**Pull pattern** — each cell independently applies `rule(idx)` to determine its next state.
The rule receives the cell index and can read any column from the GeoDataFrame.

**Snapshot semantics** — at the start of each step, the current state is frozen.
All cells read from the frozen snapshot and write to the new state simultaneously,
preserving the synchronous update semantics of classical CA theory.

**Neighbourhood** — spatial adjacency is computed via `libpysal` weights
(`Queen` or `Rook`) and cached for performance. Call `create_neighborhood()`
before running the simulation.

```python
from dissmodel.core import Environment
from dissmodel.geo import regular_grid
from dissmodel.models.ca import GameOfLife
from dissmodel.visualization.map import Map

gdf = regular_grid(dimension=(30, 30), resolution=1)

env = Environment(end_time=20)
model = GameOfLife(gdf=gdf)
model.initialize()
Map(gdf=gdf, plot_params={"column": "state"})
env.run()
```

## Implementing your own CA

Subclass `CellularAutomaton` and implement the `rule(idx)` method:

```python
from dissmodel.core import Environment
from dissmodel.geo import regular_grid, fill, FillStrategy
from dissmodel.visualization.map import Map
from libpysal.weights import Queen

from dissmodel.geo.vector.cellular_automaton import CellularAutomaton

class MyCA(CellularAutomaton):

    def setup(self) -> None:
        """Build the Queen neighborhood for the grid."""
        self.create_neighborhood(strategy=Queen, use_index=True)

    def rule(self, idx):
        neighbours = self.neighbor_values(idx, "state")
        return 1 if neighbours.sum() > 3 else 0
    
    def initialize(self) -> None:
        fill(
            strategy=FillStrategy.RANDOM_SAMPLE,
            gdf=self.gdf,
            attr="state",
            data={1: 0.4, 0: 0.6},
            seed=42,
        )
    
```

Then wire it up:

```python
gdf = regular_grid(dimension=(40, 40), resolution=1, attrs={"state": 0})
env = Environment(end_time=10)
ca  = MyCA(gdf=gdf)
ca.initialize()
Map(gdf=gdf, plot_params={"column": "state"})

env.run()
```

## Available models

| Model | Description |
|-------|-------------|
| [Game of Life](game_of_life.md) | Conway's classic binary CA — birth, survival, and death rules |
| [Fire Model](fire_model.md) | Deterministic forest fire spread |
| [Fire Model Prob](fire_model_prob.md) | Probabilistic fire with spontaneous ignition and regrowth |
| [Snow](snow.md) | Snowfall accumulation |
| [Growth](growth.md) | Stochastic radial growth from a seed cell |
| [Propagation](propagation.md) | Active-state transmission with KNN neighbourhood |
| [Anneal](anneal.md) | Binary system relaxation via majority-vote rule |