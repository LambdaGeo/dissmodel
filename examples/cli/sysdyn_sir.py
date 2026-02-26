



from dissmodel.core import Environment

from dissmodel.visualization import Chart


import sys
from pathlib import Path



# Permite importar módulos do diretório pai
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from dissmodel.models.sysdyn import SIR


env = Environment()

SIR(susceptible=9998, infected=2, recovered=0, duration=2, contacts=6,
          probability=0.25)

Chart(show_legend=True)

env.run(30)  