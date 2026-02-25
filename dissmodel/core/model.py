import salabim as sim

import math

class Model(sim.Component):
    def __init__(self, step=1, start_time=0, end_time=math.inf, name="", *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.name = name
        self._step = step
        self.start_time = start_time
        self.end_time = end_time

    def process(self):
        # Espera até o tempo de início, se necessário
        if self.env.now() < self.start_time:
            self.hold(self.start_time - self.env.now())

        # Executa até o tempo de término
        while self.env.now() < self.end_time:
            self.execute()
            self.hold(self._step)


    def __setattr__(self, name, value):
        
        cls = self.__class__

        
        # Verifica se o atributo faz parte dos que devem ser plotados
        if hasattr(cls, "_plot_info") and name.lower() in cls._plot_info:
            plot_info = cls._plot_info[name.lower()]
            plot_info["data"].append(value)


            # Garante que _plot_metadata existe
            if not hasattr(self.env, "_plot_metadata"):
                self.env._plot_metadata = {}

            # Garante que a label está registrada no _plot_metadata
            if plot_info["label"] not in self.env._plot_metadata:
                self.env._plot_metadata[plot_info["label"]] = plot_info

        # Atribui normalmente
        super().__setattr__(name, value)

