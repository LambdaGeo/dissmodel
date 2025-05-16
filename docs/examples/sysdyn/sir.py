



from dissmodel.core import Environment

from dissmodel.visualization import Chart


from dissmodel.models.sysdyn import SIR


# Preparando o ambiente de simulação e o gráfico
#print (10)
env = Environment()

SIR(susceptible=9998, infected=2, recovered=0, duration=2, contacts=6,
          probability=0.25, final_time=30)

Chart()

env.run(30)  