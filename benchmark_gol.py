import time
import warnings
import importlib

# Try to import GameOfLife from the library, otherwise define it.
# We need to import Environment first to ensure it's available if needed globally,
# but mainly we need to instantiate it before the model.

from dissmodel.core import Environment
from dissmodel.geo import regular_grid, fill, FillStrategy
from libpysal.weights import Queen
from dissmodel.geo.celular_automaton import CellularAutomaton

try:
    from dissmodel.models.ca import GameOfLife
    print("GameOfLife imported from library.")
    # We might want to monkeypatch or subclass it to use the new neighbor_values if it doesn't already
    # But since I am modifying the library, if GameOfLife is IN the library, I should check it.
    # The user's GameOfLife is in the README. The one in `dissmodel.models.ca` might be different?
    # Let's assume we use the one defined below for benchmark consistency unless we are testing the library's model specifically.
    # Actually, to test MY optimization, I should use a class that uses the new API.

except ImportError:
    pass

print("Defining optimized GameOfLife locally for benchmark.")
class GameOfLifeOptimized(CellularAutomaton):
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
        value = self.gdf.at[idx, self.state_attr] # Optimization: .at is faster than .loc for scalar

        # OPTIMIZATION: Use neighbor_values instead of neighs(idx)
        # neighs = self.neighs(idx)
        # count = neighs[self.state_attr].fillna(0).sum()

        # New API usage:
        neigh_vals = self.neighbor_values(idx, self.state_attr)
        # numpy sum, handling nans if necessary (usually 0/1 ints don't have nans in CA if initialized correctly)
        # CAUTION: neighbor_values returns numpy array.
        # If there are NaNs, we need np.nansum. But assuming valid states:
        count = neigh_vals.sum()

        if value == 1:
            return 1 if 2 <= count <= 3 else 0
        else:
            return 1 if count == 3 else 0

class GameOfLifeOriginal(CellularAutomaton):
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


def run_benchmark(model_cls, dim=(50, 50), steps=10, name="Benchmark"):
    print(f"[{name}] Setting up grid {dim}...")

    env = Environment(start_time=0, end_time=steps)
    gdf = regular_grid(dimension=dim, resolution=1, attrs={'state': 0})

    gol = model_cls(gdf=gdf, state_attr='state')
    gol.initialize()

    if not gol._neighborhood_created:
        gol.create_neighborhood(strategy=Queen, use_index=True)

    print(f"[{name}] Running execution for {steps} steps...")
    start_time = time.time()
    env.run()
    end_time = time.time()

    duration = end_time - start_time
    print(f"[{name}] Execution finished in {duration:.4f} seconds.")
    return duration

if __name__ == "__main__":
    warnings.filterwarnings("ignore")

    # Warmup
    print("Warmup...")
    run_benchmark(GameOfLifeOriginal, dim=(20, 20), steps=1, name="Warmup")

    print("\n--- Benchmarking ---")
    t_orig = run_benchmark(GameOfLifeOriginal, dim=(50, 50), steps=5, name="Original-Style")
    t_opt = run_benchmark(GameOfLifeOptimized, dim=(50, 50), steps=5, name="Optimized-Style")

    print(f"\nResults (5 steps, 50x50):")
    print(f"Original: {t_orig:.4f}s")
    print(f"Optimized: {t_opt:.4f}s")
    print(f"Speedup: {t_orig/t_opt:.2f}x")
