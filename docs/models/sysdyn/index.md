# System Dynamics

**System Dynamics (SysDyn)** is a modelling paradigm that represents a system as a set of
**stocks** (quantities that accumulate over time) and **flows** (rates that change those quantities).
The behaviour of the system emerges from the feedback loops between stocks and flows.

## How SysDyn works in DisSModel

DisSModel implements system dynamics models as `Model` subclasses that run inside the same
`salabim` environment as spatial models. This means a SysDyn model and a Cellular Automaton
can share the same simulation clock and exchange state at every step.

**Stocks** are stored as instance attributes updated in `execute()`.

**Flows** are computed each step from the current stock values and any parameters.

**Feedback loops** are expressed naturally as Python arithmetic — no special graph editor needed.

```python
from dissmodel.core import Environment
from examples.models.sysdyn import SIR
from dissmodel.visualization import Chart

env = Environment()
SIR(susceptible=9998, infected=2, recovered=0,
    duration=2, contacts=6, probability=0.25)
Chart(show_legend=True)
env.run(30)
```

## Implementing your own SysDyn model

Subclass `Model` and update stocks in `execute()`:

```python
from dissmodel.core import Model, Environment
from dissmodel.visualization import Chart, track_plot


@track_plot("population", "red")
class Logistic(Model):
    def setup(self, population, capacity, rate):
        self.population = population
        self.capacity = capacity
        self.r = rate

    def execute(self):
        growth = self.r * self.population * (1 - self.population / self.capacity)
        self.population += growth


```

Then run it:

```python
env = Environment(end_time=50)
Logistic(population=10, capacity=1000, rate=0.3)
Chart(show_legend=True, show_grid=True, title="Logistic Model")

env.run()
```

## Available models

| Model | Description |
|-------|-------------|
| [SIR](sir.md) | Susceptible–Infected–Recovered epidemiological model |
| [Predator Prey](predator_prey.md) | Lotka–Volterra ecological dynamics |
| [Population Growth](population_growth.md) | Exponential growth with variable rate |
| [Lorenz](lorenz.md) | Deterministic chaos — Lorenz attractor |
| [Coffee](coffee.md) | Newton's Law of Cooling |