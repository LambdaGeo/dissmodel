import salabim as sim
from pysal.lib import weights

from libpysal.weights import KNN

class Model (sim.Component):

    strategies = {
        "Queen" : weights.contiguity.Queen,
        "Rook" : weights.contiguity.Rook
    }

    def __init__(self, hold = 1, name="", create_neighbohood = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.create_neighbohood = create_neighbohood
        self._hold = hold
        if self.create_neighbohood:
            #self.w_ = Model.strategies[self.create_neighbohood].from_dataframe(self.env.gdf, use_index=True)                   
            self.w_ = KNN.from_dataframe(self.env.gdf, k=8)

    def neighs(self, idx):
        """
        Retorna os índices dos vizinhos da célula fornecida.
        """
        if self.create_neighbohood:
            ns = self.w_.neighbors[idx]
            #return ns
            return self.env.gdf.loc[ns]
        else:
            return {}
    
    def update_neighbohood (self, strategy):
        self.w_ = Model.strategies[strategy].from_dataframe(self.env.gdf, use_index=True)                            
        
    def process(self):
            while True: 
                self.execute() 
                self.hold(self._hold)
    
    

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

