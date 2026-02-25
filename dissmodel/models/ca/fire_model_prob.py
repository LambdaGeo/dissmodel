# Modelo FireModelProb

import random
#from dissmodel.core import CellularAutomaton



from libpysal.weights import Queen

from dissmodel.geo.celullar_automaton import CellularAutomaton

class FireModelProb(CellularAutomaton):

    FOREST = 0
    BURNING = 1
    BURNED = 2

    prob_regrowth: float
    prob_combustion: float

    def setup(self, prob_combustion=0.001, prob_regrowth=0.1):
        self.prob_combustion = prob_combustion
        self.prob_regrowth = prob_regrowth

        self.create_neighborhood()


    def rule(self, idx):
        state = self.gdf.loc[idx, "state"]

        if state == self.FOREST:
            neighs = self.neighs(idx)

            if (neighs.state == self.BURNING).any():
                return self.BURNING
            else:
                return self.BURNING if random.random() <= self.prob_combustion else self.FOREST

        elif state == self.BURNING:
            return self.BURNED

        else:  # BURNED
            return self.FOREST if random.random() <= self.prob_regrowth else self.BURNED
