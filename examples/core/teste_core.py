
from dissmodel.core import Model, Environment

class ModeloA(Model):
    def execute(self):
        print(f"[A] Tempo: {self.env.now()}")


class ModeloB(Model):
    def execute(self):
        print(f"[B] Tempo: {self.env.now()}")


class ModeloC(Model):
    def execute(self):
        print(f"[C] Tempo: {self.env.now()}")

# Cria o ambiente

env_a = Environment(name="Modelo A", 
                    start_time = 2010, end_time=2016
)

# Instancia os componentes no ambiente explicitamente
ModeloA(start_time=2012)
ModeloB(end_time = 2013)
ModeloC()

# Roda a simulação
env_a.run()



