# Core

The `dissmodel.core` module provides the simulation clock and execution lifecycle,
built on top of [Salabim](https://www.salabim.org/)'s discrete event engine.

All models and visualization components must be instantiated **after** the
`Environment` — they register themselves automatically on creation.

```
Environment  →  Model  →  Visualization  →  env.run()
     ↑             ↑            ↑                ↑
  first         second        third           fourth
```

## Usage

```python
from dissmodel.core import Environment, Model

env = Environment(start_time=1, end_time=10)

class MyModel(Model):
    def setup(self):
        pass

    def execute(self):
        print(f"step {self.env.now()}")

MyModel()
env.run()
```

## Object-Oriented Modeling

Object-oriented modeling is a core feature of DisSModel, inherited directly from
Python's class system. Just as TerraME defines agents as objects with encapsulated
attributes and behaviours, DisSModel uses class inheritance to build structured,
reusable, and modular models.

Every model is a subclass of `Model`, which guarantees automatic registration with
the active `Environment`. This means the simulation clock, the execution lifecycle,
and any visualization components are wired together without any boilerplate.

```python
from dissmodel.core import Model, Environment

class SIR(Model):

    def setup(self, susceptible=9998, infected=2, recovered=0,
              duration=2, contacts=6, probability=0.25):
        self.susceptible  = susceptible
        self.infected     = infected
        self.recovered    = recovered
        self.duration     = duration
        self.contacts     = contacts
        self.probability  = probability

    def execute(self):
        total       = self.susceptible + self.infected + self.recovered
        alpha       = self.contacts * self.probability
        new_inf     = self.infected * alpha * (self.susceptible / total)
        new_rec     = self.infected / self.duration
        self.susceptible -= new_inf
        self.infected    += new_inf - new_rec
        self.recovered   += new_rec
```

Instantiation is clean and parametric:

```python
env = Environment(end_time=30)
SIR(susceptible=9998, infected=2, recovered=0,
    duration=2, contacts=6, probability=0.25)
env.run()
```

!!! tip "Why subclass Model?"
    - **Automatic clock integration** — `self.env.now()` is always available inside `execute()`.
    - **Encapsulation** — each model owns its state; multiple instances can run in the same environment independently.
    - **Extensibility** — override `setup()` to add parameters, `execute()` to define the transition rule. Nothing else is required.
    - **Composability** — models can read each other's state, enabling coupled CA + SysDyn simulations within a single `env.run()`.



Each model can define its own `start_time` and `end_time`, independent of the
environment interval. This allows different parts of a simulation to be active
at different periods within the same run.

```python
from dissmodel.core import Model, Environment

class ModelA(Model):
    def execute(self):
        print(f"[A] t={self.env.now()}")

class ModelB(Model):
    def execute(self):
        print(f"[B] t={self.env.now()}")

class ModelC(Model):
    def execute(self):
        print(f"[C] t={self.env.now()}")

env = Environment(start_time=2010, end_time=2016)

ModelA(start_time=2012)        # active from 2012 to end
ModelB(end_time=2013)          # active from start to 2013
ModelC()                       # active throughout

env.run()
```

Expected output:

```
Running from 2010 to 2016 (duration: 6)
[B] t=2010.0
[C] t=2010.0
[B] t=2011.0
[C] t=2011.0
[A] t=2012.0
[B] t=2012.0
[C] t=2012.0
[A] t=2013.0
[C] t=2013.0
[A] t=2014.0
[C] t=2014.0
[A] t=2015.0
[C] t=2015.0
[A] t=2016.0
[C] t=2016.0
```

!!! note
    Models with no `start_time` / `end_time` inherit the environment's interval.
    Models are synchronised — all active models execute at each time step before
    the clock advances.

---

## API Reference

::: dissmodel.core.Environment

::: dissmodel.core.Model