"""
Core Behavior — start_time and end_time per model
==================================================
Demonstrates that each model can have its own active window within
the simulation, independently of the environment's time range.

- ModelA starts at 2012 (not at the environment's start_time of 2010)
- ModelB stops at 2013 (not at the environment's end_time of 2016)
- ModelC runs for the full duration of the environment

Usage
-----
    python examples/cli/core_behavior.py
"""
from __future__ import annotations

from dissmodel.core import Environment, Model


class ModelA(Model):
    """Active from start_time=2012 to environment end_time."""
    def execute(self) -> None:
        print(f"[A] time: {self.env.now()}")


class ModelB(Model):
    """Active from environment start_time to end_time=2013."""
    def execute(self) -> None:
        print(f"[B] time: {self.env.now()}")


class ModelC(Model):
    """Active for the full environment duration."""
    def execute(self) -> None:
        print(f"[C] time: {self.env.now()}")


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
env = Environment(start_time=2010, end_time=2016)

ModelA(start_time=2012)   # starts 2 years after the environment
ModelB(end_time=2013)     # stops 3 years before the environment ends
ModelC()                  # runs for the full duration

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
env.run()

# Expected output:
# [B] time: 2010
# [C] time: 2010
# [B] time: 2011
# [C] time: 2011
# [B] time: 2012
# [C] time: 2012
# [A] time: 2012  ← ModelA joins here
# [B] time: 2013
# [C] time: 2013
# [A] time: 2013
# [C] time: 2014  ← ModelB stops here
# [A] time: 2014
# [C] time: 2015
# [A] time: 2015
# [C] time: 2016
# [A] time: 2016
