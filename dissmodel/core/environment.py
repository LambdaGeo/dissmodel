import salabim as sim

class Environment(sim.Environment):
    """
    Ambiente de simulação estendido com suporte a tempo inicial customizado
 
    Funciona como um ambiente salabim padrão, mas com start_time e end_time.
    """

    def __init__(self, start_time=0, end_time=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_time = start_time
        self.end_time = end_time

    def run(self, till=None):
        """
        Executa a simulação, usando start_time e end_time personalizados.
        Se till for informado, substitui end_time.
        """
        self.reset()  # Para reiniciar estatísticas, gráficos etc.

        if till is not None:
            self.end_time = self.start_time + till
        elif self.end_time is not None:
            till = self.end_time - self.start_time
        else:
            raise ValueError("Você deve informar 'till' ou definir 'end_time'.")

        print(f"Running from {self.start_time} to {self.end_time} (duration: {till})")
        super().run(till=till)

        
    def reset(self):
        if hasattr(self, "_plot_metadata"):
            for item in self._plot_metadata.values():
                item["data"].clear()

    def now(self):
        """
        Retorna o tempo atual da simulação ajustado pelo tempo inicial.
        """
        return super().now() + self.start_time

