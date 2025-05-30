
import matplotlib.pyplot as plt


from dissmodel.core import Model



class Map (Model):

    def setup(self, plot_params, pause = True):
        # Criar uma figura para a animação        
        self.fig, self.ax = plt.subplots(1, 1, figsize=(10, 6))
        self.plot_params = plot_params

        self.pause = pause
        

    def update(self, year, gdf):
        self.ax.clear()  # Limpa o gráfico antes de redesenhar
    
        self.env.gdf.plot(ax=self.ax, **self.plot_params) 
        self.ax.set_title(f'Map for {year}')  

        plt.draw()  # Desenha o gráfico na tela
        if self.pause:
            plt.pause(0.01)  # Pausa para a atualização visual

            if self.env.now() == self.env.end_time:
                plt.show() # não fecha a janela
        


    def execute (self):
        year = self.env.now() 
        self.update(year, self.env.gdf) 


